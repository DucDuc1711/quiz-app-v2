import io
import pytest
from werkzeug.security import generate_password_hash
from extensions import db
from models import User


PNG_MIN = b"\x89PNG\r\n\x1a\n"
JPG_MIN = b"\xff\xd8\xff"
GIF_MIN = b"GIF89a"
WEBP_MIN = b"RIFF\x00\x00\x00\x00WEBP"


def get_teacher_token(client, username="tchu", email="tchu@example.com"):
    resp = client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": "Password123"
    })
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["access_token"]


def get_admin_token(client):
    with client.application.app_context():
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            admin = User(
                username="admupload",
                email="admupload@example.com",
                password_hash=generate_password_hash("AdminPassword123"),
                role="admin",
                is_active=True,
            )
            db.session.add(admin)
            db.session.commit()

    resp = client.post("/api/auth/admin/login", json={
        "username_or_email": "admupload",
        "password": "AdminPassword123"
    })
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _upload(client, headers, content, filename):
    return client.post("/api/teacher/uploads",
                       data={"file": (io.BytesIO(content), filename)},
                       headers=headers)


def test_upload_valid_images(client):
    token = get_teacher_token(client)
    headers = _auth_headers(token)
    for content, name in [
        (PNG_MIN, "a.png"),
        (JPG_MIN, "b.jpg"),
        (GIF_MIN, "c.gif"),
        (WEBP_MIN, "d.webp"),
    ]:
        resp = _upload(client, headers, content, name)
        assert resp.status_code == 201, resp.get_json()
        assert "url" in resp.get_json()


def test_upload_reject_svg(client):
    token = get_teacher_token(client, username="tchu2", email="tchu2@example.com")
    headers = _auth_headers(token)
    resp = _upload(client, headers, b"<svg></svg>", "image.svg")
    assert resp.status_code == 400, resp.get_json()


def test_upload_reject_fake_image(client):
    token = get_teacher_token(client, username="tchu3", email="tchu3@example.com")
    headers = _auth_headers(token)
    resp = _upload(client, headers, b"not an image content", "fake.png")
    assert resp.status_code == 400, resp.get_json()


def test_upload_reject_too_large(client):
    token = get_teacher_token(client, username="tchu4", email="tchu4@example.com")
    headers = _auth_headers(token)
    # Lon hon 2 MB nhung nho hon 5 MB -> spec muc 3 yeu cau ma loi 413
    big = b"\x00" * (2 * 1024 * 1024 + 1)
    resp = _upload(client, headers, big, "big.png")
    assert resp.status_code == 413, resp.get_json()


def test_upload_no_token(client):
    resp = _upload(client, None, PNG_MIN, "a.png")
    assert resp.status_code == 401, resp.get_json()


def test_upload_admin_forbidden(client):
    token = get_admin_token(client)
    headers = _auth_headers(token)
    resp = _upload(client, headers, PNG_MIN, "a.png")
    assert resp.status_code == 403, resp.get_json()


def test_upload_get_public(client):
    token = get_teacher_token(client, username="tchu5", email="tchu5@example.com")
    headers = _auth_headers(token)
    resp = _upload(client, headers, PNG_MIN, "public.png")
    assert resp.status_code == 201, resp.get_json()
    url = resp.get_json()["url"]
    filename = url.rsplit("/", 1)[-1]

    # GET cong khai: khong con token van tai duoc file vua upload
    resp = client.get(f"/api/uploads/{filename}")
    assert resp.status_code == 200, resp.get_json()
    assert resp.data == PNG_MIN
