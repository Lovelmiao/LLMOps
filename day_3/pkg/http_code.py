from enum import Enum

class HttpCode(str,Enum):
    SUCCESS = "success"
    FAIL = "fail"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    VALIDATE_ERROR = "validateError"

    # OK = 200
    # CREATED = 201
    # ACCEPTED = 202
    # NO_CONTENT = 204
    # BAD_REQUEST = 400
    # UNAUTHORIZED = 401
    # FORBIDDEN = 403
    # NOT_FOUND = 404
    # INTERNAL_SERVER_ERROR = 500
