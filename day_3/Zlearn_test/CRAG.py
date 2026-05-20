import dataclasses
import os
from typing import TypedDict, Any

import dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph,MessagesState
from langgraph.prebuilt import ToolNode
from pinecone import Pinecone
from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper

from app.app import injector
from internal.handler import MessageHander

dotenv.load_dotenv()

# class GradeDocument(BaseModel):
#     """评分文档对象"""
#     binary_score: str = Field(description="二分类评分结果，值为'0'或'1'")


class GraphState(MessagesState):
    """图状态对象"""
    generation: str
    web_search: str
    documents: list[Document]
    session_id: str

class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(description="需要查询的搜索语句，例如：python官网")

google_serper = GoogleSerperRun(
    name = "google_serper",
    description = "使用Google Serper API进行搜索",
    args_schema = GoogleSerperArgsSchema,
    api_wrapper = GoogleSerperAPIWrapper()
)

model = ChatOpenAI(
    model="bailu-2.7",
    base_url=os.getenv("BASE_URL")
)

embeddings = NVIDIAEmbeddings(model="nvidia/nv-embed-v1")
PC = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = PC.Index(name="llmops")

vector_store = PineconeVectorStore(embedding=embeddings, index=index)

retriever = vector_store.as_retriever(search_kwargs={"k": 3, "namespace": "ReID"})

grade_prompt = ChatPromptTemplate.from_messages([
    ("system","""
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

#RAG
template = """
    你是一个AI助手，使用一下检索到的上下文来回答问题。如果不知道就说不知道，不可以胡编乱造。
    问题:{question}
    上下文:{context}
"""
prompt = ChatPromptTemplate.from_messages([
    ("system",template)
])

rag_chain = prompt | model.bind(temperature = 0) | StrOutputParser()

rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个AI助手，负责将用户的问题进行改写，使其更适合进行检索。请根据以下示例进行改写：\n\n示例1:\n用户问题: '这篇论文的主要贡献是什么？'\n改写后: '请总结一下这篇论文的主要贡献。'\n\n示例2:\n用户问题: '这篇论文使用了哪些方法？'\n改写后: '请列举一下这篇论文中使用的方法。'\n\n现在请改写以下用户问题:\n"),
    ("human", "用户提问:{question}")
])
question_rewrite = rewrite_prompt | model.bind(temperature = 0) | StrOutputParser()

def retrieve(state: GraphState) -> Any:
    """检索节点"""
    print("---开始检索---")
    question = state["messages"][-1].content
    documents = retriever.invoke(question)
    return {**state, "documents": documents}

def generate(state: GraphState) -> Any:
    """生成节点"""
    print("---开始生成---")
    question = state["messages"][-1].content
    documents = state["documents"]
    generation = rag_chain.invoke({"question": question, "context": "\n".join([doc.page_content for doc in documents])})
    return {"generation": generation, "messages": [AIMessage(content=generation)]}

def grade(state: GraphState) -> Any:
    """评分节点"""
    print("---开始评分---")
    question = state["messages"][-1].content
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

def web_search(state:GraphState) -> Any:
    """网络搜索节点"""
    print("---开始网络搜索---")
    question = state["messages"][-1].content
    documents = state["documents"]

    web_search_results = google_serper.invoke(question)
    documents.append(Document(page_content=web_search_results))
    return {**state, "documents": documents}

def decide_to_generate(state:GraphState) -> str:
    """route选择"""
    print("---route选择---")
    web_search = state["web_search"]
    if web_search == "yes":
        print("---选择网络搜索---")
        return "web_search"
    else:
        print("---选择生成---")
        return "generate"


def load_history(state: GraphState) -> Any:
    message_handle = injector.get(MessageHander)
    """加载历史消息"""
    messages = []
    session_id = state["session_id"]

    print("---加载历史消息---")

    rows = message_handle.get_messages(id=session_id)
    for row in rows:
        if row.role == "user":
            messages.append(HumanMessage(content=row.content))
        else:
            messages.append(AIMessage(content=row.content))

    return {**state, "messages": messages}

def save_message(state: GraphState) -> Any:
    message_handle = injector.get(MessageHander)
    """将每一轮的对话进行保存"""
    #将state["messages"]中最新的两条消息保存到chat_message表中，包含session_id、role、content等字段，
    session_id = state["session_id"]
    messages = state["messages"]

    latest_two_messages = messages[-2:]
    for msg in latest_two_messages:
        role = "assistant"
        if isinstance(msg, HumanMessage):
            role = "user"
        token_count = model.get_num_tokens_from_messages([msg])
        message_handle.add_message(id=session_id, role=role, content=msg.content, token_count=token_count)

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

response = app.invoke({
    "user_input": "这篇论文的主要贡献是什么？",
    "session_id": "test-session-id"
})

print(response["generation"])


# def completion(self, app_id: uuid.UUID):
#     user_input = CompletionForm()
#     if not user_input.validate():
#         return {"error": user_input.errors}, 400
#
#     class GraphState(TypedDict):
#         """图状态对象"""
#         question: str
#         generation: str
#         web_search: str
#         documents: list[Document]
#         session_id: str
#
#     class GoogleSerperArgsSchema(BaseModel):
#         query: str = Field(description="需要查询的搜索语句，例如：python官网")
#
#     google_serper = GoogleSerperRun(
#         name="google_serper",
#         description="使用Google Serper API进行搜索",
#         args_schema=GoogleSerperArgsSchema,
#         api_wrapper=GoogleSerperAPIWrapper()
#     )
#
#     model = ChatOpenAI(
#         model="bailu-2.7",
#         base_url=os.getenv("BASE_URL")
#     )
#
#     embeddings = NVIDIAEmbeddings(model="nvidia/nv-embed-v1")
#     PC = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
#     index = PC.Index(name="llmops")
#
#     vector_store = PineconeVectorStore(embedding=embeddings, index=index)
#
#     retriever = vector_store.as_retriever(search_kwargs={"k": 3, "namespace": "ReID"})
#
#     grade_prompt = ChatPromptTemplate.from_messages([
#         ("system", """
#         你是文档相关性评分器。
#         只输出一个字符：
#         1 = 文档相关
#         0 = 文档不相关
#
#         禁止输出任何解释。"""),
#         ("human",
#          "文档:\n{documents}\n\n问题:\n{question}")
#     ])
#
#     retriever_grade_chain = (
#             grade_prompt
#             | model.bind(temperature=0)
#             | StrOutputParser()
#     )
#
#     # RAG
#     template = """
#         你是一个AI助手，使用一下检索到的上下文来回答问题。如果不知道就说不知道，不可以胡编乱造。
#         问题:{question}
#         上下文:{context}
#     """
#     prompt = ChatPromptTemplate.from_messages([
#         ("system", template)
#     ])
#
#     rag_chain = prompt | model.bind(temperature=0) | StrOutputParser()
#
#     rewrite_prompt = ChatPromptTemplate.from_messages([
#         ("system",
#          "你是一个AI助手，负责将用户的问题进行改写，使其更适合进行检索。请根据以下示例进行改写：\n\n示例1:\n用户问题: '这篇论文的主要贡献是什么？'\n改写后: '请总结一下这篇论文的主要贡献。'\n\n示例2:\n用户问题: '这篇论文使用了哪些方法？'\n改写后: '请列举一下这篇论文中使用的方法。'\n\n现在请改写以下用户问题:\n"),
#         ("human", "用户提问:{question}")
#     ])
#     question_rewrite = rewrite_prompt | model.bind(temperature=0) | StrOutputParser()
#
#     def retrieve(state: GraphState) -> Any:
#         """检索节点"""
#         print("---开始检索---")
#         question = state["question"]
#         documents = retriever.invoke(question)
#         return {**state, "documents": documents}
#
#     def generate(state: GraphState) -> Any:
#         """生成节点"""
#         print("---开始生成---")
#         question = state["question"]
#         documents = state["documents"]
#         generation = rag_chain.invoke(
#             {"question": question, "context": "\n".join([doc.page_content for doc in documents])})
#         return {**state, "generation": generation}
#
#     def grade(state: GraphState) -> Any:
#         """评分节点"""
#         print("---开始评分---")
#         question = state["question"]
#         documents = state["documents"]
#
#         web_search = "no"
#         filtered_docs = []
#         for doc in documents:
#             score = retriever_grade_chain.invoke({"question": question, "documents": doc.page_content}).strip()
#
#             if score == "1":
#                 print("---文档有关联---")
#                 filtered_docs.append(doc)
#             else:
#                 web_search = "yes"
#                 print("---文档无关联---")
#         return {**state, "web_search": web_search, "documents": filtered_docs}
#
#     def transform_query(state: GraphState) -> Any:
#         """改写查询节点"""
#         print("---开始改写查询---")
#         question = state["question"]
#         # rewritten_question = question_rewrite.invoke({"question": question})
#         return {**state, "question": question}
#
#     def web_search(state: GraphState) -> Any:
#         """网络搜索节点"""
#         print("---开始网络搜索---")
#         question = state["question"]
#         documents = state["documents"]
#
#         web_search_results = google_serper.invoke(question)
#         documents.append(Document(page_content=web_search_results))
#         return {**state, "documents": documents}
#
#     def decide_to_generate(state: GraphState) -> str:
#         """route选择"""
#         print("---route选择---")
#         web_search = state["web_search"]
#         if web_search == "yes":
#             print("---选择网络搜索---")
#             return "transform_query"
#         else:
#             print("---选择生成---")
#             return "generate"
#
#     workflow = StateGraph(GraphState)
#
#     workflow.add_node("retrieve", retrieve)
#     workflow.add_node("grade", grade)
#     workflow.add_node("generate", generate)
#     workflow.add_node("web_search", web_search)
#     workflow.add_node("transform_query", transform_query)
#
#     workflow.set_entry_point("retrieve")
#     workflow.add_edge("retrieve", "grade")
#     workflow.add_conditional_edges("grade", decide_to_generate)
#     workflow.add_edge("transform_query", "web_search")
#     workflow.add_edge("web_search", "generate")
#     workflow.set_finish_point("generate")
#
#     app = workflow.compile()
#
#     response = app.invoke({"question": user_input.user_input.data})
#     success_res = success_json(data={"content": response["generation"]})
#     return success_res