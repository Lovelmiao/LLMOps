from flask import Flask

from internal.exception import CustomException
from internal.model.app import App
from internal.router import Router
from config.config import Config
from pkg.sqlalchemy import SQLAlchemy

from pkg.http_code import HttpCode
from pkg.response import json, Response


class Http(Flask):
    def __init__(self, *args, config: Config, db: SQLAlchemy, router: Router, **kwargs):
        super().__init__(*args, **kwargs)

        self.config.from_object(config)

        self.register_error_handler(Exception, self._register_error_handler)

        db.init_app(self)
        with self.app_context():
            _ = App()
            db.create_all()

        router.register_router(self)

    def _register_error_handler(self, error: Exception):
        if  isinstance(error, CustomException):
            return json(Response(
                code = error.code,
                message = error.message,
                data = error.data
            ))
        if self.debug:
            raise error
        else:
            return json(Response(
                code = HttpCode.FAIL,
                message = str(error),
                data = {}
            ))