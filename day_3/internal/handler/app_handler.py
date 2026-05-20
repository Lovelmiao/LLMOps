import os
import uuid
import tiktoken
from datetime import datetime
from typing import Any, TypedDict, List

from flask import request
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.documents import Document
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_pinecone import PineconeVectorStore
from langgraph.graph import StateGraph, MessagesState
from openai import OpenAI
from pinecone import Pinecone
from pydantic import Field, BaseModel

from internal.handler.auth_handler import get_login_user_id
from internal.model import ChatMessage, ChatSession, ChatSummary
from internal.exception import FailException
from internal.service import AppService, MessageService
from injector import inject
from dataclasses import dataclass
from pkg.response import success_message, success_json
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate,MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate, AIMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from internal.extension.database_extension import db
import dotenv

dotenv.load_dotenv()
@inject
@dataclass
class AppHandler:
    app_service: AppService
    message_service: MessageService

    def create_app(self):
        app = self.app_service.create_app()
        return success_message(f"创建成功{app.id}")

    def get_app(self, id: uuid.UUID):
        app = self.app_service.get_app(id)
        return success_message(f"查询成功{app.name}")

    def update_app(self, id: uuid.UUID):
        app = self.app_service.update_app(id)
        return success_message(f"更新成功{app.name}")

    def delete_app(self, id: uuid.UUID):
        app = self.app_service.delete_app(id)
        return success_message(f"删除成功{app.id}")

    def _count_tokens(self, text: str) -> int:
        """使用tiktoken计算文本的token数量"""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            # 降级方案：按字符估算
            return len(text) // 4

    def _compress_context_if_needed(self, session_id: uuid.UUID, model_max_tokens: int = 8000):
        """检查并压缩上下文"""
        return self.message_service.check_and_compress_context(session_id, model_max_tokens)

    def completion(self, app_id: uuid.UUID = None, session_id: uuid.UUID = None):
        session_id = session_id or app_id
        payload = request.get_json(silent=True) or {}
        question = (payload.get("user_input") or "").strip()
        settings = payload.get("settings") or {}
        model_name = settings.get("model") or "bailu-2.7"
        temperature = float(settings.get("temperature", 0))
        retrieval_top_k = int(settings.get("retrieval_top_k", 3))
        namespace = settings.get("namespace") or "ReID"
        enable_web_search = bool(settings.get("enable_web_search", True))
        model_max_tokens = int(settings.get("max_tokens", 8000))
        if not question:
            return {"code": "validateError", "message": "用户输入不能为空", "data": {}}, 200
        if len(question) > 500:
            return {"code": "validateError", "message": "用户输入长度不能超过 500", "data": {}}, 200

        user_id = get_login_user_id()
        if user_id:
            chat_session = self.message_service.get_user_session(session_id, user_id)
            if not chat_session:
                return {"code": "fail", "message": "会话不存在", "data": {}}, 200

        class GraphState(MessagesState):
            """图状态对象"""
            question: str
            generation: str
            web_search: str
            documents: list[Document]
            session_id: str


        class GoogleSerperArgsSchema(BaseModel):
            query: str = Field(description="需要查询的搜索语句，例如：python官网")

        google_serper = GoogleSerperRun(
            name="google_serper",
            description="使用Google Serper API进行搜索",
            args_schema=GoogleSerperArgsSchema,
            api_wrapper=GoogleSerperAPIWrapper()
        )

        model = ChatOpenAI(
            model=model_name,
            base_url=os.getenv("BASE_URL")
        )

        embeddings = NVIDIAEmbeddings(model="nvidia/nv-embed-v1")
        PC = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = PC.Index(name="llmops")

        vector_store = PineconeVectorStore(embedding=embeddings, index=index)

        retriever = vector_store.as_retriever(search_kwargs={"k": retrieval_top_k, "namespace": namespace})

        grade_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            你是文档相关性评分器。
            只输出一个字符：
            1 = 文档相关
            0 = 文档不相关

            禁止输出任何解释。"""),
            ("human",
             "文档:\n{documents}\n\n问题:\n{question}")
        ])

        retriever_grade_chain = (
                grade_prompt
                | model.bind(temperature=0)
                | StrOutputParser()
        )

        # RAG
        template = """
            你是一个AI助手，使用一下检索到的上下文来回答问题。如果不知道就说不知道，不可以胡编乱造。
            问题:{question}
            聊天历史:{history}
            上下文:{context}
            
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", template)
        ])

        rag_chain = prompt | model.bind(temperature=temperature) | StrOutputParser()

        def retrieve(state: GraphState) -> Any:
            """检索节点"""
            print("---开始检索---")
            question = state["question"]
            documents = retriever.invoke(question)
            return {**state, "documents": documents}

        def generate(state: GraphState) -> Any:
            """生成节点"""
            print("---开始生成---")
            question = state["question"]
            documents = state["documents"]
            messages = state["messages"]
            history = messages[:-1]
            generation = rag_chain.invoke(
                {"question": question, "context": "\n".join([doc.page_content for doc in documents]), "history": history})
            return {"generation": generation, "messages": [AIMessage(content=generation)]}

        def grade(state: GraphState) -> Any:
            """评分节点"""
            print("---开始评分---")
            question = state["question"]
            documents = state["documents"]

            web_search = "no"
            filtered_docs = []
            for doc in documents:
                score = retriever_grade_chain.invoke({"question": question, "documents": doc.page_content}).strip()

                if score == "1":
                    print("---文档有关联---")
                    filtered_docs.append(doc)
                else:
                    web_search = "yes"
                    print("---文档无关联---")
            return {**state, "web_search": web_search, "documents": filtered_docs}

        def web_search(state: GraphState) -> Any:
            """网络搜索节点"""
            print("---开始网络搜索---")
            question = state["question"]
            documents = state["documents"]

            web_search_results = google_serper.invoke(question)
            documents.append(Document(page_content=web_search_results))
            return {**state, "documents": documents}

        def decide_to_generate(state: GraphState) -> str:
            """route选择"""
            print("---route选择---")
            web_search = state["web_search"]
            if web_search == "yes" and enable_web_search:
                print("---选择网络搜索---")
                return "web_search"
            else:
                print("---选择生成---")
                return "generate"

        def load_history(state: GraphState) -> Any:
            messages = []
            session_id = state["session_id"]
            question = state["question"]

            print("---加载历史消息---")

            # 先检查是否需要压缩上下文
            self._compress_context_if_needed(session_id, model_max_tokens)

            # 获取总结
            summary_obj = (
                db.session.query(ChatSummary)
                .filter(ChatSummary.session_id == session_id)
                .first()
            )

            # 如果有总结，添加到消息开头
            if summary_obj and summary_obj.summary:
                messages.append(HumanMessage(content=f"以下是之前对话的总结：\n{summary_obj.summary}"))
                messages.append(AIMessage(content="好的，我已了解之前的对话内容。"))

            # 获取最近的消息
            rows = (
                db.session.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.asc())
                .all()
            )

            for row in rows:
                if row.role == "user":
                    messages.append(HumanMessage(content=row.content))
                else:
                    messages.append(AIMessage(content=row.content))
            messages.append(HumanMessage(content=question))
            print(messages)
            return {**state, "messages": messages}

        def save_message(state: GraphState) -> Any:

            """将每一轮的对话进行保存"""
            # 将state["messages"]中最新的两条消息保存到chat_message表中
            session_id = state["session_id"]
            messages = state["messages"]
            question = state["question"]

            print(messages)
            latest_two_messages = messages[-2:]
            for msg in latest_two_messages:
                role = "assistant"
                if isinstance(msg, HumanMessage):
                    role = "user"
                # 使用tiktoken计算token数量
                token_count = self._count_tokens(msg.content)
                new_message = ChatMessage(
                    session_id=session_id,
                    role=role,
                    content=msg.content,
                    token_count=token_count
                )
                db.session.add(new_message)
            chat_session = db.session.query(ChatSession).get(session_id)
            if chat_session:
                chat_session.updated_at = datetime.now()
                if not chat_session.title or chat_session.title == "新的论文研究会话":
                    chat_session.title = question[:30]
            db.session.commit()

            # 保存消息后再次检查是否需要压缩
            self._compress_context_if_needed(session_id, model_max_tokens)

            return state

        workflow = StateGraph(GraphState)

        workflow.add_node("load_history", load_history)
        workflow.add_node("retrieve", retrieve)
        workflow.add_node("grade", grade)
        workflow.add_node("web_search", web_search)
        workflow.add_node("generate", generate)
        workflow.add_node("save_message", save_message)

        workflow.set_entry_point("load_history")
        workflow.add_edge("load_history", "retrieve")
        workflow.add_edge("retrieve", "grade")
        workflow.add_conditional_edges("grade", decide_to_generate)
        workflow.add_edge("web_search", "generate")
        workflow.add_edge("generate", "save_message")
        workflow.set_finish_point("save_message")

        app = workflow.compile()

        response = app.invoke({"question": question, "session_id": session_id})
        success_res = success_json(data={
            "content": response["generation"],
            "message": {
                "role": "assistant",
                "content": response["generation"],
            }
        })
        return success_res

    def ping(self):
        raise FailException("数据未找到")
