from dataclasses import dataclass, field
from typing import Any

from flask import jsonify

from pkg.http_code import HttpCode


@dataclass
class Response:
    code: HttpCode = HttpCode.SUCCESS
    message: str = ""
    data: Any = field(default_factory=dict)

def json(data: Response = None):
    return jsonify(data), 200

def success_json(message: str = "", data: Any = None):
    response = Response(
        code=HttpCode.SUCCESS,
        message=message,
        data=data
    )
    return json(response)

def validate_error_json(message: str = "", data: Any = None):
    response = Response(
        code=HttpCode.VALIDATE_ERROR,
        message=message,
        data=data
    )
    return json(response)

def fail_json(message: str = "", data: Any = None):
    response = Response(
        code=HttpCode.FAIL,
        message=message,
        data=data
    )
    return json(response)

def success_message(message: str = ""):
    return success_json(message=message)


