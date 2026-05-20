from flask import Flask, Blueprint
from internal.handler import AppHandler, MessageHander, AuthHandler, SessionHandler
from injector import inject
from dataclasses import dataclass

@inject
@dataclass
class Router:
   app_handler: AppHandler
   message_handle: MessageHander
   auth_handler: AuthHandler
   session_handler: SessionHandler

   def register_router(self, app:Flask):
      #1. 创建一个蓝图
      bp = Blueprint('llmops', __name__, url_prefix="")

      #2. 将url与对应的控制器方法做绑定

      bp.add_url_rule('/app', view_func=self.app_handler.ping)
      bp.add_url_rule('/apps/<uuid:app_id>/debug', view_func=self.app_handler.completion, methods=['POST'])
      bp.add_url_rule('/app/create', view_func=self.app_handler.create_app, methods=['POST'])
      bp.add_url_rule('/app/<uuid:id>', view_func=self.app_handler.get_app, methods = ['GET'])
      bp.add_url_rule('/app/<uuid:id>', view_func=self.app_handler.update_app, methods = ['POST'])
      bp.add_url_rule('/app/<uuid:id>/delete', view_func=self.app_handler.delete_app, methods = ['POST'])
      bp.add_url_rule('/auth/register', endpoint='auth_register', view_func=self.auth_handler.register, methods=['POST'])
      bp.add_url_rule('/auth/login', endpoint='auth_login', view_func=self.auth_handler.login, methods=['POST'])
      bp.add_url_rule('/auth/me', endpoint='auth_me', view_func=self.auth_handler.me, methods=['GET'])
      bp.add_url_rule('/auth/logout', endpoint='auth_logout', view_func=self.auth_handler.logout, methods=['POST'])
      bp.add_url_rule('/sessions', endpoint='session_create', view_func=self.session_handler.create_session, methods=['POST'])
      bp.add_url_rule('/sessions', endpoint='session_list', view_func=self.session_handler.list_sessions, methods=['GET'])
      bp.add_url_rule('/sessions/<uuid:session_id>', endpoint='session_detail', view_func=self.session_handler.get_session, methods=['GET'])
      bp.add_url_rule('/sessions/<uuid:session_id>', endpoint='session_update', view_func=self.session_handler.update_session, methods=['PATCH'])
      bp.add_url_rule('/sessions/<uuid:session_id>', endpoint='session_delete', view_func=self.session_handler.delete_session, methods=['DELETE'])
      bp.add_url_rule('/sessions/<uuid:session_id>/messages', endpoint='session_messages_create', view_func=self.app_handler.completion, methods=['POST'])
      bp.add_url_rule('/sessions/<uuid:session_id>/documents', endpoint='session_documents_list', view_func=self.session_handler.list_documents, methods=['GET'])
      bp.add_url_rule('/sessions/<uuid:session_id>/documents', endpoint='session_documents_upload', view_func=self.session_handler.upload_documents, methods=['POST'])
      bp.add_url_rule('/sessions/<uuid:session_id>/documents/<uuid:document_id>', endpoint='session_documents_delete', view_func=self.session_handler.delete_document, methods=['DELETE'])
      bp.add_url_rule('/sessions/<uuid:session_id>/settings', endpoint='session_settings_get', view_func=self.session_handler.get_settings, methods=['GET'])
      bp.add_url_rule('/sessions/<uuid:session_id>/settings', endpoint='session_settings_update', view_func=self.session_handler.update_settings, methods=['PATCH'])
      bp.add_url_rule('/sessions/<uuid:session_id>/messages/<uuid:message_id>', endpoint='session_message_delete', view_func=self.session_handler.delete_message_pair, methods=['DELETE'])
      bp.add_url_rule('/message/create/<uuid:id>', endpoint='legacy_message_create_session', view_func=self.message_handle.create_session, methods = ["POST"])
      bp.add_url_rule('/message/<uuid:id>', endpoint='legacy_message_get_session', view_func=self.message_handle.get_session, methods=["GET"])
      bp.add_url_rule('/message/summary/<uuid:id>', endpoint='legacy_message_get_summary', view_func=self.message_handle.get_summary, methods=["GET"])
      bp.add_url_rule('/message/summary/<uuid:id>', endpoint='legacy_message_update_summary', view_func=self.message_handle.update_summary, methods=["POST"])
      bp.add_url_rule('/message/add/<uuid:id>', endpoint='legacy_message_get_messages', view_func=self.message_handle.get_messages, methods=["GET"])
      bp.add_url_rule('/message/add/<uuid:id>', endpoint='legacy_message_add_message', view_func=self.message_handle.add_message, methods=["POST"])

      #3. 在应用上注册蓝图
      app.register_blueprint(bp)
