import os

# Required by src.config.Settings; set before src is imported so tests don't need a real .env file.
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASS", "test")
os.environ.setdefault("DB_NAME", "test")

import pytest
from flask import Flask

from src.extensions import db
import src.models  # noqa: registers all models on db.metadata


@pytest.fixture()
def app_context():
    """An application context backed by SQLite, so db.session.flush()/commit()
    work in PaymentService tests without needing a real Postgres instance."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)
    with app.app_context():
        yield app
