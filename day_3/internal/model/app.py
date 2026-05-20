from datetime import datetime

from internal.extension.database_extension import db
import uuid

from sqlalchemy import (
    Column,
    String,
    UUID,
    Text,
    DateTime,
    PrimaryKeyConstraint,
    Index,
    func
)


class App(db.Model):
    __tablename__ = 'app'
    __table_args__ = (
        PrimaryKeyConstraint('id', name = "pk_app_id"),
        Index("idx_account_id", "account_id")
    )


    id = Column(UUID, default=uuid.uuid4, nullable=False)
    account_id = Column(UUID, nullable=False)
    name = Column(String(255), default="", nullable=False)
    icon = Column(String(255), default="", nullable=True)
    description = Column(Text, default="", nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=func.now(), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_users_id"),
        Index("idx_users_username", "username"),
    )

    id = db.Column(db.UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False )
    updated_at = Column(DateTime, default=datetime.now, onupdate=func.now(), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

class ChatSession(db.Model):
    __tablename__ = "chat_sessions"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_chat_sessions_id"),
        Index("idx_chat_sessions_user_id", "user_id"),
    )

    id = db.Column(db.UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(255))
    updated_at = Column(DateTime, default=datetime.now, onupdate=func.now(), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_chat_messages_id"),

        Index(
            "idx_chat_messages_session_id",
            "session_id"
        ),

        Index(
            "idx_chat_messages_created_at",
            "created_at"
        ),

        Index(
            "idx_chat_messages_session_created",
            "session_id",
            "created_at"
        ),
    )

    id = db.Column(db.UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    session_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    token_count = db.Column(db.Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.now, onupdate=func.now(), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

class ChatSummary(db.Model):
    __tablename__ = "chat_summaries"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_chat_summaries_id"),
        Index(
            "idx_chat_summaries_session_id",
            "session_id"
        ),
    )

    id = db.Column(db.UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    session_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    summary = db.Column(db.Text, nullable=False, default="")
    token_count = db.Column(db.Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.now, onupdate=func.now(), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

