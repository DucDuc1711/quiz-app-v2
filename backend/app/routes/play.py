from flask import Blueprint, jsonify, request
from datetime import datetime, timezone

from extensions import db, limiter
from models import Quiz, Question, Choice, Attempt, AttemptAnswer
from app.services.scoring import check_answer, compute_score, compute_time_spent, compute_ranking
from utils import error_response

play_bp = Blueprint("play", __name__)

GRACE_SECONDS = 2


def _now():
    return datetime.now(timezone.utc)


def _ensure_aware(dt):
    """Chuyen datetime naiv (tu SQLite) thanh co mui gio de phep tinh toan."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _clean_name(name):
    if not name:
        return ""
    cleaned = "".join(ch for ch in name if ord(ch) >= 32)
    cleaned = " ".join(cleaned.split())
    return cleaned


def _quiz_not_found():
    return error_response("Khong tim thay bo de voi ma nay.", 404)


def _quiz_closed():
    return error_response("Bo de dong hoac chua vao thoi gian lam bai.", 403)


def _get_attempt_or_404(token):
    attempt = Attempt.query.filter_by(token=token).first()
    if attempt is None:
        return None, error_response("Khong tim thay luot lam bai.", 404)
    return attempt, None, None


@play_bp.route("/lookup", methods=["GET"])
@limiter.limit("30/minute")
def lookup():
    code = (request.args.get("code") or "").strip()
    if not code:
        return error_response("Vui long nhap ma bo de.", 400)

    quiz = Quiz.query.filter_by(access_code=code).first()
    if quiz is None:
        return _quiz_not_found()

    now = _now()
    if not quiz.is_open:
        return _quiz_closed()
    if quiz.open_at and now < quiz.open_at:
        return _quiz_closed()
    if quiz.close_at and now > quiz.close_at:
        return _quiz_closed()

    return jsonify({
        "quiz": {
            "title": quiz.title,
            "description": quiz.description,
            "total_questions": len(quiz.questions),
            "question_time": quiz.question_time,
            "is_open": quiz.is_open,
            "message": "Bo de san sang lam bai." if quiz.is_open else "Bo de dang dong.",
        }
    }), 200


@play_bp.route("/join", methods=["POST"])
@limiter.limit("30/minute")
def join():
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    name = _clean_name(data.get("name") or "")
    device_id = (data.get("device_id") or "").strip()

    if not code:
        return error_response("Vui long nhap ma bo de.", 400)
    if not name:
        return error_response("Ten hoc sinh khong duoc bo trong.", 400)
    if len(name) > 40:
        return error_response("Ten hoc sinh toi da 40 ky tu.", 400)
    if not device_id:
        return error_response("Thieu thiet bi danh dau (device_id).", 400)

    quiz = Quiz.query.filter_by(access_code=code).first()
    if quiz is None:
        return _quiz_not_found()

    now = _now()
    if not quiz.is_open:
        return _quiz_closed()
    if quiz.open_at and now < quiz.open_at:
        return _quiz_closed()
    if quiz.close_at and now > quiz.close_at:
        return _quiz_closed()

    if not quiz.allow_retake:
        existing = Attempt.query.filter_by(quiz_id=quiz.id, device_id=device_id).first()
        if existing is not None:
            if existing.status == "finished":
                return error_response("Thiet bi nay da lam bo de nay.", 409)
            return jsonify({
                "attempt_token": existing.token,
                "quiz": {"title": quiz.title, "total_questions": len(quiz.questions)},
                "resumed": True,
            }), 200

    questions = quiz.questions
    question_ids = [q.id for q in questions]
    choice_orders = {}

    import random
    if quiz.shuffle_questions:
        random.shuffle(question_ids)

    for q in questions:
        choice_ids = [c.id for c in q.choices]
        if quiz.shuffle_choices:
            random.shuffle(choice_ids)
        choice_orders[str(q.id)] = choice_ids

    import secrets
    attempt = Attempt(
        token=secrets.token_urlsafe(24),
        quiz_id=quiz.id,
        student_name=name,
        device_id=device_id,
        status="in_progress",
        phase="question",
        current_index=0,
        question_started_at=None,
        question_order=question_ids,
        choice_orders=choice_orders,
        total_questions=len(questions),
        correct_answers=0,
        score=0.0,
        time_spent=0.0,
        tab_switch_count=0,
    )
    db.session.add(attempt)
    db.session.commit()

    return jsonify({
        "attempt_token": attempt.token,
        "quiz": {"title": quiz.title, "total_questions": len(questions)},
        "resumed": False,
    }), 201


def _build_question_payload(attempt, quiz, question, seconds_left):
    choices = []
    for c in question.choices:
        choices.append({"id": c.id, "content": c.content})
    return {
        "status": "in_progress",
        "phase": "question",
        "index": attempt.current_index,
        "total": attempt.total_questions,
        "question": {
            "id": question.id,
            "type": question.type,
            "content": question.content,
            "image_url": question.image_url,
            "choices": choices,
        },
        "time_limit": question.time_limit if question.time_limit is not None else quiz.question_time,
        "seconds_left": max(0, int(seconds_left)) if seconds_left is not None else None,
    }


def _build_feedback_payload(attempt, answer, question):
    correct_choice_ids = [c.id for c in question.choices if c.is_correct]
    return {
        "status": "in_progress",
        "phase": "feedback",
        "index": attempt.current_index,
        "total": attempt.total_questions,
        "feedback": {
            "question_id": question.id,
            "is_correct": answer.is_correct,
            "timed_out": answer.timed_out,
            "correct_choice_ids": correct_choice_ids,
            "selected_choice_ids": answer.selected_choice_ids or [],
            "explanation": question.explanation,
        },
        "is_last": attempt.current_index >= attempt.total_questions - 1,
    }


@play_bp.route("/<token>/state", methods=["GET"])
def state(token):
    attempt, err, code = _get_attempt_or_404(token)
    if err:
        return err, code

    if attempt.status == "finished":
        return jsonify({"status": "finished"}), 200

    quiz = attempt.quiz
    q_id = attempt.question_order[attempt.current_index]
    question = db.session.get(Question, q_id)
    if question is None:
        return error_response("Cau hoi khong ton tai."), 404

    now = _now()

    if attempt.question_started_at is None:
        attempt.question_started_at = now
        db.session.commit()
        started_at = now
    else:
        started_at = _ensure_aware(attempt.question_started_at)

    time_limit = question.time_limit if question.time_limit is not None else quiz.question_time
    elapsed = (now - started_at).total_seconds()
    seconds_left = time_limit - elapsed

    if elapsed > time_limit + GRACE_SECONDS:
        existing = AttemptAnswer.query.filter_by(
            attempt_id=attempt.id, question_id=question.id
        ).first()
        if existing is None:
            answer = AttemptAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_choice_ids=[],
                is_correct=False,
                timed_out=True,
                time_taken=elapsed,
            )
            db.session.add(answer)
            db.session.commit()
        else:
            answer = existing

        attempt.phase = "feedback"
        db.session.commit()
        return jsonify(_build_feedback_payload(attempt, answer, question)), 200

    return jsonify(_build_question_payload(attempt, quiz, question, seconds_left)), 200


@play_bp.route("/<token>/answer", methods=["POST"])
@limiter.limit("120/minute")
def answer(token):
    attempt, err, code = _get_attempt_or_404(token)
    if err:
        return err, code

    if attempt.status != "in_progress":
        return error_response("Luot lam da ket thuc."), 409
    if attempt.phase != "question":
        return error_response("Chi co the tra loi o cau hoi hien tai.", 409)

    data = request.get_json(silent=True)
    if data is None or "question_id" not in data or "choice_ids" not in data:
        return error_response("Thieu question_id hoac choice_ids.", 400)
    question_id = data.get("question_id")
    choice_ids = data.get("choice_ids") or []

    quiz = attempt.quiz
    q_id = attempt.question_order[attempt.current_index]
    question = Question.query.get(q_id)
    if question is None:
        return error_response("Cau hoi khong ton tai.", 404)

    if str(question.id) != str(question_id):
        return error_response("Khong hop le: chi duoc tra loi cau hoi hien tai.", 409)

    now = _now()
    if attempt.question_started_at is None:
        attempt.question_started_at = now
        started_at = now
    else:
        started_at = _ensure_aware(attempt.question_started_at)

    time_limit = question.time_limit if question.time_limit is not None else quiz.question_time
    elapsed = (now - started_at).total_seconds()
    timed_out = elapsed > time_limit + GRACE_SECONDS

    existing = AttemptAnswer.query.filter_by(
        attempt_id=attempt.id, question_id=question.id
    ).first()
    if existing is not None:
        return error_response("Cau hoi nay da duoc tra loi roi."), 409

    if timed_out:
        is_correct = False
        selected = []
    else:
        correct_ids = [c.id for c in question.choices if c.is_correct]
        is_correct = check_answer(choice_ids, correct_ids)
        selected = choice_ids

    answer = AttemptAnswer(
        attempt_id=attempt.id,
        question_id=question.id,
        selected_choice_ids=selected,
        is_correct=is_correct,
        timed_out=timed_out,
        time_taken=elapsed,
    )
    db.session.add(answer)

    attempt.phase = "feedback"
    db.session.commit()

    return jsonify({
        "feedback": {
            "question_id": question.id,
            "is_correct": is_correct,
            "timed_out": timed_out,
            "correct_choice_ids": [c.id for c in question.choices if c.is_correct],
            "selected_choice_ids": selected,
            "explanation": question.explanation,
        },
        "is_last": attempt.current_index >= attempt.total_questions - 1,
    }), 200


@play_bp.route("/<token>/next", methods=["POST"])
def next_question(token):
    attempt, err, code = _get_attempt_or_404(token)
    if err:
        return err, code

    if attempt.status != "in_progress":
        return error_response("Luot lam da ket thuc.", 409)
    if attempt.phase != "feedback":
        return error_response("Chi co the chuyen cau sau khi da tra loi cau hien tai.", 409)

    attempt.current_index += 1
    attempt.phase = "question"
    attempt.question_started_at = None

    if attempt.current_index >= attempt.total_questions:
        attempt.status = "finished"
        attempt.finished_at = _now()

        correct_count = AttemptAnswer.query.filter_by(
            attempt_id=attempt.id, is_correct=True
        ).count()
        answers = AttemptAnswer.query.filter_by(attempt_id=attempt.id).all()
        attempt.correct_answers = correct_count
        attempt.score = compute_score(correct_count, attempt.total_questions)
        attempt.time_spent = compute_time_spent(answers)
        db.session.commit()

        return jsonify({"status": "finished"}), 200

    db.session.commit()

    now = _now()
    if attempt.question_started_at is None:
        attempt.question_started_at = now
        db.session.commit()
        started_at = now
    else:
        started_at = _ensure_aware(attempt.question_started_at)

    quiz = attempt.quiz
    q_id = attempt.question_order[attempt.current_index]
    question = db.session.get(Question, q_id)
    if question is None:
        return error_response("Cau hoi khong ton tai."), 404

    time_limit = question.time_limit if question.time_limit is not None else quiz.question_time
    elapsed = (now - started_at).total_seconds()
    seconds_left = time_limit - elapsed

    return jsonify(_build_question_payload(attempt, quiz, question, seconds_left)), 200


@play_bp.route("/<token>/result", methods=["GET"])
def result(token):
    attempt, err, code = _get_attempt_or_404(token)
    if err:
        return err, code

    if attempt.status != "finished":
        return error_response("Chua xong bai, khong xem duoc ket qua.", 409)

    quiz = attempt.quiz

    attempts = Attempt.query.filter_by(quiz_id=quiz.id).all()
    ranking = compute_ranking(attempts, me_token=attempt.token)
    my_entry = next((r for r in ranking if r["is_me"]), None)
    my_rank = my_entry["rank"] if my_entry else None

    return jsonify({
        "student_name": attempt.student_name,
        "quiz_title": quiz.title,
        "score": attempt.score,
        "correct_answers": attempt.correct_answers,
        "total_questions": attempt.total_questions,
        "time_spent": attempt.time_spent,
        "rank": my_rank,
        "total_participants": len([a for a in attempts if a.status == "finished"]),
        "show_ranking": quiz.show_ranking,
    }), 200


@play_bp.route("/<token>/ranking", methods=["GET"])
def ranking(token):
    attempt, err, code = _get_attempt_or_404(token)
    if err:
        return err, code

    if attempt.status != "finished":
        return error_response("Chua xong bai, khong xem duoc bang xep hang.", 409)

    quiz = attempt.quiz
    if not quiz.show_ranking:
        return jsonify({"ranking": []}), 200

    attempts = Attempt.query.filter_by(quiz_id=quiz.id).all()
    ranking_list = compute_ranking(attempts, me_token=attempt.token)

    return jsonify({"ranking": ranking_list}), 200


@play_bp.route("/<token>/event", methods=["POST"])
@limiter.limit("60/minute")
def event(token):
    attempt, err, code = _get_attempt_or_404(token)
    if err:
        return err, code

    data = request.get_json(silent=True) or {}
    if data.get("type") == "tab_hidden":
        attempt.tab_switch_count = (attempt.tab_switch_count or 0) + 1
        db.session.commit()

    return "", 204