import pytest


def get_teacher_token(client, username="tfix", email="tfix@example.com", password="Password123"):
    resp = client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert resp.status_code == 201
    return resp.get_json()["access_token"]


def test_question_validation_and_detail(client):
    token = get_teacher_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post("/api/teacher/quizzes", json={"title": "Quiz Fix"}, headers=headers)
    quiz_id = create_resp.get_json()["quiz"]["id"]

    # 1. POST câu hỏi thiếu choices, 1 đáp án, 7 đáp án, single có 2 đáp án đúng, true_false sai nội dung -> đều 400
    # Thiếu choices
    r1 = client.post(f"/api/teacher/quizzes/{quiz_id}/questions", json={
        "type": "single", "content": "Q1?"
    }, headers=headers)
    assert r1.status_code == 400

    # 1 đáp án (< 2)
    r2 = client.post(f"/api/teacher/quizzes/{quiz_id}/questions", json={
        "type": "single", "content": "Q1?",
        "choices": [{"content": "A", "is_correct": True}]
    }, headers=headers)
    assert r2.status_code == 400

    # 7 đáp án (> 6)
    r3 = client.post(f"/api/teacher/quizzes/{quiz_id}/questions", json={
        "type": "single", "content": "Q1?",
        "choices": [{"content": str(i), "is_correct": i == 1} for i in range(7)]
    }, headers=headers)
    assert r3.status_code == 400

    # single có 2 đáp án đúng
    r4 = client.post(f"/api/teacher/quizzes/{quiz_id}/questions", json={
        "type": "single", "content": "Q1?",
        "choices": [
            {"content": "A", "is_correct": True},
            {"content": "B", "is_correct": True}
        ]
    }, headers=headers)
    assert r4.status_code == 400

    # true_false sai nội dung đáp án
    r5 = client.post(f"/api/teacher/quizzes/{quiz_id}/questions", json={
        "type": "true_false", "content": "Q1?",
        "choices": [
            {"content": "Đúng", "is_correct": True},
            {"content": "Sai biet", "is_correct": False}
        ]
    }, headers=headers)
    assert r5.status_code == 400

    # Valid question (single, 2 choices, 1 correct)
    r_valid = client.post(f"/api/teacher/quizzes/{quiz_id}/questions", json={
        "type": "single", "content": "1+1=?",
        "choices": [
            {"content": "1", "is_correct": False},
            {"content": "2", "is_correct": True}
        ]
    }, headers=headers)
    assert r_valid.status_code == 201

    # GET bộ đề có câu hỏi và choices với is_correct
    detail_resp = client.get(f"/api/teacher/quizzes/{quiz_id}", headers=headers)
    assert detail_resp.status_code == 200
    data = detail_resp.get_json()
    assert "questions" in data
    assert len(data["questions"]) == 1
    q = data["questions"][0]
    assert len(q["choices"]) == 2
    assert any(c["is_correct"] for c in q["choices"])


def test_play_flow_seconds_left_and_answer_validation(client):
    token = get_teacher_token(client, username="tplay", email="tplay@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post("/api/teacher/quizzes", json={"title": "Play Flow"}, headers=headers)
    quiz_data = create_resp.get_json()["quiz"]
    quiz_id = quiz_data["id"]
    code = quiz_data["access_code"]

    client.post(f"/api/teacher/quizzes/{quiz_id}/questions", json={
        "type": "single", "content": "Color of sky?",
        "choices": [
            {"content": "Red", "is_correct": False},
            {"content": "Blue", "is_correct": True}
        ]
    }, headers=headers)

    client.post(f"/api/teacher/quizzes/{quiz_id}/questions", json={
        "type": "single", "content": "2+2=?",
        "choices": [
            {"content": "3", "is_correct": False},
            {"content": "4", "is_correct": True}
        ]
    }, headers=headers)

    # Join
    join_resp = client.post("/api/play/join", json={
        "code": code, "name": "HocSinh", "device_id": "dev-999"
    })
    assert join_resp.status_code == 201
    token_attempt = join_resp.get_json()["attempt_token"]

    # State -> seconds_left is a number, choices >= 2
    state_resp = client.get(f"/api/play/{token_attempt}/state")
    assert state_resp.status_code == 200
    s_data = state_resp.get_json()
    assert len(s_data["question"]["choices"]) >= 2
    assert isinstance(s_data["seconds_left"], (int, float))

    # Answer thiếu trường -> 400
    bad_ans = client.post(f"/api/play/{token_attempt}/answer", json={
        "question_id": s_data["question"]["id"]
    })
    assert bad_ans.status_code == 400
    assert "Thieu question_id hoac choice_ids" in bad_ans.get_json()["error"]

    # Answer đúng -> feedback có correct_choice_ids không rỗng
    correct_id = next(c["id"] for c in s_data["question"]["choices"] if c["content"] == "Blue")
    ans_resp = client.post(f"/api/play/{token_attempt}/answer", json={
        "question_id": s_data["question"]["id"],
        "choice_ids": [correct_id]
    })
    assert ans_resp.status_code == 200
    fb = ans_resp.get_json()["feedback"]
    assert len(fb["correct_choice_ids"]) > 0

    # Next -> seconds_left là số
    next_resp = client.post(f"/api/play/{token_attempt}/next")
    assert next_resp.status_code == 200
    next_data = next_resp.get_json()
    assert isinstance(next_data["seconds_left"], (int, float))
