from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from . import user
from . import document
from . import tag
from . import chat_history
from . import chat_session
from . import langchain_collection
from . import langchain_embedding