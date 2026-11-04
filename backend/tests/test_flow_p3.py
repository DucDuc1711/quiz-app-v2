import pytest
from werkzeug.security import generate_password_hash
from extensions import db
from models import User


def test_regression_register_and_teacher_quiz_creation(client):
    """Register teacher -> get access_token -> POST /api/teacher/quizzes returns 201."""
    reg_resp = client.post("/api/auth/register", json={
        "username": "regteacher",
        "email": "regteacher@example.com",
        "password": "Password123"
    })
    assert reg_resp.status_code == 201
    token = reg_resp.get_json()["access_token"]

    resp = client.post("/api/teacher/quizzes", json={
        "title": "Quiz Regression Test",
        "description": "Checking post-register token access"
    }, headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 201
    assert "quiz" in resp.get_json()


def test_regression_teacher_calling_admin_route_gets_403(client):
    """Teacher token calling /api/admin/stats returns 403."""
    reg_resp = client.post("/api/auth/register", json={
        "username": "teacherforadmincheck",
        "email": "teachcheck@example.com",
        "password": "Password123"
    })
    token = reg_resp.get_json()["access_token"]

    resp = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_regression_admin_calling_teacher_route_gets_403(client):
    """Admin token calling /api/teacher/quizzes returns 403."""
    with client.application.app_context():
        admin = User(
            username="p3admin",
            email="p3admin@example.com",
            password_hash=generate_password_hash("AdminPassword123"),
            role="admin",
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()

    login_resp = client.post("/api/auth/admin/login", json={
        "username_or_email": "p3admin",
        "password": "AdminPassword123"
    })
    assert login_resp.status_code == 200
    admin_token = login_resp.get_json()["access_token"]

    resp = client.post("/api/teacher/quizzes", json={
        "title": "Admin Attempting Teacher Quiz"
    }, headers={"Authorization": f"Bearer {admin_token}"})

    assert resp.status_code == 403


def test_locked_teacher_rejected_on_teacher_route(client):
    """Locked teacher token is immediately rejected with 401."""
    reg_resp = client.post("/api/auth/register", json={
        "username": "lockedteacher",
        "email": "lockedteacher@example.com",
        "password": "Password123"
    })
    token = reg_resp.get_json()["access_token"]

    with client.application.app_context():
        user = User.query.filter_by(username="lockedteacher").first()
        user.is_active = False
        db.session.commit()

    resp = client.post("/api/teacher/quizzes", json={
        "title": "Locked Teacher Quiz"
    }, headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 401
