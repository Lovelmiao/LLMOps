import uuid
from dataclasses import dataclass

from flask import request, session
from injector import inject

from internal.service import AuthService
from pkg.response import success_json, validate_error_json, fail_json


def serialize_user(user):
    return {
        "id": str(user.id),
        "username": user.username,
    }


def get_login_user_id() -> uuid.UUID | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    try:
        return uuid.UUID(user_id)
    except ValueError:
        session.clear()
        return None


@inject
@dataclass
class AuthHandler:
    auth_service: AuthService

    def register(self):
        payload = request.get_json(silent=True) or {}
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""

        if len(username) < 3 or len(password) < 6:
            return validate_error_json("用户名至少 3 位，密码至少 6 位")

        if self.auth_service.get_user_by_username(username):
            return validate_error_json("用户名已存在")

        user = self.auth_service.create_user(username, password)
        session["user_id"] = str(user.id)
        return success_json("注册成功", {"user": serialize_user(user)})

    def login(self):
        payload = request.get_json(silent=True) or {}
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""

        user = self.auth_service.get_user_by_username(username)
        if not user or not self.auth_service.verify_password(user, password):
            return fail_json("用户名或密码错误")

        session["user_id"] = str(user.id)
        return success_json("登录成功", {"user": serialize_user(user)})

    def me(self):
        user_id = get_login_user_id()
        if not user_id:
            return success_json(data={"user": None})

        user = self.auth_service.get_user(user_id)
        if not user:
            session.clear()
            return success_json(data={"user": None})

        return success_json(data={"user": serialize_user(user)})

    def logout(self):
        session.clear()
        return success_json("已退出登录")
