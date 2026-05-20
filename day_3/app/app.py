from pkg.sqlalchemy import SQLAlchemy
from injector import Injector, singleton, Binder

from internal.router import Router
from internal.server import Http
import dotenv
from config.config import Config
from internal.extension.database_extension import db
from .module import ExtensionModule

dotenv.load_dotenv()

injector = Injector([ExtensionModule()])

config = Config()

app = Http(__name__, config=config, db=injector.get(SQLAlchemy), router=injector.get(Router))

if __name__ == "__main__":
    app.run(debug=True)
