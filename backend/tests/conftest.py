import pytest
from app import create_app
from extensions import db
from config import TestingConfig


@pytest.fixture
def app():
    app = create_app(TestingConfig)

    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    assert uri.startswith("sqlite:///:memory:"), (
        f"CRITICAL ERROR: SQLALCHEMY_DATABASE_URI is '{uri}', not in-memory SQLite! "
        "Tests must NEVER touch real database."
    )

    with app.app_context():
        assert app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("sqlite:///:memory:"), (
            "CRITICAL ERROR: SQLALCHEMY_DATABASE_URI must be in-memory SQLite before db.create_all()"
        )
        db.create_all()
        yield app
        assert app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("sqlite:///:memory:"), (
            "CRITICAL ERROR: SQLALCHEMY_DATABASE_URI must be in-memory SQLite before db.drop_all()"
        )
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
