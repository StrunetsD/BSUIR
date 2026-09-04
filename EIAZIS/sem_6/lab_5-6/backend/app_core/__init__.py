from flask import Flask

from .api.chat import chat_bp
from .api.health import health_bp
from .api.rag import rag_bp
from .bootstrap import bootstrap_infrastructure


def create_app() -> Flask:
    app = Flask(__name__)
    bootstrap_infrastructure()
    app.register_blueprint(health_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(rag_bp)
    return app
