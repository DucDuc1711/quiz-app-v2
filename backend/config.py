import os
from dotenv import load_dotenv

load_dotenv()

_BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    _db_path = os.path.join(_BASE_DIR, "instance", "quiz.db").replace("\\", "/")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///" + _db_path)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = False  # sẽ thiết lập 24 giờ qua timedelta trong app factory
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://127.0.0.1:5173")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret-key-123456789")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "test-jwt-secret-key-123456789")
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"
    WTF_CSRF_ENABLED = False
