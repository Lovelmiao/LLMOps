import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List

from flask import request
from injector import inject
from werkzeug.utils import secure_filename

from internal.handler.auth_handler import get_login_user_id
from internal.service import MessageService
from pkg.response import success_json, validate_error_json, fail_json

import dotenv

dotenv.load_dotenv()

# Pinecone相关导入
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_core.documents import Document

DEFAULT_SESSION_TITLE = "新的论文研究会话"

DEFAULT_DOCUMENT_METADATA = {
    "title": "",
    "author": "",
    "year": "",
    "keywords": "",
    "source": "local_upload",
    "tags": [],
}

DEFAULT_SESSION_SETTINGS = {
    "model": "bailu-2.7",
    "temperature": 0,
    "top_p": 1,
    "retrieval_top_k": 3,
    "namespace": "ReID",
    "enable_web_search": True,
}


def serialize_session(chat_session):
    return {
        "id": str(chat_session.id),
        "title": chat_session.title or DEFAULT_SESSION_TITLE,
        "created_at": chat_session.created_at.isoformat(),
        "updated_at": chat_session.updated_at.isoformat(),
    }


def serialize_message(message):
    return {
        "id": str(message.id),
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


@inject
@dataclass
class SessionHandler:
    message_service: MessageService

    def _storage_root(self):
        return os.path.abspath(os.path.join(os.getcwd(), "instance", "session_assets"))

    def _session_dir(self, session_id: uuid.UUID):
        return os.path.join(self._storage_root(), str(session_id))

    def _documents_path(self, session_id: uuid.UUID):
        return os.path.join(self._session_dir(session_id), "documents.json")

    def _settings_path(self, session_id: uuid.UUID):
        return os.path.join(self._session_dir(session_id), "settings.json")

    def _read_json(self, path: str, default):
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _write_json(self, path: str, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def _public_documents(self, documents):
        private_keys = {"stored_path", "vector_ids", "namespace"}
        return [{key: value for key, value in item.items() if key not in private_keys} for item in documents]

    def _require_user(self):
        user_id = get_login_user_id()
        if not user_id:
            return None, fail_json("请先登录")
        return user_id, None

    def _require_user_session(self, session_id: uuid.UUID):
        user_id, error = self._require_user()
        if error:
            return None, error

        chat_session = self.message_service.get_user_session(session_id, user_id)
        if not chat_session:
            return None, fail_json("会话不存在")

        return chat_session, None

    def _get_vector_store(self):
        """获取Pinecone向量存储实例"""
        try:
            embeddings = NVIDIAEmbeddings(model="nvidia/nv-embed-v1")
            pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            index = pc.Index(name="llmops")
            return PineconeVectorStore(embedding=embeddings, index=index)
        except Exception as e:
            print(f"获取Pinecone连接失败: {e}")
            return None

    def _load_and_split_document(self, file_path: str) -> List[Document]:
        """加载并分割文档"""
        try:
            loader = PyMuPDFLoader(file_path)
            documents = loader.load()
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500, 
                chunk_overlap=100
            )
            chunks = text_splitter.split_documents(documents)
            return chunks
        except Exception as e:
            print(f"文档加载失败: {e}")
            return []

    def _upload_to_pinecone(self, file_path: str, namespace: str, metadata: dict = None) -> List[str]:
        """将文档上传到Pinecone，返回向量ID列表"""
        try:
            chunks = self._load_and_split_document(file_path)
            if not chunks:
                return []

            vector_store = self._get_vector_store()
            if not vector_store:
                return []

            texts = []
            metadatas = []
            for chunk in chunks:
                texts.append(chunk.page_content)
                chunk_metadata = {**(chunk.metadata or {}), **(metadata or {})}
                metadatas.append(chunk_metadata)

            ids = vector_store.add_texts(texts, metadatas=metadatas, namespace=namespace)
            print(f"成功上传 {len(ids)} 个向量到Pinecone")
            return ids
        except Exception as e:
            print(f"Pinecone上传失败: {e}")
            return []

    def _delete_from_pinecone(self, namespace: str, vector_ids: List[str]) -> bool:
        """从Pinecone删除向量"""
        try:
            vector_store = self._get_vector_store()
            if not vector_store:
                return False

            index = vector_store._index
            index.delete(ids=vector_ids, namespace=namespace)
            print(f"成功从Pinecone删除 {len(vector_ids)} 个向量")
            return True
        except Exception as e:
            print(f"Pinecone删除失败: {e}")
            return False

    def create_session(self):
        user_id, error = self._require_user()
        if error:
            return error

        payload = request.get_json(silent=True) or {}
        title = (payload.get("title") or DEFAULT_SESSION_TITLE).strip()
        chat_session = self.message_service.create_session(user_id, title)
        return success_json("创建成功", {"session": serialize_session(chat_session)})

    def list_sessions(self):
        user_id, error = self._require_user()
        if error:
            return error

        sessions = self.message_service.list_sessions(user_id)
        return success_json(data={"sessions": [serialize_session(item) for item in sessions]})

    def get_session(self, session_id: uuid.UUID):
        chat_session, error = self._require_user_session(session_id)
        if error:
            return error

        messages = self.message_service.get_messages(session_id)
        return success_json(data={
            "session": serialize_session(chat_session),
            "messages": [serialize_message(item) for item in messages],
        })

    def update_session(self, session_id: uuid.UUID):
        user_id, error = self._require_user()
        if error:
            return error

        payload = request.get_json(silent=True) or {}
        title = (payload.get("title") or "").strip()
        if not title:
            return validate_error_json("会话标题不能为空")

        chat_session = self.message_service.update_session(session_id, user_id, title)
        if not chat_session:
            return fail_json("会话不存在")

        return success_json("更新成功", {"session": serialize_session(chat_session)})

    def delete_session(self, session_id: uuid.UUID):
        user_id, error = self._require_user()
        if error:
            return error

        chat_session = self.message_service.delete_session(session_id, user_id)
        if not chat_session:
            return fail_json("会话不存在")

        return success_json("删除成功")

    def list_documents(self, session_id: uuid.UUID):
        _, error = self._require_user_session(session_id)
        if error:
            return error

        documents = self._read_json(self._documents_path(session_id), [])
        return success_json(data={"documents": self._public_documents(documents)})

    def upload_documents(self, session_id: uuid.UUID):
        _, error = self._require_user_session(session_id)
        if error:
            return error

        files = request.files.getlist("files")
        if not files:
            return validate_error_json("请选择要加载的文件")

        raw_metadata = request.form.get("metadata") or "{}"
        try:
            payload_metadata = json.loads(raw_metadata)
        except json.JSONDecodeError:
            return validate_error_json("metadata 必须是合法 JSON")

        session_dir = self._session_dir(session_id)
        upload_dir = os.path.join(session_dir, "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        documents = self._read_json(self._documents_path(session_id), [])
        
        # 获取namespace，优先使用metadata中的，否则使用默认值
        namespace = payload_metadata.get("namespace", DEFAULT_SESSION_SETTINGS["namespace"])

        for file in files:
            filename = secure_filename(file.filename or "document")
            document_id = str(uuid.uuid4())
            stored_filename = f"{document_id}_{filename}"
            stored_path = os.path.join(upload_dir, stored_filename)
            file.save(stored_path)

            metadata = {**DEFAULT_DOCUMENT_METADATA, **payload_metadata}
            if not metadata.get("title"):
                metadata["title"] = os.path.splitext(filename)[0]
            if not isinstance(metadata.get("tags"), list):
                metadata["tags"] = []

            # 上传到Pinecone
            vector_ids = []
            if filename.lower().endswith('.pdf'):
                pinecone_metadata = {
                    "document_id": document_id,
                    "filename": filename,
                    "session_id": str(session_id),
                    **metadata
                }
                vector_ids = self._upload_to_pinecone(stored_path, namespace, pinecone_metadata)
                status = "indexed" if vector_ids else "index_failed"
            else:
                status = "ready"  # 非PDF文件暂不处理向量化

            documents.append({
                "id": document_id,
                "filename": filename,
                "content_type": file.mimetype or "application/octet-stream",
                "size": os.path.getsize(stored_path),
                "status": status,
                "metadata": metadata,
                "stored_path": stored_path,
                "vector_ids": vector_ids,  # 保存向量ID用于后续删除
                "namespace": namespace,
                "created_at": datetime.now().isoformat(),
            })

        self._write_json(self._documents_path(session_id), documents)
        return success_json("上传成功", {"documents": self._public_documents(documents)})

    def delete_document(self, session_id: uuid.UUID, document_id: uuid.UUID):
        _, error = self._require_user_session(session_id)
        if error:
            return error

        documents = self._read_json(self._documents_path(session_id), [])
        target = None
        remaining = []
        for item in documents:
            if item.get("id") == str(document_id):
                target = item
            else:
                remaining.append(item)

        if not target:
            return fail_json("文件不存在")

        # 删除本地文件
        stored_path = target.get("stored_path")
        if stored_path and os.path.exists(stored_path):
            os.remove(stored_path)

        # 删除Pinecone中的向量数据
        vector_ids = target.get("vector_ids", [])
        namespace = target.get("namespace", DEFAULT_SESSION_SETTINGS["namespace"])
        if vector_ids:
            self._delete_from_pinecone(namespace, vector_ids)
            print(f"已从Pinecone删除 {len(vector_ids)} 个向量")

        self._write_json(self._documents_path(session_id), remaining)
        return success_json("删除成功", {"documents": self._public_documents(remaining)})

    def delete_message_pair(self, session_id: uuid.UUID, message_id: uuid.UUID):
        """删除用户消息及其对应的AI回复"""
        _, error = self._require_user_session(session_id)
        if error:
            return error

        try:
            # 查找目标消息
            target_message = self.message_service.get_message_by_id(message_id)
            if not target_message:
                return fail_json("消息不存在")

            if str(target_message.session_id) != str(session_id):
                return fail_json("消息不属于该会话")

            # 如果是用户消息，删除它和紧随其后的AI回复
            messages_to_delete = [target_message]

            if target_message.role == "user":
                # 查找该用户消息之后的第一条assistant消息
                next_assistant = self.message_service.get_next_assistant_message(session_id, target_message.created_at)
                if next_assistant:
                    messages_to_delete.append(next_assistant)

            # 删除消息
            for msg in messages_to_delete:
                self.message_service.delete_message(msg.id)

            return success_json("消息已删除")
        except Exception as e:
            return fail_json(f"删除失败: {str(e)}")

    def get_settings(self, session_id: uuid.UUID):
        _, error = self._require_user_session(session_id)
        if error:
            return error

        settings = {
            **DEFAULT_SESSION_SETTINGS,
            **self._read_json(self._settings_path(session_id), {}),
        }
        return success_json(data={"settings": settings})

    def update_settings(self, session_id: uuid.UUID):
        _, error = self._require_user_session(session_id)
        if error:
            return error

        payload = request.get_json(silent=True) or {}
        settings = {
            **DEFAULT_SESSION_SETTINGS,
            **payload,
        }
        settings["temperature"] = max(0, min(2, float(settings.get("temperature", 0))))
        settings["top_p"] = max(0, min(1, float(settings.get("top_p", 1))))
        settings["retrieval_top_k"] = max(1, min(20, int(settings.get("retrieval_top_k", 3))))
        settings["enable_web_search"] = bool(settings.get("enable_web_search", True))

        self._write_json(self._settings_path(session_id), settings)
        return success_json("设置已保存", {"settings": settings})
