from pkg.sqlalchemy import SQLAlchemy
from injector import Module, Binder
from internal.extension.database_extension import db

class ExtensionModule(Module):
    def configure(self, binder: Binder):
        binder.bind(SQLAlchemy, to=db)