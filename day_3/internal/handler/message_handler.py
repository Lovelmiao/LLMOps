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

    def update_summary(self, id: uuid.UUID):
        """使用LLM自动总结会话内容"""
        message = self.message_service.update_summary_with_llm(session_id=id)
        if message:
            return success_message(f"总结成功: {message.summary}")
        return success_message("没有可总结的内容")

    def get_summary(self, id: uuid.UUID):
        message = self.message_service.get_summary(session_id=id)
        if message:
            return success_message(f"查询成功: {message.summary}")
        return success_message("暂无总结")

    def add_message(self, id: uuid.UUID, role: str, content: str, token_count: int = 0):
        """添加消息并自动检查是否需要压缩上下文"""
        # 添加消息（token_count会自动计算）
        message = self.message_service.add_message(
            session_id=id, role=role, content=content, token_count=token_count
        )
        
        # 自动检查并压缩上下文
        compress_result = self.message_service.check_and_compress_context(session_id=id)
        
        return success_message({
            "message": message.content,
            "compressed": compress_result.get("compressed", False)
        })

    def get_messages(self, id: uuid.UUID):
        message = self.message_service.get_messages(session_id=id)
        contents = [m.content for m in message]
        return success_message(contents)

    def get_context(self, id: uuid.UUID):
        """获取用于LLM的完整上下文（包括总结和最近消息）"""
        context = self.message_service.get_context_for_llm(session_id=id)
        return success_message(context)

    def compress_context(self, id: uuid.UUID, model_max_tokens: int = 8000):
        """手动触发上下文压缩"""
        result = self.message_service.check_and_compress_context(
            session_id=id, 
            model_max_tokens=model_max_tokens
        )
        return success_message(result)
