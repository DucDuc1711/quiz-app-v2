from flask import Blueprint, request, jsonify, send_file, Response, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from models import db, Quiz, Question, Choice, Attempt, AttemptAnswer
from app.services.exporter import export_results_to_xlsx, export_results_to_csv
from app.services.importer import generate_import_template, parse_import_file, process_imported_questions
from utils import teacher_required
import secrets
def _validate_question_data(data):
    errors = []
    q_type = data.get("type")
    content = data.get("content", "")
    choices = data.get("choices", [])

    if q_type not in ["single", "multiple", "true_false"]:
        errors.append("Loại câu hỏi phải là single, multiple hoặc true_false.")
    
    if not (1 <= len(str(content)) <= 1000):
        errors.append("Nội dung câu hỏi từ 1-1000 ký tự.")

    if not (2 <= len(choices) <= 6):
        errors.append("Số lượng đáp án phải từ 2-6.")
    
    for c in choices:
        c_content = c.get("content", "")
        if not (1 <= len(str(c_content)) <= 300):
            errors.append("Nội dung đáp án từ 1-300 ký tự.")
            break

    correct_choices = [c for c in choices if c.get("is_correct")]
    if q_type == "true_false":
        if len(choices) != 2:
            errors.append("Câu đúng/sai phải có đúng 2 đáp án.")
        elif {c.get("content") for c in choices} != {"Đúng", "Sai"}:
            errors.append("Đáp án câu đúng/sai phải là 'Đúng' và 'Sai'.")
        elif len(correct_choices) != 1:
            errors.append("Câu đúng/sai phải có đúng 1 đáp án đúng.")
    elif q_type == "single":
        if len(correct_choices) != 1:
            errors.append("Câu hỏi một đáp án phải có đúng 1 đáp án đúng.")
    elif q_type == "multiple":
        if len(correct_choices) < 1:
            errors.append("Câu hỏi nhiều đáp án phải có ít nhất 1 đáp án đúng.")

    return errors


teacher_bp = Blueprint('teacher', __name__, url_prefix='/api/teacher')

_ACCESS_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def _make_access_code():
    while True:
        code = "".join(secrets.choice(_ACCESS_CODE_ALPHABET) for _ in range(6))
        if not Quiz.query.filter_by(access_code=code).first():
            return code

@teacher_bp.before_request
@teacher_required
def before_teacher_request():
    pass

@teacher_bp.route('/quizzes', methods=['POST'])
def create_quiz():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    if not (5 <= data.get('question_time', 30) <= 600):
        return jsonify({"error": "Thời gian câu hỏi từ 5-600 giây"}), 400
    access_code=_make_access_code()
    new_quiz = Quiz(
        owner_id=current_user_id,
        title=data.get('title'),
        description=data.get('description'),
        access_code=access_code,
        question_time=data.get('question_time', 30),
        is_public=data.get('is_public', True),
        tags=data.get('tags'),
    )
    db.session.add(new_quiz)
    db.session.commit()
    return jsonify({"message": "Tạo bộ đề thành công", "quiz": {"id": new_quiz.id, "access_code": access_code}}), 201

@teacher_bp.route('/quizzes', methods=['GET'])
def get_quizzes():
    current_user_id = int(get_jwt_identity())
    quizzes = Quiz.query.filter_by(owner_id=current_user_id).all()
    return jsonify([
        {
            "id": q.id,
            "title": q.title,
            "access_code": q.access_code,
            "question_count": len(q.questions),
            "attempt_count": len(q.attempts),
            "is_open": q.is_open,
            "is_public": q.is_public,
            "updated_at": q.updated_at.isoformat() if q.updated_at else None,
        }
        for q in quizzes
    ])

@teacher_bp.route('/quizzes/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    
    questions_data = []
    for q in sorted(quiz.questions, key=lambda x: x.order_num):
        choices_data = []
        for c in sorted(q.choices, key=lambda x: x.order_num):
            choices_data.append({
                "id": c.id,
                "content": c.content,
                "is_correct": c.is_correct,
                "order_num": c.order_num
            })
        questions_data.append({
            "id": q.id,
            "type": q.type,
            "content": q.content,
            "image_url": q.image_url,
            "order_num": q.order_num,
            "time_limit": q.time_limit,
            "choices": choices_data
        })

    return jsonify({
        "id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "tags": quiz.tags,
        "access_code": quiz.access_code,
        "is_open": quiz.is_open,
        "open_at": quiz.open_at.isoformat() if quiz.open_at else None,
        "close_at": quiz.close_at.isoformat() if quiz.close_at else None,
        "question_time": quiz.question_time,
        "shuffle_questions": quiz.shuffle_questions,
        "shuffle_choices": quiz.shuffle_choices,
        "show_ranking": quiz.show_ranking,
        "allow_retake": quiz.allow_retake,
        "is_public": quiz.is_public,
        "source_quiz_id": quiz.source_quiz_id,
        "created_at": quiz.created_at.isoformat() if quiz.created_at else None,
        "updated_at": quiz.updated_at.isoformat() if quiz.updated_at else None,
        "questions": questions_data
    }), 200


@teacher_bp.route('/quizzes/<int:quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    db.session.delete(quiz)
    db.session.commit()
    return jsonify({"message": "Đã xóa bộ đề"})

@teacher_bp.route('/quizzes/<int:quiz_id>', methods=['PUT'])
def update_quiz(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    data = request.get_json() or {}
    quiz.title = data.get('title', quiz.title)
    quiz.description = data.get('description', quiz.description)
    quiz.question_time = data.get('question_time', quiz.question_time)
    quiz.shuffle_questions = data.get('shuffle_questions', quiz.shuffle_questions)
    quiz.shuffle_choices = data.get('shuffle_choices', quiz.shuffle_choices)
    quiz.show_ranking = data.get('show_ranking', quiz.show_ranking)
    quiz.allow_retake = data.get('allow_retake', quiz.allow_retake)
    quiz.is_public = data.get('is_public', quiz.is_public)
    quiz.is_open = data.get('is_open', quiz.is_open)
    quiz.tags = data.get('tags', quiz.tags)

    open_at = data.get('open_at')
    close_at = data.get('close_at')
    if open_at is not None:
        quiz.open_at = _parse_iso(open_at) if open_at != '' else None
    if close_at is not None:
        quiz.close_at = _parse_iso(close_at) if close_at != '' else None
    if quiz.open_at and quiz.close_at and quiz.close_at <= quiz.open_at:
        return jsonify({"error": "Thời gian đóng phải sau thời gian mở."}), 400

    db.session.commit()
    return jsonify({"message": "Cập nhật bộ đề thành công", "quiz": {
        "id": quiz.id, "title": quiz.title, "description": quiz.description,
        "is_public": quiz.is_public, "is_open": quiz.is_open,
        "question_time": quiz.question_time, "open_at": quiz.open_at.isoformat() if quiz.open_at else None,
        "close_at": quiz.close_at.isoformat() if quiz.close_at else None,
    }}), 200


def _parse_iso(value):
    from datetime import datetime
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return value

@teacher_bp.route('/quizzes/<int:quiz_id>/publish', methods=['PATCH'])
def publish_quiz(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    data = request.get_json() or {}
    if 'is_public' in data:
        quiz.is_public = data.get('is_public')
    if 'is_open' in data:
        quiz.is_open = data.get('is_open')
    db.session.commit()
    return jsonify({"message": "Đã cập nhật trạng thái bộ đề", "is_public": quiz.is_public, "is_open": quiz.is_open}), 200

@teacher_bp.route('/quizzes/<int:quiz_id>/questions/order', methods=['PUT'])
def reorder_questions(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    if quiz.attempts:
        return jsonify({"error": "Không thể thay đổi thứ tự câu hỏi khi đã có lượt làm bài"}), 409
    data = request.get_json() or {}
    ids = data.get('ids', [])
    for i, q_id in enumerate(ids):
        q = Question.query.get(q_id)
        if q and q.quiz_id == quiz.id:
            q.order_num = i
    db.session.commit()
    return jsonify({"message": "Thay đổi thứ tự câu hỏi thành công"}), 200

@teacher_bp.route('/quizzes/<int:quiz_id>/questions', methods=['POST'])
def add_question(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    if quiz.attempts:
        return jsonify({"error": "Không thể thêm câu hỏi khi đã có lượt làm bài"}), 409
    data = request.get_json() or {}
    errors = _validate_question_data(data)
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400
        
    new_q = Question(
        quiz_id=quiz_id,
        type=data.get('type'),
        content=data.get('content'),
        image_url=data.get('image_url'),
        time_limit=data.get('time_limit')
    )
    db.session.add(new_q)
    db.session.commit()
    
    for c in data.get('choices', []):
        new_c = Choice(
            question_id=new_q.id,
            content=c.get('content'),
            is_correct=c.get('is_correct', False)
        )
        db.session.add(new_c)
    db.session.commit()
    
    return jsonify({"message": "Thêm câu hỏi thành công", "id": new_q.id}), 201

@teacher_bp.route('/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    current_user_id = int(get_jwt_identity())
    q = Question.query.join(Quiz).filter(Question.id == question_id, Quiz.owner_id == current_user_id).first_or_404()
    if q.quiz.attempts:
        return jsonify({"error": "Không thể xóa câu hỏi khi đã có lượt làm bài"}), 409
    db.session.delete(q)
    db.session.commit()
    return jsonify({"message": "Đã xóa câu hỏi"})

@teacher_bp.route('/questions/<int:question_id>', methods=['PUT'])
def update_question(question_id):
    current_user_id = int(get_jwt_identity())
    q = Question.query.join(Quiz).filter(Question.id == question_id, Quiz.owner_id == current_user_id).first_or_404()
    if q.quiz.attempts:
        return jsonify({"error": "Không thể sửa câu hỏi khi đã có lượt làm bài"}), 409
    data = request.get_json() or {}
    errors = _validate_question_data(data)
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    q.type = data.get('type')
    q.content = data.get('content')
    q.image_url = data.get('image_url')
    q.time_limit = data.get('time_limit')

    for c in q.choices:
        db.session.delete(c)

    for c in data.get('choices', []):
        new_c = Choice(
            question_id=q.id,
            content=c.get('content'),
            is_correct=c.get('is_correct', False)
        )
        db.session.add(new_c)

    db.session.commit()
    return jsonify({"message": "Cập nhật câu hỏi thành công", "id": q.id}), 200

@teacher_bp.route('/quizzes/<int:quiz_id>/attempts', methods=['GET'])
def get_attempts(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    attempts_data = []
    for a in quiz.attempts:
        attempts_data.append({
            "id": a.id,
            "student_name": a.student_name,
            "score": a.score,
            "correct_answers": a.correct_answers,
            "total_questions": a.total_questions,
            "time_spent": round(a.time_spent, 1) if a.time_spent is not None else 0,
            "tab_switch_count": a.tab_switch_count,
            "status": a.status,
            "started_at": a.started_at.isoformat() if a.started_at else None,
            "finished_at": a.finished_at.isoformat() if a.finished_at else None,
        })
    return jsonify(attempts_data), 200

@teacher_bp.route('/quizzes/<int:quiz_id>/stats', methods=['GET'])
def get_stats(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    total = len(quiz.attempts)
    avg_score = sum(a.score for a in quiz.attempts) / total if total > 0 else 0
    max_score = max((a.score for a in quiz.attempts), default=0)
    min_score = min((a.score for a in quiz.attempts), default=0)

    # Tỉ lệ sai từng câu
    question_stats = []
    for q in sorted(quiz.questions, key=lambda x: x.order_num):
        wrong = 0
        answered = 0
        for aa in q.answers:
            answered += 1
            if not aa.is_correct:
                wrong += 1
        question_stats.append({
            "id": q.id,
            "content": q.content,
            "wrong_count": wrong,
            "wrong_rate": round(wrong / answered, 2) if answered > 0 else 0,
            "wrong": wrong,
            "answered": answered,
        })

    return jsonify({
        "total_attempts": total,
        "average_score": round(avg_score, 2),
        "max_score": round(max_score, 2),
        "min_score": round(min_score, 2),
        "questions": question_stats,
    }), 200

@teacher_bp.route('/quizzes/<int:quiz_id>/export', methods=['GET'])
def export_results(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    fmt = request.args.get('format', 'xlsx')
    if fmt == 'xlsx':
        output = export_results_to_xlsx(quiz.attempts)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name=f'results_{quiz_id}.xlsx')
    else:
        csv_data = export_results_to_csv(quiz.attempts)
        return Response(csv_data, mimetype='text/csv', headers={"Content-Disposition": f"attachment;filename=results_{quiz_id}.csv"})

@teacher_bp.route('/library', methods=['GET'])
def get_library():
    current_user_id = int(get_jwt_identity())
    search = request.args.get('search', '').strip()
    tag = request.args.get('tag', '').strip()
    page = max(int(request.args.get('page', 1) or 1), 1)
    per_page = max(int(request.args.get('per_page', 12) or 12), 1)

    query = Quiz.query.filter_by(is_public=True)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Quiz.title.ilike(like), Quiz.description.ilike(like)))
    if tag:
        query = query.filter(Quiz.tags.ilike(f"%{tag}%"))

    total = query.count()
    quizzes = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "quizzes": [{
            "id": q.id,
            "title": q.title,
            "description": q.description,
            "owner": q.owner.username,
            "owner_id": q.owner_id,
            "is_public": q.is_public,
            "tags": q.tags,
            "source_quiz_id": q.source_quiz_id,
        } for q in quizzes],
        "page": page,
        "per_page": per_page,
        "total": total,
    }), 200

@teacher_bp.route('/library/<int:quiz_id>', methods=['GET'])
def get_library_quiz(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, is_public=True).filter(Quiz.owner_id != current_user_id).first_or_404()
    questions_data = []
    for q in sorted(quiz.questions, key=lambda x: x.order_num):
        choices_data = []
        for c in sorted(q.choices, key=lambda x: x.order_num):
            choices_data.append({
                "content": c.content,
                "is_correct": c.is_correct,
                "order_num": c.order_num,
            })
        questions_data.append({
            "type": q.type,
            "content": q.content,
            "image_url": q.image_url,
            "time_limit": q.time_limit,
            "order_num": q.order_num,
            "choices": choices_data,
        })
    return jsonify({
        "id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "owner": quiz.owner.username,
        "owner_id": quiz.owner_id,
        "tags": quiz.tags,
        "is_public": quiz.is_public,
        "questions": questions_data,
    }), 200


@teacher_bp.route('/library/<int:quiz_id>/clone', methods=['POST'])
def clone_quiz(quiz_id):
    current_user_id = int(get_jwt_identity())
    original = Quiz.query.filter_by(id=quiz_id, is_public=True).filter(Quiz.owner_id != current_user_id).first_or_404()

    new_quiz = Quiz(
        owner_id=current_user_id,
        title=f"{original.title} (Bản sao)",
        description=original.description,
        tags=original.tags,
        access_code=_make_access_code(),
        question_time=original.question_time,
        is_public=False,
        source_quiz_id=original.id,
    )
    db.session.add(new_quiz)
    db.session.commit()

    for q in sorted(original.questions, key=lambda x: x.order_num):
        new_q = Question(
            quiz_id=new_quiz.id,
            type=q.type,
            content=q.content,
            image_url=q.image_url,

            order_num=q.order_num,
            time_limit=q.time_limit,
        )
        db.session.add(new_q)
        db.session.commit()
        for c in sorted(q.choices, key=lambda x: x.order_num):
            new_c = Choice(
                question_id=new_q.id,
                content=c.content,
                is_correct=c.is_correct,
                order_num=c.order_num,
            )
            db.session.add(new_c)
    db.session.commit()

    return jsonify({
        "message": "Đã sao chép bộ đề thành công",
        "quiz": {
            "id": new_quiz.id,
            "title": new_quiz.title,
            "access_code": new_quiz.access_code,
            "is_public": new_quiz.is_public,
            "source_quiz_id": new_quiz.source_quiz_id,
        }
    }), 201

@teacher_bp.route('/import-template', methods=['GET'])
def import_template():
    output = generate_import_template()
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        download_name='import-template.xlsx',
        as_attachment=True,
    )


@teacher_bp.route('/quizzes/<int:quiz_id>/import', methods=['POST'])
def import_quiz(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    if quiz.attempts:
        return jsonify({"error": "Không thể nhập câu hỏi khi bộ đề đã có lượt làm bài"}), 409

    if 'file' not in request.files:
        return jsonify({"error": "Không có file được tải lên."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Không chọn file."}), 400

    try:
        rows = parse_import_file(file)
    except Exception as e:
        return jsonify({"error": f"Không đọc được file: {str(e)}"}), 400

    valid_questions, errors = process_imported_questions(rows)

    for q_data in valid_questions:
        new_q = Question(
            quiz_id=quiz_id,
            type=q_data['type'],
            content=q_data['content'],
            image_url=q_data.get('image_url'),

            time_limit=q_data.get('time_limit'),
        )
        db.session.add(new_q)
        db.session.commit()
        for c in q_data['choices']:
            new_c = Choice(
                question_id=new_q.id,
                content=c['content'],
                is_correct=c['is_correct'],
                order_num=c['order_num'],
            )
            db.session.add(new_c)
    db.session.commit()

    return jsonify({
        "message": "Nhập câu hỏi thành công",
        "imported": len(valid_questions),
        "errors": errors,
    }), 200

@teacher_bp.route('/attempts/<int:attempt_id>', methods=['DELETE'])
def delete_attempt(attempt_id):
    current_user_id = int(get_jwt_identity())
    attempt = Attempt.query.join(Quiz).filter(Attempt.id == attempt_id, Quiz.owner_id == current_user_id).first_or_404()
    db.session.delete(attempt)
    db.session.commit()
    return jsonify({"message": "Đã xóa kết quả làm bài"}), 200


@teacher_bp.route('/quizzes/<int:quiz_id>/attempts', methods=['DELETE'])
def delete_all_attempts(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    count = len(quiz.attempts)
    Attempt.query.filter_by(quiz_id=quiz_id).delete()
    db.session.commit()
    return jsonify({"deleted": count, "message": "Đã xóa toàn bộ kết quả làm bài của bộ đề"}), 200


@teacher_bp.route('/quizzes/<int:quiz_id>/regenerate-code', methods=['POST'])
def regenerate_code(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    new_code = _make_access_code()
    quiz.access_code = new_code
    db.session.commit()
    return jsonify({"message": "Đã sinh mã mới", "access_code": new_code}), 200


@teacher_bp.route('/quizzes/<int:quiz_id>/duplicate', methods=['POST'])
def duplicate_quiz(quiz_id):
    current_user_id = int(get_jwt_identity())
    original = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()

    new_quiz = Quiz(
        owner_id=current_user_id,
        title=f"{original.title} (Bản sao)",
        description=original.description,
        tags=original.tags,
        access_code=_make_access_code(),
        question_time=original.question_time,
        is_public=False,
        source_quiz_id=original.id,
    )
    db.session.add(new_quiz)
    db.session.commit()

    for q in sorted(original.questions, key=lambda x: x.order_num):
        new_q = Question(
            quiz_id=new_quiz.id,
            type=q.type,
            content=q.content,
            image_url=q.image_url,

            order_num=q.order_num,
            time_limit=q.time_limit,
        )
        db.session.add(new_q)
        db.session.commit()
        for c in sorted(q.choices, key=lambda x: x.order_num):
            new_c = Choice(
                question_id=new_q.id,
                content=c.content,
                is_correct=c.is_correct,
                order_num=c.order_num,
            )
            db.session.add(new_c)
    db.session.commit()

    return jsonify({
        "message": "Sao chép thành công",
        "quiz": {
            "id": new_quiz.id,
            "title": new_quiz.title,
            "description": new_quiz.description,
            "access_code": new_quiz.access_code,
            "is_public": new_quiz.is_public,
            "question_time": new_quiz.question_time,
            "source_quiz_id": new_quiz.source_quiz_id,
        }
    }), 201
