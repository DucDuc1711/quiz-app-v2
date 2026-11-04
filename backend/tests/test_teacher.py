import pytest


def get_teacher_token(client, username="teacher1", email="teacher1@example.com", password="Password123"):
    resp = client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert resp.status_code == 201
    return resp.get_json()["access_token"]


def test_teacher_create_quiz(client):
    token = get_teacher_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/teacher/quizzes", json={
        "title": "De thi Toan",
        "description": "Kiem tra 1 tiet",
        "question_time": 30,
        "is_public": True
    }, headers=headers)

    assert resp.status_code == 201
    data = resp.get_json()
    assert "quiz" in data
    assert data["quiz"]["id"] is not None
    assert len(data["quiz"]["access_code"]) == 6


def test_teacher_get_quizzes_and_detail(client):
    token = get_teacher_token(client, username="teacher2", email="teacher2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post("/api/teacher/quizzes", json={
        "title": "De thi Ly",
        "description": "Kiem tra hoc ky"
    }, headers=headers)
    quiz_id = create_resp.get_json()["quiz"]["id"]

    resp = client.get("/api/teacher/quizzes", headers=headers)
    assert resp.status_code == 200
    quizzes = resp.get_json()
    assert len(quizzes) == 1
    assert quizzes[0]["id"] == quiz_id

    resp_detail = client.get(f"/api/teacher/quizzes/{quiz_id}", headers=headers)
    assert resp_detail.status_code == 200
    assert resp_detail.get_json()["id"] == quiz_id


def test_teacher_add_and_delete_question(client):
    token = get_teacher_token(client, username="teacher3", email="teacher3@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post("/api/teacher/quizzes", json={
        "title": "De thi Hoa"
    }, headers=headers)
    quiz_id = create_resp.get_json()["quiz"]["id"]

    q_resp = client.post(f"/api/teacher/quizzes/{quiz_id}/questions", json={
        "type": "single",
        "content": "Axiit la gi?",
        "time_limit": 30,
        "choices": [
            {"content": "A", "is_correct": True},
            {"content": "B", "is_correct": False}
        ]
    }, headers=headers)
    assert q_resp.status_code == 201
    q_id = q_resp.get_json()["id"]

    del_q_resp = client.delete(f"/api/teacher/questions/{q_id}", headers=headers)
    assert del_q_resp.status_code == 200
    
    # Verify deletion
    get_resp = client.get(f"/api/teacher/quizzes/{quiz_id}", headers=headers)
    assert get_resp.status_code == 200
    assert len(get_resp.get_json()["questions"]) == 0


def test_teacher_delete_quiz(client):
    token = get_teacher_token(client, username="teacher4", email="teacher4@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post("/api/teacher/quizzes", json={
        "title": "De thi Sinh"
    }, headers=headers)
    quiz_id = create_resp.get_json()["quiz"]["id"]

    del_resp = client.delete(f"/api/teacher/quizzes/{quiz_id}", headers=headers)
    assert del_resp.status_code == 200

    get_resp = client.get(f"/api/teacher/quizzes/{quiz_id}", headers=headers)
    assert get_resp.status_code == 404
