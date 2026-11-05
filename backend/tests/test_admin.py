import io
import pytest
from werkzeug.security import generate_password_hash
from extensions import db
from models import User, Quiz, Attempt, AttemptAnswer
from datetime import datetime, timezone
import uuid


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


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def get_teacher_token(client, username="tchadmin", email="tchadmin@example.com"):
    resp = client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": "Password123"
    })
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["access_token"]


def _create_quiz_via_teacher(client, token, title="Danh sach admin", is_public=True):
    resp = client.post("/api/teacher/quizzes", json={
        "title": title, "is_public": is_public
    }, headers=_auth_headers(token))
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["quiz"]["id"]


def _add_attempt_via_model(app, quiz_id):
    with app.app_context():
        token = f"att-{uuid.uuid4().hex[:12]}"
        a = Attempt(
            token=token, quiz_id=quiz_id, student_name="Hoc sinh admin",
            device_id="dev-admin", status="finished", phase="question",
            current_index=1, total_questions=1, correct_answers=1,
            score=8.0, time_spent=30.0, finished_at=datetime.now(timezone.utc),
        )
        db.session.add(a)
        db.session.commit()
        return a.id


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


def test_admin_patch_teacher_activate_deactivate(client):
    admin_token = get_admin_token(client)
    aheaders = _auth_headers(admin_token)

    teacher_token = get_teacher_token(client, username="tchpatch", email="tchpatch@example.com")
    with client.application.app_context():
        teacher = User.query.filter_by(username="tchpatch").first()
        teacher_id = teacher.id

    resp = client.patch(f"/api/admin/teachers/{teacher_id}", json={"is_active": False}, headers=aheaders)
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["is_active"] is False

    resp = client.get("/api/teacher/quizzes", headers=_auth_headers(teacher_token))
    assert resp.status_code == 401, resp.get_json()

    resp = client.patch(f"/api/admin/teachers/{teacher_id}", json={"is_active": True}, headers=aheaders)
    assert resp.status_code == 200
    assert resp.get_json()["is_active"] is True

    with client.application.app_context():
        admin = User.query.filter_by(role="admin").first()
    resp = client.patch(f"/api/admin/teachers/{admin.id}", json={"is_active": False}, headers=aheaders)
    assert resp.status_code == 403


def test_admin_delete_teacher_quizzes_invalid(client):
    admin_token = get_admin_token(client)
    aheaders = _auth_headers(admin_token)

    teacher_token = get_teacher_token(client, username="tchdel", email="tchdel@example.com")
    quiz_id = _create_quiz_via_teacher(client, teacher_token)
    with client.application.app_context():
        teacher = User.query.filter_by(username="tchdel").first()
        teacher_id = teacher.id

    resp = client.delete(f"/api/admin/teachers/{teacher_id}?quizzes=keep", headers=aheaders)
    assert resp.status_code == 400, resp.get_json()


def test_admin_delete_teacher_quizzes_transfer(client):
    admin_token = get_admin_token(client)
    aheaders = _auth_headers(admin_token)

    teacher_token = get_teacher_token(client, username="tchdelx", email="tchdelx@example.com")
    quiz_id = _create_quiz_via_teacher(client, teacher_token)
    with client.application.app_context():
        teacher = User.query.filter_by(username="tchdelx").first()
        teacher_id = teacher.id
        admin = User.query.filter_by(role="admin").first()
        admin_id = admin.id

    resp = client.delete(f"/api/admin/teachers/{teacher_id}?quizzes=transfer", headers=aheaders)
    assert resp.status_code == 200, resp.get_json()

    with client.application.app_context():
        # Giao vien bi xoa het
        assert User.query.get(teacher_id) is None
        # Bo de van con va duoc chuyen sang admin
        q = Quiz.query.get(quiz_id)
        assert q is not None
        assert q.owner_id == admin_id


def test_admin_delete_teacher_quizzes_delete(client):
    admin_token = get_admin_token(client)
    aheaders = _auth_headers(admin_token)

    teacher_token = get_teacher_token(client, username="tchdel2", email="tchdel2@example.com")
    quiz_id = _create_quiz_via_teacher(client, teacher_token)
    with client.application.app_context():
        teacher = User.query.filter_by(username="tchdel2").first()
        teacher_id = teacher.id

    resp = client.delete(f"/api/admin/teachers/{teacher_id}?quizzes=delete", headers=aheaders)
    assert resp.status_code == 200, resp.get_json()
    with client.application.app_context():
        assert Quiz.query.get(quiz_id) is None


def test_admin_quizzes_search(client):
    admin_token = get_admin_token(client)
    aheaders = _auth_headers(admin_token)

    teacher_token = get_teacher_token(client, username="tchq", email="tchq@example.com")
    _create_quiz_via_teacher(client, teacher_token, title="Toan admin search")

    resp = client.get("/api/admin/quizzes?search=Toan", headers=aheaders)
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()
    assert any(q["title"] == "Toan admin search" for q in data)


def test_admin_patch_quiz(client):
    admin_token = get_admin_token(client)
    aheaders = _auth_headers(admin_token)

    teacher_token = get_teacher_token(client, username="tchquizp", email="tchquizp@example.com")
    quiz_id = _create_quiz_via_teacher(client, teacher_token)

    resp = client.patch(f"/api/admin/quizzes/{quiz_id}", json={"is_open": False, "is_public": False}, headers=aheaders)
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["is_open"] is False
    assert resp.get_json()["is_public"] is False


def test_admin_delete_quiz(client):
    admin_token = get_admin_token(client)
    aheaders = _auth_headers(admin_token)

    teacher_token = get_teacher_token(client, username="tchquizd", email="tchquizd@example.com")
    quiz_id = _create_quiz_via_teacher(client, teacher_token)

    resp = client.delete(f"/api/admin/quizzes/{quiz_id}", headers=aheaders)
    assert resp.status_code == 200, resp.get_json()


def test_admin_attempts_search_and_quiz_id(client, app):
    admin_token = get_admin_token(client)
    aheaders = _auth_headers(admin_token)

    teacher_token = get_teacher_token(client, username="tchatt", email="tchatt@example.com")
    quiz_id = _create_quiz_via_teacher(client, teacher_token)
    attempt_id = _add_attempt_via_model(app, quiz_id)

    resp = client.get(f"/api/admin/attempts?quiz_id={quiz_id}", headers=aheaders)
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()
    assert any(a["id"] == attempt_id for a in data)

    resp = client.get("/api/admin/attempts?search=Hoc sinh admin", headers=aheaders)
    assert resp.status_code == 200, resp.get_json()
    assert any(a["student_name"] == "Hoc sinh admin" for a in resp.get_json())


def test_admin_delete_attempt(client, app):
    admin_token = get_admin_token(client)
    aheaders = _auth_headers(admin_token)

    teacher_token = get_teacher_token(client, username="tchattd", email="tchattd@example.com")
    quiz_id = _create_quiz_via_teacher(client, teacher_token)
    attempt_id = _add_attempt_via_model(app, quiz_id)

    resp = client.delete(f"/api/admin/attempts/{attempt_id}", headers=aheaders)
    assert resp.status_code == 200, resp.get_json()


def test_admin_bulk_delete_attempts(client, app):
    admin_token = get_admin_token(client)
    aheaders = _auth_headers(admin_token)

    teacher_token = get_teacher_token(client, username="tchattb", email="tchattb@example.com")
    quiz_id = _create_quiz_via_teacher(client, teacher_token)
    ids = [_add_attempt_via_model(app, quiz_id) for _ in range(3)]

    resp = client.post("/api/admin/attempts/bulk-delete", json={"ids": []}, headers=aheaders)
    assert resp.status_code == 400, resp.get_json()

    resp = client.post("/api/admin/attempts/bulk-delete", json={"ids": "notlist"}, headers=aheaders)
    assert resp.status_code == 400, resp.get_json()

    resp = client.post("/api/admin/attempts/bulk-delete", json={"ids": ids}, headers=aheaders)
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["deleted"] == 3
