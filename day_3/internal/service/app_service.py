import uuid
import os
import tiktoken
from openai import OpenAI
from pkg.sqlalchemy import SQLAlchemy
from injector import inject
from dataclasses import dataclass
from internal.model.app import App, User, ChatSummary, ChatSession, ChatMessage
from werkzeug.security import generate_password_hash, check_password_hash

@inject
@dataclass
class AppService:
    db: SQLAlchemy

    def create_app(self) -> App:
        with self.db.auto_commit():
            app = App(
                name = "test app",
                account_id = uuid.uuid4(),
                icon = "",
                description = "test app description"
            )
            self.db.session.add(app)
        return app

    def get_app(self, id:uuid.UUID) -> App:
        app = self.db.session.query(App).get(id)
        return app

    def update_app(self, id:uuid.UUID) -> App:
        with self.db.auto_commit():
            app = self.db.session.query(App).get(id)
            app.name = "xulaoban"
        return app

    def delete_app(self, id:uuid.UUID) -> App:
        with self.db.auto_commit():
            app = self.db.session.query(App).get(id)
            self.db.session.delete(app)
        return app

@inject
@dataclass
class MessageService:
    db: SQLAlchemy

    def _count_tokens(self, text: str) -> int:
        """使用tiktoken计算文本的token数量"""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            # 降级方案：按字符估算
            return len(text) // 4

    def _summarize_with_llm(self, messages: list, existing_summary: str = "") -> str:
        """使用LLM总结对话内容"""
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("BASE_URL")
        )
        
        # 构建对话文本
        conversation = "\n".join([f"{m.role}: {m.content}" for m in messages])
        
        prompt = f"""请总结以下对话内容，保留关键信息和要点。

{f"已有总结: {existing_summary}" if existing_summary else ""}

对话内容:
{conversation}

请提供简洁的总结（不超过500字）："""
        
        try:
            response = client.chat.completions.create(
                model="bailu-2.7",
                messages=[
                    {"role": "system", "content": "你是一个对话总结助手，请简洁地总结对话内容。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            # 降级方案：简单截取
            return f"对话摘要：{conversation[:500]}..."

    def add_message(
            self,
            session_id: uuid.UUID,
            role: str,
            content: str,
            token_count: int
    ) -> ChatMessage:

        token_count = self._count_tokens(content)
        with self.db.auto_commit():
            chatmessage = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                token_count=token_count
            )
            self.db.session.add(chatmessage)

        return chatmessage
    def get_messages(self, session_id: uuid.UUID) -> ChatMessage:
        chatmessage = self.db.session.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
        return chatmessage


    def get_summary(self, session_id: uuid.UUID) -> ChatSummary | None:
        return (
            self.db.session
            .query(ChatSummary)
            .filter(ChatSummary.session_id == session_id)
            .first()
        )
    def update_summary(
        self,
        session_id: uuid.UUID,
        summary: str,
        token_count: int
    ):
        """更新或创建会话摘要"""
        with self.db.auto_commit():
            obj = (
                self.db.session
                .query(ChatSummary)
                .filter(ChatSummary.session_id == session_id)
                .first()
            )

            if obj:
                obj.summary = summary
                obj.token_count = token_count
            else:
                obj = ChatSummary(
                    session_id=session_id,
                    summary=summary,
                    token_count=token_count
                )
                self.db.session.add(obj)

        return obj

    def update_summary_with_llm(self, session_id: uuid.UUID) -> ChatSummary | None:
        """使用LLM自动总结会话内容"""
        # 获取所有消息
        messages = self.get_messages(session_id)
        if not messages:
            return None
        
        # 获取已有总结
        existing_summary_obj = self.get_summary(session_id)
        existing_summary = existing_summary_obj.summary if existing_summary_obj else ""
        
        # 使用LLM生成总结
        summary_text = self._summarize_with_llm(messages, existing_summary)
        
        # 计算总结的token数
        token_count = self._count_tokens(summary_text)
        
        # 保存到数据库
        return self.update_summary(session_id, summary_text, token_count)

    def check_and_compress_context(self, session_id: uuid.UUID, model_max_tokens: int = 8000) -> dict:
        """
        摘要缓冲记忆功能：当上下文长度超过模型上下文限制的80%时，进行上下文压缩
        保留最近的记录（80%token），超出部分采用摘要的方式保存
        """
        threshold = int(model_max_tokens * 0.8)  # 80%的阈值
        
        # 获取所有消息
        messages = self.get_messages(session_id)
        if not messages:
            return {"compressed": False, "reason": "no_messages"}
        
        # 计算当前总token数
        total_tokens = sum(m.token_count for m in messages)
        
        # 获取已有总结的token数
        existing_summary_obj = self.get_summary(session_id)
        summary_tokens = existing_summary_obj.token_count if existing_summary_obj else 0
        
        # 计算上下文总长度（消息 + 已有总结）
        context_tokens = total_tokens + summary_tokens
        
        if context_tokens <= threshold:
            return {
                "compressed": False, 
                "reason": "within_limit",
                "total_tokens": total_tokens,
                "summary_tokens": summary_tokens,
                "context_tokens": context_tokens,
                "threshold": threshold
            }
        
        # 需要压缩：找到需要保留的最近消息
        tokens_to_keep = threshold
        keep_messages = []
        current_tokens = 0
        
        # 从最新的消息开始往前遍历，保留80%token的最近消息
        for msg in reversed(messages):
            if current_tokens + msg.token_count > tokens_to_keep:
                break
            keep_messages.insert(0, msg)
            current_tokens += msg.token_count
        
        # 需要被压缩的消息（较早的消息）
        compress_messages = messages[:len(messages) - len(keep_messages)]
        
        if not compress_messages:
            return {
                "compressed": False,
                "reason": "cannot_compress",
                "total_tokens": total_tokens,
                "threshold": threshold
            }
        
        # 将已有总结和需要压缩的消息一起总结
        all_to_summarize = []
        if existing_summary_obj and existing_summary_obj.summary:
            all_to_summarize.append(type('Message', (), {
                'role': 'system', 
                'content': f"之前的总结：{existing_summary_obj.summary}"
            })())
        all_to_summarize.extend(compress_messages)
        
        # 使用LLM总结
        new_summary = self._summarize_with_llm(all_to_summarize)
        new_token_count = self._count_tokens(new_summary)
        
        # 保存新的总结
        self.update_summary(session_id, new_summary, new_token_count)
        
        # 删除已被压缩的消息
        for msg in compress_messages:
            self.delete_message(msg.id)
        
        return {
            "compressed": True,
            "reason": "exceeded_threshold",
            "original_tokens": total_tokens,
            "compressed_messages_count": len(compress_messages),
            "kept_messages_count": len(keep_messages),
            "new_summary_tokens": new_token_count,
            "threshold": threshold
        }

    def get_context_for_llm(self, session_id: uuid.UUID) -> list:
        """
        获取用于LLM的上下文（包括总结和最近消息）
        返回格式化的消息列表
        """
        context_messages = []
        
        # 获取总结
        summary_obj = self.get_summary(session_id)
        if summary_obj and summary_obj.summary:
            context_messages.append({
                "role": "system",
                "content": f"以下是之前对话的总结：\n{summary_obj.summary}"
            })
        
        # 获取最近的消息
        messages = self.get_messages(session_id)
        for msg in messages:
            context_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return context_messages

    def create_session(self, user_id: uuid.UUID, title: str = "") -> ChatSession:
        with self.db.auto_commit():
            chatsession = ChatSession(
                user_id=user_id,
                title=title or "新的论文研究会话"
            )
            self.db.session.add(chatsession)
        return chatsession

    def get_session(self, id: uuid.UUID) -> ChatSession:
        chatsession = self.db.session.query(ChatSession).get(id)
        return chatsession

    def list_sessions(self, user_id: uuid.UUID) -> list[ChatSession]:
        return (
            self.db.session.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
            .all()
        )

    def update_session(self, session_id: uuid.UUID, user_id: uuid.UUID, title: str) -> ChatSession | None:
        with self.db.auto_commit():
            chatsession = (
                self.db.session.query(ChatSession)
                .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
                .first()
            )
            if chatsession:
                chatsession.title = title
        return chatsession

    def delete_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> ChatSession | None:
        with self.db.auto_commit():
            chatsession = (
                self.db.session.query(ChatSession)
                .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
                .first()
            )
            if chatsession:
                self.db.session.delete(chatsession)
        return chatsession

    def get_message_by_id(self, message_id: uuid.UUID) -> ChatMessage | None:
        return self.db.session.query(ChatMessage).get(message_id)

    def get_next_assistant_message(self, session_id: uuid.UUID, after_time) -> ChatMessage | None:
        return (
            self.db.session.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session_id,
                ChatMessage.role == "assistant",
                ChatMessage.created_at > after_time,
            )
            .order_by(ChatMessage.created_at.asc())
            .first()
        )

    def delete_message(self, message_id: uuid.UUID):
        message = self.db.session.query(ChatMessage).get(message_id)
        if message:
            with self.db.auto_commit():
                self.db.session.delete(message)

    def get_user_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> ChatSession | None:
        return (
            self.db.session.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .first()
        )


@inject
@dataclass
class AuthService:
    db: SQLAlchemy

    def create_user(self, username: str, password: str) -> User:
        with self.db.auto_commit():
            user = User(
                username=username,
                password_hash=generate_password_hash(password)
            )
            self.db.session.add(user)
        return user

    def get_user_by_username(self, username: str) -> User | None:
        return self.db.session.query(User).filter(User.username == username).first()

    def get_user(self, user_id: uuid.UUID) -> User | None:
        return self.db.session.query(User).get(user_id)

    def verify_password(self, user: User, password: str) -> bool:
        return check_password_hash(user.password_hash, password)
