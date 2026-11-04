import pytest
from werkzeug.security import generate_password_hash
from extensions import db
from models import User


def get_admin_token(client):
    with client.application.app_context():
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            admin = User(
                username="adminuser",
                email="admin@example.com",
                password_hash=generate_password_hash("AdminPassword123"),
                role="admin",
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()

    resp = client.post("/api/auth/admin/login", json={
        "username_or_email": "adminuser",
        "password": "AdminPassword123"
    })
    assert resp.status_code == 200
    return resp.get_json()["access_token"]


def test_admin_get_stats(client):
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/admin/stats", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total_users" in data
    assert "total_quizzes" in data
    assert "total_attempts" in data


def test_admin_get_teachers(client):
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/auth/register", json={
        "username": "teacherforadmin",
        "email": "tadmin@example.com",
        "password": "Password123"
    })

    resp = client.get("/api/admin/teachers", headers=headers)
    assert resp.status_code == 200
    teachers = resp.get_json()
    assert len(teachers) >= 1
    usernames = [t["username"] for t in teachers]
    assert "teacherforadmin" in usernames


def test_admin_cannot_delete_self(client):
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    with client.application.app_context():
        admin = User.query.filter_by(role="admin").first()
        admin_id = admin.id

    resp = client.delete(f"/api/admin/teachers/{admin_id}", headers=headers)
    assert resp.status_code == 403
