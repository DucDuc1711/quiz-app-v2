from flask import Blueprint, jsonify, request
from datetime import datetime, timezone

from extensions import db, limiter
from models import Quiz, Question, Choice, Attempt, AttemptAnswer
from app.services.scoring import check_answer, compute_score, compute_time_spent, compute_ranking
from utils import error_response

play_bp = Blueprint("play", __name__)

FEEDBACK_SECONDS = 3

def _now():
    return datetime.now(timezone.utc)


def _ensure_aware(dt):
    """Chuyen datetime naiv (tu SQLite) thanh co mui gio de phep tinh toan."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _feedback_seconds_left(attempt):
    if attempt.feedback_started_at is None:
        return FEEDBACK_SECONDS
    started = _ensure_aware(attempt.feedback_started_at)
    elapsed = (_now() - started).total_seconds()
    return round(max(0.0, FEEDBACK_SECONDS - elapsed), 2)


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
    choices = [{"id": c.id, "content": c.content} for c in question.choices]
    return {
        "status": "in_progress",
        "phase": "feedback",
        "index": attempt.current_index,
        "total": attempt.total_questions,
        "question": {
            "id": question.id,
            "type": question.type,
            "content": question.content,
            "image_url": question.image_url,
            "choices": choices,
        },
        "feedback": {
            "question_id": question.id,
            "is_correct": answer.is_correct,
            "timed_out": answer.timed_out,
            "correct_choice_ids": correct_choice_ids,
            "selected_choice_ids": answer.selected_choice_ids or [],
        },
        "feedback_seconds_left": _feedback_seconds_left(attempt),
        "is_last": attempt.current_index >= attempt.total_questions - 1,
    }


def _clean_name(name):
    if not name:
        return ""
    cleaned = "".join(ch for ch in name if ord(ch) >= 32)
    cleaned = " ".join(cleaned.split())
    return cleaned


def _quiz_not_found():
    return error_response("Không tìm thấy bộ đề với mã này.", 404)


def _quiz_closed():
    return error_response("Bộ đề đang đóng hoặc chưa tới thời gian làm bài.", 403)


def _get_attempt_or_404(token):
    attempt = Attempt.query.filter_by(token=token).first()
    if attempt is None:
        return None, error_response("Không tìm thấy lượt làm bài.", 404)
    return attempt, None


@play_bp.route("/lookup", methods=["GET"])
@limiter.limit("30/minute")
def lookup():
    code = (request.args.get("code") or "").strip()
    if not code:
        return error_response("Vui lòng nhập mã bộ đề.", 400)

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
            "message": "Bộ đề đã mở làm bài." if quiz.is_open else "Bộ đề đang đóng.",
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
        return error_response("Vui lòng nhập mã bộ đề.", 400)
    if not name:
        return error_response("Tên học sinh không được để trống.", 400)
    if len(name) > 40:
        return error_response("Tên học sinh tối đa 40 ký tự.", 400)
    if not device_id:
        return error_response("Thiếu mã định danh thiết bị (device_id).", 400)

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

    # Kiểm tra xem thiết bị có đang có attempt in_progress cho bộ đề này không
    existing_in_progress = Attempt.query.filter_by(
        quiz_id=quiz.id, device_id=device_id, status="in_progress"
    ).first()
    if existing_in_progress is not None:
        return jsonify({
            "attempt_token": existing_in_progress.token,
            "quiz": {"title": quiz.title, "total_questions": len(quiz.questions)},
            "resumed": True,
        }), 200

    # Nếu không có in_progress (chưa làm hoặc lượt cũ đã finished) -> tao luot moi
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
    choices = [{"id": c.id, "content": c.content} for c in question.choices]
    return {
        "status": "in_progress",
        "phase": "feedback",
        "index": attempt.current_index,
        "total": attempt.total_questions,
        "question": {
            "id": question.id,
            "type": question.type,
            "content": question.content,
            "image_url": question.image_url,
            "choices": choices,
        },
        "feedback": {
            "question_id": question.id,
            "is_correct": answer.is_correct,
            "timed_out": answer.timed_out,
            "correct_choice_ids": correct_choice_ids,
            "selected_choice_ids": answer.selected_choice_ids or [],
        },
        "feedback_seconds_left": _feedback_seconds_left(attempt),
        "is_last": attempt.current_index >= attempt.total_questions - 1,
    }


@play_bp.route("/<token>/state", methods=["GET"])
def state(token):
    attempt, err = _get_attempt_or_404(token)
    if err:
        return err

    if attempt.status == "finished":
        return jsonify({"status": "finished"}), 200

    quiz = attempt.quiz
    q_id = attempt.question_order[attempt.current_index]
    question = db.session.get(Question, q_id)
    if question is None:
        return error_response("Câu hỏi không tồn tại.", 404)

    now = _now()

    if attempt.question_started_at is None:
        attempt.question_started_at = now
        db.session.commit()
        started_at = now
    else:
        started_at = _ensure_aware(attempt.question_started_at)

    time_limit = question.time_limit if question.time_limit is not None else quiz.question_time
    elapsed = (now - started_at).total_seconds()

    # Luôn đọc attempt.phase: nếu đang ở feedback thì trả payload phản hồi
    # (không trả lại câu hỏi nữa) — khắc phục lỗi gốc state() không đọc phase.
    if attempt.phase == "feedback":
        answer = AttemptAnswer.query.filter_by(
            attempt_id=attempt.id, question_id=question.id
        ).first()
        if answer is None:
            # Chưa có bản ghi -> ghi "không trả lời" rồi trả feedback.
            answer = AttemptAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_choice_ids=[],
                is_correct=False,
                timed_out=True,
                time_taken=min(elapsed, time_limit),
            )
            db.session.add(answer)
            attempt.phase = "feedback"
            if attempt.feedback_started_at is None:
                attempt.feedback_started_at = now
            db.session.commit()
        elif attempt.feedback_started_at is None:
            # Dữ liệu cũ: gán feedback_started_at = bây giờ.
            attempt.feedback_started_at = now
            db.session.commit()
        return jsonify(_build_feedback_payload(attempt, answer, question)), 200

    # phase == "question": đã quá hạn và chưa trả lời -> tự ghi "không trả lời",
    # chuyển sang feedback. Không có ân hạn.
    if elapsed > time_limit:
        answer = AttemptAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_choice_ids=[],
            is_correct=False,
            timed_out=True,
            time_taken=min(elapsed, time_limit),
        )
        db.session.add(answer)
        attempt.phase = "feedback"
        attempt.feedback_started_at = now
        db.session.commit()
        return jsonify(_build_feedback_payload(attempt, answer, question)), 200

    seconds_left = max(0, int(time_limit - elapsed)) if time_limit is not None else None
    return jsonify(_build_question_payload(attempt, quiz, question, seconds_left)), 200


@play_bp.route("/<token>/answer", methods=["POST"])
@limiter.limit("120/minute")
def answer(token):
    attempt, err = _get_attempt_or_404(token)
    if err:
        return err

    if attempt.status != "in_progress":
        return error_response("Lượt làm đã kết thúc.", 409)
    if attempt.phase != "question":
        return error_response("Chỉ có thể trả lời câu hỏi hiện tại.", 409)

    data = request.get_json(silent=True)
    if data is None or "question_id" not in data or "choice_ids" not in data:
        return error_response("Thiếu question_id hoặc choice_ids.", 400)
    question_id = data.get("question_id")
    choice_ids = data.get("choice_ids")

    if not isinstance(choice_ids, list):
        return error_response("choice_ids phải là danh sách.", 400)


    quiz = attempt.quiz
    q_id = attempt.question_order[attempt.current_index]
    question = db.session.get(Question, q_id)
    if question is None:
        return error_response("Câu hỏi không tồn tại.", 404)

    if str(question.id) != str(question_id):
        return error_response("Chỉ có thể trả lời câu hỏi hiện tại.", 409)
    # Mọi id đáp án gửi lên phải thuộc câu hỏi hiện tại.
    valid_choice_ids = {c.id for c in question.choices}
    for cid in choice_ids:
        if cid not in valid_choice_ids:
            return error_response("Một hoặc nhiều đáp án không thuộc câu hỏi này.", 400)

    now = _now()
    if attempt.question_started_at is None:
        attempt.question_started_at = now
        started_at = now
    else:
        started_at = _ensure_aware(attempt.question_started_at)

    time_limit = question.time_limit if question.time_limit is not None else quiz.question_time
    elapsed = (now - started_at).total_seconds()
    timed_out = elapsed > time_limit

    existing = AttemptAnswer.query.filter_by(
        attempt_id=attempt.id, question_id=question.id
    ).first()
    if existing is not None:
        return error_response("Câu hỏi này đã được trả lời rồi.", 409)

    # Kiểm tra câu single/true_false chỉ được chọn tối đa 1 đáp án.
    unique_choice_ids = list(dict.fromkeys(choice_ids))
    if question.type in ("single", "true_false") and len(unique_choice_ids) > 1:
        return error_response("Câu này chỉ được chọn một đáp án.", 400)

    correct_ids = [c.id for c in question.choices if c.is_correct]
    is_correct = check_answer(unique_choice_ids, correct_ids)
    selected = unique_choice_ids

    answer = AttemptAnswer(
        attempt_id=attempt.id,
        question_id=question.id,
        selected_choice_ids=selected,
        is_correct=is_correct,
        timed_out=timed_out,
        time_taken=min(elapsed, time_limit),
    )
    db.session.add(answer)

    attempt.phase = "feedback"
    attempt.feedback_started_at = now
    db.session.commit()

    return jsonify({
        "feedback": {
            "question_id": question.id,
            "is_correct": is_correct,
            "timed_out": timed_out,
            "correct_choice_ids": [c.id for c in question.choices if c.is_correct],
            "selected_choice_ids": selected,
        },
        "feedback_seconds_left": FEEDBACK_SECONDS,
        "is_last": attempt.current_index >= attempt.total_questions - 1,
    }), 200


@play_bp.route("/<token>/next", methods=["POST"])
def next_question(token):
    attempt, err = _get_attempt_or_404(token)
    if err:
        return err

    if attempt.status != "in_progress":
        return error_response("Lượt làm đã kết thúc.", 409)
    if attempt.phase != "feedback":
        return error_response("Chỉ có thể chuyển câu sau khi đã trả lời câu hiện tại.", 409)

    attempt.current_index += 1
    attempt.phase = "question"
    attempt.question_started_at = None
    attempt.feedback_started_at = None

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
        return error_response("Câu hỏi không tồn tại.", 404)

    time_limit = question.time_limit if question.time_limit is not None else quiz.question_time
    elapsed = (now - started_at).total_seconds()
    seconds_left = max(0, int(time_limit - elapsed))

    return jsonify(_build_question_payload(attempt, quiz, question, seconds_left)), 200


@play_bp.route("/<token>/result", methods=["GET"])
def result(token):
    attempt, err = _get_attempt_or_404(token)
    if err:
        return err

    if attempt.status != "finished":
        return error_response("Chưa làm xong bài nên chưa xem được kết quả.", 409)

    quiz = attempt.quiz

    attempts = Attempt.query.filter_by(quiz_id=quiz.id).all()
    ranking = compute_ranking(attempts, me_token=attempt.device_id)
    my_entry = next((r for r in ranking if r["is_me"]), None)
    my_rank = my_entry["rank"] if my_entry else None
    total_participants = len({a.device_id for a in attempts if a.status == "finished"})

    return jsonify({
        "student_name": attempt.student_name,
        "quiz_title": quiz.title,
        "score": attempt.score,
        "correct_answers": attempt.correct_answers,
        "total_questions": attempt.total_questions,
        "time_spent": attempt.time_spent,
        "rank": my_rank,
        "total_participants": total_participants,
        "show_ranking": quiz.show_ranking,
    }), 200


@play_bp.route("/<token>/ranking", methods=["GET"])
def ranking(token):
    attempt, err = _get_attempt_or_404(token)
    if err:
        return err

    if attempt.status != "finished":
        return error_response("Chưa làm xong bài nên chưa xem được bảng xếp hạng.", 409)

    quiz = attempt.quiz
    if not quiz.show_ranking:
        return jsonify({"ranking": []}), 200

    attempts = Attempt.query.filter_by(quiz_id=quiz.id).all()
    ranking_list = compute_ranking(attempts, me_token=attempt.device_id)

    return jsonify({"ranking": ranking_list}), 200


@play_bp.route("/<token>/event", methods=["POST"])
@limiter.limit("60/minute")
def event(token):
    attempt, err = _get_attempt_or_404(token)
    if err:
        return err

    data = request.get_json(silent=True) or {}
    if data.get("type") == "tab_hidden":
        attempt.tab_switch_count = (attempt.tab_switch_count or 0) + 1
        db.session.commit()

    return "", 204