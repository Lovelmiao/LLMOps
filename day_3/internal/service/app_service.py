import uuid

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

    def add_message(
            self,
            session_id: uuid.UUID,
            role: str,
            content: str,
            token_count: int
    ) -> ChatMessage:

        token_count = len(content.split())
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
