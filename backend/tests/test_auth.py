import pytest
from extensions import db
from models import User


def test_register_cannot_create_admin(client):
    """Đăng ký không thể tạo admin được nếu gửi role=admin."""
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
    """Validation đăng ký: username, email, mật khẩu."""
    # Username quá ngắn
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

    # Mật khẩu quá ngắn
    resp = client.post("/api/auth/register", json={
        "username": "validuser",
        "email": "test@example.com",
        "password": "short",
    })
    assert resp.status_code == 400

    # Đúng dữ liệu
    resp = client.post("/api/auth/register", json={
        "username": "validuser",
        "email": "test@example.com",
        "password": "Password123",
    })
    assert resp.status_code == 201


def test_register_duplicate(client):
    """Không thể đăng ký trùng username hoặc email."""
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
    """Đăng nhập thành công."""
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
    """Đăng nhập sai mật khẩu."""
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
    """Tài khoản bị khóa không đăng nhập được."""
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


def test_register_case_insensitive_username_and_email(client):
    """Đăng ký và đăng nhập không phân biệt hoa thường, mật khẩu phân biệt."""
    resp = client.post("/api/auth/register", json={
        "username": "GiaoVien1",
        "email": "GiaoVien1@Gmail.com",
        "password": "GiaoVien1",
    })
    assert resp.status_code == 201, resp.get_json()
    data = resp.get_json()
    assert data["user"]["username"] == "giaovien1", data
    assert data["user"]["email"] == "giaovien1@gmail.com", data

    for login in ["giaovien1", "GIAOVIEN1", "GiaoVien1"]:
        r = client.post("/api/auth/login", json={
            "username_or_email": login, "password": "GiaoVien1",
        })
        assert r.status_code == 200, (login, r.get_json())
    for login in ["giaovien1@gmail.com", "GIAOVIEN1@GMAIL.COM", "GiaoVien1@Gmail.com"]:
        r = client.post("/api/auth/login", json={
            "username_or_email": login, "password": "GiaoVien1",
        })
        assert r.status_code == 200, (login, r.get_json())

    r = client.post("/api/auth/login", json={
        "username_or_email": "giaovien1", "password": "giavien1",
    })
    assert r.status_code == 401
    assert r.get_json()["error"] == "Tài khoản hoặc mật khẩu không chính xác."

    r = client.post("/api/auth/register", json={
        "username": "GIAOVIEN1", "email": "other@example.com", "password": "Password123",
    })
    assert r.status_code == 409
    assert r.get_json()["error"] == "Tên đăng nhập đã tồn tại."

    r = client.post("/api/auth/register", json={
        "username": "otheruser", "email": "GIAOVIEN1@GMAIL.COM", "password": "Password123",
    })
    assert r.status_code == 409
    assert r.get_json()["error"] == "Email đã được sử dụng."


def test_login_case_insensitive_stored_uppercase_email(client):
    """Tài khoản cũ lưu email hoa thường vẫn đăng nhập được bằng email thường."""
    client.post("/api/auth/register", json={
        "username": "olduser", "email": "OLDUSER@GMAIL.COM", "password": "Password123",
    })
    r = client.post("/api/auth/login", json={
        "username_or_email": "olduser@gmail.com", "password": "Password123",
    })
    assert r.status_code == 200, r.get_json()


def test_login_username_or_email_with_spaces(client):
    """username_or_email có khoảng trắng hai đầu vẫn vào được."""
    client.post("/api/auth/register", json={
        "username": "spuser", "email": "sp@example.com", "password": "Password123",
    })
    r = client.post("/api/auth/login", json={
        "username_or_email": "  spuser  ", "password": "Password123",
    })
    assert r.status_code == 200, r.get_json()


def test_password_keeps_leading_trailing_spaces(client):
    """Mật khẩu có khoảng trắng đầu/cuối không được cắt, so sánh nguyên văn."""
    client.post("/api/auth/register", json={
        "username": "pwuser", "email": "pw@example.com", "password": "Pass word ",
    })
    r = client.post("/api/auth/login", json={
        "username_or_email": "pwuser", "password": "Pass word ",
    })
    assert r.status_code == 200, r.get_json()
    r = client.post("/api/auth/login", json={
        "username_or_email": "pwuser", "password": "Pass word",
    })
    assert r.status_code == 401


def test_admin_login_case_insensitive(client):
    """Admin đăng nhập không phân biệt hoa thường tên."""
    from werkzeug.security import generate_password_hash
    with client.application.app_context():
        admin = User(username="AdMin1", email="ADMIN1@GMAIL.COM",
                     password_hash="x", role="admin", is_active=True)
        db.session.add(admin)
        db.session.commit()
        admin_id = admin.id
        admin = db.session.get(User, admin_id)
        admin.password_hash = generate_password_hash("AdminPass123")
        db.session.commit()
    r = client.post("/api/auth/admin/login", json={
        "username_or_email": "admin1", "password": "AdminPass123",
    })
    assert r.status_code == 200, r.get_json()
    r = client.post("/api/auth/admin/login", json={
        "username_or_email": "ADMIN1@GMAIL.COM", "password": "AdminPass123",
    })
    assert r.status_code == 200, r.get_json()