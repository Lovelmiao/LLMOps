import os
import uuid
from dataclasses import dataclass
from typing import List

import dotenv
from injector import inject
from internal.service import MessageService
from internal.model.app import App, User, ChatSummary, ChatSession, ChatMessage
from pkg.response import success_message

dotenv.load_dotenv()

@inject
@dataclass
class MessageHander:
    message_service: MessageService

    def create_session(self, id: uuid.UUID):
        message = self.message_service.create_session(id, title="test")

        return success_message(f"创建成功{message.id}")
    def get_session(self, id: uuid.UUID):
        message = self.message_service.get_session(id=id)
        return success_message(f"查询成功{message.user_id}")

    def update_summary(self,id: uuid.UUID):
        summary = "数据量一大可能会变慢"
        token_count = 10
        message = self.message_service.update_summary(session_id=id,summary=summary,token_count=token_count)
        return success_message(f"查询成功{message.summary}")

    def get_summary(self,id: uuid.UUID):
        message = self.message_service.get_summary(session_id=id)
        return success_message(f"查询成功{message.summary}")

    def add_message(self,id: uuid.UUID, role:str, content:str, token_count:int):
        message = self.message_service.add_message(session_id=id, role=role, content=content, token_count=token_count)
        return success_message(f"查询成功{message.content}")

    def get_messages(self, id: uuid.UUID):
        message = self.message_service.get_messages(session_id=id)
        contents = [m.content for m in message]
        return success_message(contents)