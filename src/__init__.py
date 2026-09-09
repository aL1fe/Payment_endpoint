from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from src.extensions import db, migrate

from src.config import settings


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = settings.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = settings.SQLALCHEMY_TRACK_MODIFICATIONS

    db.init_app(app)
    migrate.init_app(app, db)

    from src.routes.main import main_bp
    app.register_blueprint(main_bp)

    import src.models  # noqa

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        response = jsonify({"error": exc.description, "status": exc.code})
        response.status_code = exc.code
        return response

    return app
