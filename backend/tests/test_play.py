import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from extensions import db
from models import User, Quiz, Question, Choice, Attempt, AttemptAnswer
from app.services.scoring import check_answer, compute_score, compute_time_spent, compute_ranking


def _make_quiz(app_ctx, code="ABC123", allow_retake=False, question_time=30,
               shuffle_questions=False, shuffle_choices=False, show_ranking=True,
               open_at=None, close_at=None, is_open=True):
    with app_ctx:
        admin = User(username="admin", email="admin@test.com", password_hash="hash", role="admin", is_active=True)
        db.session.add(admin)
        db.session.flush()

        quiz = Quiz(
            owner_id=admin.id, title="Test Quiz", description="desc",
            access_code=code, is_open=is_open, question_time=question_time,
            shuffle_questions=shuffle_questions, shuffle_choices=shuffle_choices,
            show_ranking=show_ranking, allow_retake=allow_retake, is_public=True,
            open_at=open_at, close_at=close_at,
        )
        db.session.add(quiz)
        db.session.flush()

        q1 = Question(quiz_id=quiz.id, type="single", content="Cau 1?", order_num=1)
        db.session.add(q1)
        db.session.flush()
        db.session.add_all([
            Choice(question_id=q1.id, content="Dap an 1", is_correct=True, order_num=1),
            Choice(question_id=q1.id, content="Dap an 2", is_correct=False, order_num=2),
        ])

        q2 = Question(quiz_id=quiz.id, type="multiple", content="Cau 2?", order_num=2)
        db.session.add(q2)
        db.session.flush()
        db.session.add_all([
            Choice(question_id=q2.id, content="Dap an A", is_correct=True, order_num=1),
            Choice(question_id=q2.id, content="Dap an B", is_correct=False, order_num=2),
            Choice(question_id=q2.id, content="Dap an C", is_correct=True, order_num=3),
        ])

        q3 = Question(quiz_id=quiz.id, type="true_false", content="Cau 3?", order_num=3)
        db.session.add(q3)
        db.session.flush()
        db.session.add_all([
            Choice(question_id=q3.id, content="Dung", is_correct=True, order_num=1),
            Choice(question_id=q3.id, content="Sai", is_correct=False, order_num=2),
        ])

        db.session.commit()
        return code  # tra ve ma chuoi de tranh DetachedInstanceError


def test_check_answer_single_correct(app):
    with app.app_context():
        assert check_answer([1], [1]) is True
        assert check_answer([2], [1]) is False
        assert check_answer([], [1]) is False


def test_check_answer_multiple_correct(app):
    with app.app_context():
        assert check_answer([1, 3], [1, 3]) is True
        assert check_answer([1], [1, 3]) is False
        assert check_answer([1, 2, 3], [1, 3]) is False


def test_check_answer_true_false(app):
    with app.app_context():
        assert check_answer([1], [1]) is True
        assert check_answer([2], [1]) is False


def test_compute_score(app):
    with app.app_context():
        assert compute_score(5, 10) == 5.0
        assert compute_score(0, 10) == 0.0
        assert compute_score(10, 10) == 10.0


def test_compute_time_spent(app):
    with app.app_context():
        class A:
            time_taken = 10.5
        class B:
            time_taken = 5.25
        assert compute_time_spent([A(), B()]) == 15.75


def test_compute_ranking(app):
    with app.app_context():
        admin = User(username="admin", email="a@t.com", password_hash="h", role="admin")
        db.session.add(admin)
        db.session.flush()

        quiz = Quiz(owner_id=admin.id, title="Q", access_code="X1Y2Z3")
        db.session.add(quiz)
        db.session.flush()

        now = datetime.now(timezone.utc)

        def mk(name, score, time_spent, finished, token="tok"):
            a = Attempt(quiz_id=quiz.id, student_name=name, device_id="d",
                        token=token, status="finished", phase="question",
                        current_index=0, total_questions=5, correct_answers=int(score),
                        score=score, time_spent=time_spent,
                        started_at=now, finished_at=finished)
            db.session.add(a)
            return a

        a1 = mk("Alice", 10.0, 100.0, now, token="tok-alice")
        a2 = mk("Bob", 8.0, 90.0, now + timedelta(seconds=10), token="tok-bob")
        a3 = mk("Charlie", 8.0, 90.0, now + timedelta(seconds=20), token="tok-charlie")
        a4 = mk("Dave", 5.0, 200.0, now + timedelta(seconds=30), token="tok-dave")
        db.session.commit()

        ranking = compute_ranking([a1, a2, a3, a4], me_token=a3.token)
        assert ranking[0]["rank"] == 1
        assert ranking[0]["name"] == "Alice"
        assert ranking[1]["rank"] == 2
        assert ranking[1]["name"] == "Bob"
        assert ranking[2]["rank"] == 2
        assert ranking[2]["is_me"] is True
        assert ranking[3]["rank"] == 4


def test_join_valid(client, app):
    with app.app_context():
        code = _make_quiz(app.app_context())

    resp = client.post("/api/play/join", json={
        "code": code,
        "name": "Nguyen Van A",
        "device_id": "device-1",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert "attempt_token" in data
    assert data["quiz"]["title"] == "Test Quiz"
    assert data["resumed"] is False


def test_join_invalid_code(client):
    resp = client.post("/api/play/join", json={
        "code": "WRONG",
        "name": "Ten",
        "device_id": "device-1",
    })
    assert resp.status_code == 404


def test_join_quiz_closed(client, app):
    with app.app_context():
        code = _make_quiz(app.app_context(), is_open=False)

    resp = client.post("/api/play/join", json={
        "code": code,
        "name": "Ten",
        "device_id": "device-1",
    })
    assert resp.status_code == 403


def test_join_name_empty(client, app):
    with app.app_context():
        code = _make_quiz(app.app_context())

    resp = client.post("/api/play/join", json={
        "code": code,
        "name": "   ",
        "device_id": "device-1",
    })
    assert resp.status_code == 400


def test_join_device_limit_finished(client, app):
    with app.app_context():
        code = _make_quiz(app.app_context(), allow_retake=False)
        quiz = Quiz.query.filter_by(access_code=code).first()
        attempt = Attempt(
            token="tok-finished", quiz_id=quiz.id, student_name="Old",
            device_id="dev-1", status="finished", phase="question",
            current_index=0, total_questions=3, score=0.0, time_spent=0.0,
        )
        db.session.add(attempt)
        db.session.commit()

    resp = client.post("/api/play/join", json={
        "code": code,
        "name": "New",
        "device_id": "dev-1",
    })
    assert resp.status_code == 409


def test_join_device_resume_in_progress(client, app):
    with app.app_context():
        code = _make_quiz(app.app_context(), allow_retake=False)
        quiz = Quiz.query.filter_by(access_code=code).first()
        attempt = Attempt(
            token="tok-resume", quiz_id=quiz.id, student_name="Old",
            device_id="dev-1", status="in_progress", phase="question",
            current_index=0, question_started_at=None,
            question_order=[1, 2, 3], choice_orders={},
            total_questions=3, score=0.0, time_spent=0.0,
        )
        db.session.add(attempt)
        db.session.commit()

    resp = client.post("/api/play/join", json={
        "code": code,
        "name": "New",
        "device_id": "dev-1",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["resumed"] is True
    assert data["attempt_token"] == "tok-resume"


def test_join_allow_retake(client, app):
    with app.app_context():
        code = _make_quiz(app.app_context(), allow_retake=True)
        quiz = Quiz.query.filter_by(access_code=code).first()
        attempt = Attempt(
            token="tok-old", quiz_id=quiz.id, student_name="Old",
            device_id="dev-1", status="finished", phase="question",
            current_index=0, total_questions=3, score=0.0, time_spent=0.0,
        )
        db.session.add(attempt)
        db.session.commit()

    resp = client.post("/api/play/join", json={
        "code": code,
        "name": "New",
        "device_id": "dev-1",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["resumed"] is False
    assert data["attempt_token"] != "tok-old"


def _join_and_get_token(client, app, code=None, device_id="dev-1"):
    with app.app_context():
        if code is None:
            code = _make_quiz(app.app_context())
    resp = client.post("/api/play/join", json={
        "code": code, "name": "Hoc Vien", "device_id": device_id,
    })
    assert resp.status_code == 201
    return resp.get_json()["attempt_token"], code


def test_state_question_no_correct_in_payload(client, app):
    token, code = _join_and_get_token(client, app)
    resp = client.get(f"/api/play/{token}/state")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["phase"] == "question"
    assert data["question"]["id"] is not None
    for c in data["question"]["choices"]:
        assert "is_correct" not in c
    assert data["seconds_left"] is not None
    assert data["seconds_left"] > 0


def test_state_finished_after_all(client, app):
    token, code = _join_and_get_token(client, app)
    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        q_ids = attempt.question_order

    q1 = q_ids[0]
    client.post(f"/api/play/{token}/answer", json={"question_id": q1, "choice_ids": [1]})
    client.post(f"/api/play/{token}/next")

    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        q2 = attempt.question_order[attempt.current_index]
    client.post(f"/api/play/{token}/answer", json={"question_id": q2, "choice_ids": [3, 5]})
    client.post(f"/api/play/{token}/next")

    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        q3 = attempt.question_order[attempt.current_index]
    client.post(f"/api/play/{token}/answer", json={"question_id": q3, "choice_ids": [6]})
    resp = client.post(f"/api/play/{token}/next")
    assert resp.get_json()["status"] == "finished"

    resp = client.get(f"/api/play/{token}/state")
    assert resp.get_json()["status"] == "finished"


def test_answer_single_correct(client, app):
    token, code = _join_and_get_token(client, app)
    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        q1 = attempt.question_order[0]

    resp = client.post(f"/api/play/{token}/answer", json={"question_id": q1, "choice_ids": [1]})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["feedback"]["is_correct"] is True
    assert data["feedback"]["timed_out"] is False


def _get_correct_choice_ids(app_ctx, question_id):
    with app_ctx:
        q = Question.query.get(question_id)
        return [c.id for c in q.choices if c.is_correct]


def test_answer_multiple_correct(client, app):
    token, code = _join_and_get_token(client, app)
    client.post(f"/api/play/{token}/next")
    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        q2 = attempt.question_order[attempt.current_index]
    correct_ids = _get_correct_choice_ids(app.app_context(), q2)

    resp = client.post(f"/api/play/{token}/answer", json={"question_id": q2, "choice_ids": correct_ids})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["feedback"]["is_correct"] is True


def test_answer_true_false_correct(client, app):
    token, code = _join_and_get_token(client, app)
    client.post(f"/api/play/{token}/next")
    client.post(f"/api/play/{token}/next")
    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        q3 = attempt.question_order[attempt.current_index]
    correct_ids = _get_correct_choice_ids(app.app_context(), q3)

    resp = client.post(f"/api/play/{token}/answer", json={"question_id": q3, "choice_ids": correct_ids})
    assert resp.status_code == 200
    assert resp.get_json()["feedback"]["is_correct"] is True


def test_answer_reject_wrong_phase(client, app):
    token, code = _join_and_get_token(client, app)
    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        q1 = attempt.question_order[0]
    client.post(f"/api/play/{token}/answer", json={"question_id": q1, "choice_ids": [1]})
    resp = client.post(f"/api/play/{token}/answer", json={"question_id": q1, "choice_ids": [1]})
    assert resp.status_code == 409


def test_answer_reject_wrong_question(client, app):
    token, code = _join_and_get_token(client, app)
    resp = client.post(f"/api/play/{token}/answer", json={"question_id": 9999, "choice_ids": [1]})
    assert resp.status_code == 409


def test_state_auto_timeout(client, app):
    token, code = _join_and_get_token(client, app)
    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        quiz = attempt.quiz
        quiz.question_time = 1
        # Đặt question_started_at quá hạn 10 giây (vượt limit 1s, không có ân hạn)
        attempt.question_started_at = datetime.now(timezone.utc) - timedelta(seconds=10)
        db.session.commit()

    resp = client.get(f"/api/play/{token}/state")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["phase"] == "feedback"
    assert data["feedback"]["timed_out"] is True


def test_answer_over_limit_is_timeout(client, app):
    token, code = _join_and_get_token(client, app)
    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        quiz = attempt.quiz
        quiz.question_time = 1
        attempt.question_started_at = datetime.now(timezone.utc) - timedelta(seconds=10)
        db.session.commit()
        q1 = attempt.question_order[0]

    # Qua han nhung van chon dung -> timed_out true, is_correct true (van cham lua chon da chon)
    resp = client.post(f"/api/play/{token}/answer", json={"question_id": q1, "choice_ids": [1]})
    assert resp.status_code == 200
    fb = resp.get_json()["feedback"]
    assert fb["timed_out"] is True
    assert fb["is_correct"] is True
    assert fb["selected_choice_ids"] == [1]

    # Chuyen sang cau 2, dat qua han, chon sai -> timed_out true, is_correct false
    client.post(f"/api/play/{token}/next")
    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        attempt.question_started_at = datetime.now(timezone.utc) - timedelta(seconds=10)
        db.session.commit()
        q2 = attempt.question_order[attempt.current_index]

    resp2 = client.post(f"/api/play/{token}/answer", json={"question_id": q2, "choice_ids": [4]})
    assert resp2.status_code == 200
    fb2 = resp2.get_json()["feedback"]
    assert fb2["timed_out"] is True
    assert fb2["is_correct"] is False
    assert fb2["selected_choice_ids"] == [4]


def test_result_blocked_before_finish(client, app):
    token, code = _join_and_get_token(client, app)
    resp = client.get(f"/api/play/{token}/result")
    assert resp.status_code == 409


def test_ranking_blocked_before_finish(client, app):
    token, code = _join_and_get_token(client, app)
    resp = client.get(f"/api/play/{token}/ranking")
    assert resp.status_code == 409


def _answer_current_question(client, app, token):
    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        q_id = attempt.question_order[attempt.current_index]
        q = Question.query.get(q_id)
        correct_ids = [c.id for c in q.choices if c.is_correct]
    resp = client.post(f"/api/play/{token}/answer", json={
        "question_id": q_id, "choice_ids": correct_ids,
    })
    assert resp.status_code == 200
    assert resp.get_json()["feedback"]["is_correct"] is True
    return q_id


def test_result_and_ranking_after_finish(client, app):
    token, code = _join_and_get_token(client, app)

    for _ in range(3):
        _answer_current_question(client, app, token)
        client.post(f"/api/play/{token}/next")

    resp = client.get(f"/api/play/{token}/result")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["score"] == 10.0
    assert data["correct_answers"] == 3
    assert data["total_questions"] == 3
    assert data["show_ranking"] is True

    resp = client.get(f"/api/play/{token}/ranking")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["ranking"]) == 1
    assert data["ranking"][0]["is_me"] is True
    assert data["ranking"][0]["rank"] == 1


def test_answer_empty_choice_ids(client, app):
    """choice_ids rong la hop lap, tinh la sai."""
    token, code = _join_and_get_token(client, app)
    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        q1 = attempt.question_order[0]

    resp = client.post(f"/api/play/{token}/answer", json={"question_id": q1, "choice_ids": []})
    assert resp.status_code == 200
    fb = resp.get_json()["feedback"]
    assert fb["is_correct"] is False
    assert fb["selected_choice_ids"] == []
    assert fb["timed_out"] is False


def test_answer_missing_fields(client, app):
    """Chi tra 400 khi thieu hang trieu question_id hoac choice_ids."""
    token, code = _join_and_get_token(client, app)
    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        q1 = attempt.question_order[0]

    resp = client.post(f"/api/play/{token}/answer", json={"question_id": q1})
    assert resp.status_code == 400

    resp = client.post(f"/api/play/{token}/answer", json={"choice_ids": [1]})
    assert resp.status_code == 400

    resp = client.post(f"/api/play/{token}/answer", json={})
    assert resp.status_code == 400


def test_state_after_limit_no_answer(client, app):
    """State qua limit chua answer -> tu ghi khong tra loi, chuyen phase feedback."""
    token, code = _join_and_get_token(client, app)
    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        quiz = attempt.quiz
        quiz.question_time = 1
        attempt.question_started_at = datetime.now(timezone.utc) - timedelta(seconds=10)
        db.session.commit()

    resp = client.get(f"/api/play/{token}/state")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["phase"] == "feedback"
    assert data["feedback"]["timed_out"] is True
    assert data["feedback"]["selected_choice_ids"] == []
    assert data["feedback"]["is_correct"] is False

    # Sau khi da tu ghi khong tra loi, khong the tra loi lai duoc (409)
    with app.app_context():
        attempt = Attempt.query.filter_by(token=token).first()
        q1 = attempt.question_order[0]
    resp2 = client.post(f"/api/play/{token}/answer", json={"question_id": q1, "choice_ids": [1]})
    assert resp2.status_code == 409


def test_event_tab_hidden(client, app):
    token, code = _join_and_get_token(client, app)
    resp = client.post(f"/api/play/{token}/event", json={"type": "tab_hidden"})
    assert resp.status_code == 204