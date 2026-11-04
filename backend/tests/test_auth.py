import pytest
from extensions import db
from models import User


def test_register_cannot_create_admin(client):
    """Dang ky khong the tao admin duoc duoc gui role=admin."""
    resp = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Password123",
        "role": "admin",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["user"]["role"] == "teacher"


def test_register_validation(client):
    """Validation dang ky: username, email, mat khau."""
    # Username qua ngan
    resp = client.post("/api/auth/register", json={
        "username": "abc",
        "email": "test@example.com",
        "password": "Password123",
    })
    assert resp.status_code == 400

    # Email sai
    resp = client.post("/api/auth/register", json={
        "username": "validuser",
        "email": "not-an-email",
        "password": "Password123",
    })
    assert resp.status_code == 400

    # Mat khau qua ngan
    resp = client.post("/api/auth/register", json={
        "username": "validuser",
        "email": "test@example.com",
        "password": "short",
    })
    assert resp.status_code == 400

    # Dung du lieu
    resp = client.post("/api/auth/register", json={
        "username": "validuser",
        "email": "test@example.com",
        "password": "Password123",
    })
    assert resp.status_code == 201


def test_register_duplicate(client):
    """Khong the dang ky trung username hoac email."""
    client.post("/api/auth/register", json={
        "username": "dupuser",
        "email": "dup@example.com",
        "password": "Password123",
    })
    resp = client.post("/api/auth/register", json={
        "username": "dupuser",
        "email": "other@example.com",
        "password": "Password123",
    })
    assert resp.status_code == 409

    resp = client.post("/api/auth/register", json={
        "username": "otheruser",
        "email": "dup@example.com",
        "password": "Password123",
    })
    assert resp.status_code == 409


def test_login_success(client):
    """Dang nhap thanh cong."""
    client.post("/api/auth/register", json={
        "username": "loguser",
        "email": "log@example.com",
        "password": "Password123",
    })
    resp = client.post("/api/auth/login", json={
        "username_or_email": "loguser",
        "password": "Password123",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert "access_token" in data


def test_login_wrong_password(client):
    """Dang nhap sai mat khau."""
    client.post("/api/auth/register", json={
        "username": "wronguser",
        "email": "wrong@example.com",
        "password": "Password123",
    })
    resp = client.post("/api/auth/login", json={
        "username_or_email": "wronguser",
        "password": "WrongPassword",
    })
    assert resp.status_code == 401


def test_login_inactive_account(client):
    """Tai khoan bi khoa khong dang nhap duoc."""
    client.post("/api/auth/register", json={
        "username": "inactive",
        "email": "inactive@example.com",
        "password": "Password123",
    })
    # Khoa tai khoan
    with client.application.app_context():
        from extensions import db
        user = User.query.filter_by(username="inactive").first()
        user.is_active = False
        db.session.commit()

    resp = client.post("/api/auth/login", json={
        "username_or_email": "inactive",
        "password": "Password123",
    })
    assert resp.status_code == 403


def test_admin_login_rejects_teacher(client):
    """admin/login tu choi giao vien."""
    client.post("/api/auth/register", json={
        "username": "teach",
        "email": "teach@example.com",
        "password": "Password123",
    })
    resp = client.post("/api/auth/admin/login", json={
        "username_or_email": "teach",
        "password": "Password123",
    })
    assert resp.status_code == 403


def test_me_endpoint(client):
    """GET /api/auth/me tra thong tin nguoi dung."""
    client.post("/api/auth/register", json={
        "username": "meuser",
        "email": "me@example.com",
        "password": "Password123",
    })
    login_resp = client.post("/api/auth/login", json={
        "username_or_email": "meuser",
        "password": "Password123",
    })
    token = login_resp.get_json()["access_token"]

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["user"]["username"] == "meuser"


def test_token_rejected_after_account_locked(client):
    """Token cu bi tu choi khi tai khoan bi khoa."""
    client.post("/api/auth/register", json={
        "username": "lockuser",
        "email": "lock@example.com",
        "password": "Password123",
    })
    login_resp = client.post("/api/auth/login", json={
        "username_or_email": "lockuser",
        "password": "Password123",
    })
    token = login_resp.get_json()["access_token"]

    # Khoa tai khoan
    with client.application.app_context():
        user = User.query.filter_by(username="lockuser").first()
        user.is_active = False
        db.session.commit()

    # Token cu bi tu choi (user_lookup_loader kiem tra is_active)
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401