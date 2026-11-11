import pytest
from app import create_app
from app.config import TestingConfig
from extensions import db
from models import User, Quiz


@pytest.fixture
def app():
    app = create_app(TestingConfig)
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    assert uri.startswith("sqlite:///:memory:"), uri
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def _seed(app, args=None):
    runner = app.test_cli_runner()
    return runner.invoke(args=["seed-samples"] + (args or []))


def test_seed_samples_co_dau(app):
    with app.app_context():
        admin = User(username="admin", email="admin@example.com", password_hash="x", role="admin", is_active=True)
        db.session.add(admin)
        db.session.commit()

    res = _seed(app)
    assert res.exit_code == 0, res.output
    assert "Đã seed 2 bộ đề mẫu cho admin" in res.output

    with app.app_context():
        qs = Quiz.query.filter_by(owner_id=User.query.filter_by(role="admin").first().id).all()
        assert len(qs) == 2, qs
        titles = {q.title for q in qs}
        assert "Lập trình Python cơ bản" in titles
        assert "Kiến thức chung vui Việt" in titles
        # Không có chuỗi không dấu
        assert not any("Lap trinh Python co ban" == q.title for q in qs)
        assert not any("Kien thuc chung vui ve" == q.title for q in qs)
        # tags có dấu
        assert all(("mẫu" in (q.tags or "")) for q in qs)


def test_seed_samples_khong_nhan_doi(app):
    with app.app_context():
        admin = User(username="admin", email="admin@example.com", password_hash="x", role="admin", is_active=True)
        db.session.add(admin)
        db.session.commit()

    _seed(app)
    res2 = _seed(app)  # không --reset
    assert res2.exit_code == 0, res2.output
    assert "đã được seed trước đó" in res2.output

    with app.app_context():
        n = Quiz.query.filter_by(owner_id=User.query.filter_by(role="admin").first().id).count()
        assert n == 2, n  # không nhân đôi


def test_seed_samples_reset(app):
    with app.app_context():
        admin = User(username="admin", email="admin@example.com", password_hash="x", role="admin", is_active=True)
        db.session.add(admin)
        db.session.commit()

    _seed(app)
    res = _seed(app, ["--reset"])
    assert res.exit_code == 0, res.output
    assert "Đã seed 2 bộ đề mẫu cho admin" in res.output

    with app.app_context():
        n = Quiz.query.filter_by(owner_id=User.query.filter_by(role="admin").first().id).count()
        assert n == 2, n  # reset xóa rồi seed lại, vẫn 2
