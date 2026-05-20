from dataclasses import field
from typing import Any
from pkg.response import HttpCode

class CustomException(Exception):
    code: HttpCode = HttpCode.FAIL
    message: str = ""
    data: Any = field(default_factory=dict)

    def __init__(self, message: str = "", data: Any = None):
        super().__init__()
        self.message = message
        self.data = data


class FailException(CustomException):
    code = HttpCode.FAIL

class NotFoundException(CustomException):
    code = HttpCode.NOT_FOUND

class UnauthorizedException(CustomException):
    code = HttpCode.UNAUTHORIZED

class ForbiddenException(CustomException):
    code = HttpCode.FORBIDDEN

class ValidationException(CustomException):
    code = HttpCode.VALIDATE_ERROR
