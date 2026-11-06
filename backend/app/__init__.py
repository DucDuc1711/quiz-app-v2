import os
from datetime import timedelta

from flask import Flask, jsonify

from app.config import Config
from extensions import db, migrate, jwt, cors, limiter


def create_app(config_object=None):
    app = Flask(__name__, instance_path=os.path.join(os.path.dirname(__file__), "..", "instance"))
    app.config.from_object(Config)
    if config_object:
        if isinstance(config_object, dict):
            app.config.update(config_object)
        else:
            app.config.from_object(config_object)

    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config.get("CORS_ORIGINS", "*"))
    limiter.init_app(app)

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from app.routes.play import play_bp
    app.register_blueprint(play_bp, url_prefix="/api/play")

    from app.routes.uploads import uploads_bp
    app.register_blueprint(uploads_bp, url_prefix="/api")

    from app.routes.teacher import teacher_bp
    app.register_blueprint(teacher_bp)

    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)

    from utils import register_error_handlers
    register_error_handlers(app)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        from models import User, db
        identity = jwt_data["sub"]
        user = db.session.get(User, int(identity))
        if user is None or not user.is_active:
            return None
        return user

    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_data):
        return jsonify({"error": "Token da het han. Vui long dang nhap lai."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({"error": "Token khong hop le: " + reason}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        return jsonify({"error": "Can xac thuc: " + reason}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(_jwt_header, _jwt_data):
        return jsonify({"error": "Token da bi thu hoi. Vui long dang nhap lai."}), 401

    from cli import register_cli
    register_cli(app)

    return app