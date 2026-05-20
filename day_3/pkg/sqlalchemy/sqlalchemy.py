from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy
from contextlib import contextmanager
import traceback
class SQLAlchemy(_SQLAlchemy):
    @contextmanager
    def auto_commit(self):
        try:
            yield
            self.session.commit()
        except Exception as e:
            traceback.print_exc()
            self.session.rollback()
            raise e