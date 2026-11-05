from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import or_
from models import db, User, Quiz, Attempt
from utils import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.before_request
@admin_required
def before_admin_request():
    pass

@admin_bp.route('/stats', methods=['GET'])
def get_admin_stats():
    return jsonify({
        "total_users": User.query.count(),
        "total_quizzes": Quiz.query.count(),
        "total_attempts": Attempt.query.count()
    })

@admin_bp.route('/teachers', methods=['GET'])
def get_teachers():
    teachers = User.query.filter_by(role='teacher').all()
    return jsonify([{"id": t.id, "username": t.username, "is_active": t.is_active} for t in teachers])

@admin_bp.route('/teachers/<int:user_id>', methods=['PATCH'])
def patch_teacher(user_id):
    current_user_id = int(get_jwt_identity())
    if str(user_id) == str(current_user_id):
        return jsonify({"error": "Không thể thay đổi trạng thái chính mình"}), 403
    user = User.query.filter_by(role='teacher', id=user_id).first_or_404()
    data = request.get_json() or {}
    if 'is_active' in data:
        user.is_active = bool(data['is_active'])
    db.session.commit()
    return jsonify({"message": "Đã cập nhật trạng thái giáo viên", "is_active": user.is_active}), 200


@admin_bp.route('/teachers/<int:user_id>', methods=['DELETE'])
def delete_teacher(user_id):
    current_user_id = int(get_jwt_identity())
    if str(user_id) == str(current_user_id):
        return jsonify({"error": "Không thể xóa chính mình"}), 403
    user = User.query.filter_by(role='teacher', id=user_id).first_or_404()
    mode = request.args.get('quizzes', '').strip()
    if mode not in ('delete', 'transfer'):
        return jsonify({"error": "Tham số quizzes phải là 'delete' hoặc 'transfer'"}), 400
    if mode == 'transfer':
        admin = User.query.filter_by(role='admin').first()
        if admin:
            for q in user.quizzes:
                q.owner_id = admin.id
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Đã xóa giáo viên"}), 200
@admin_bp.route('/quizzes', methods=['GET'])
def get_admin_quizzes():
    search = request.args.get('search', '').strip()
    query = Quiz.query.join(User, Quiz.owner_id == User.id, isouter=True)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Quiz.title.ilike(like), User.username.ilike(like)))
    quizzes = query.all()
    result = []
    for q in quizzes:
        result.append({
            "id": q.id,
            "title": q.title,
            "owner": q.owner.username if q.owner else None,
            "owner_id": q.owner_id,
            "is_open": q.is_open,
            "is_public": q.is_public,
            "question_count": len(q.questions),
            "attempt_count": len(q.attempts),
        })
    return jsonify(result), 200


@admin_bp.route('/quizzes/<int:quiz_id>', methods=['PATCH'])
def patch_admin_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    data = request.get_json() or {}
    if 'is_open' in data:
        quiz.is_open = bool(data['is_open'])
    if 'is_public' in data:
        quiz.is_public = bool(data['is_public'])
    db.session.commit()
    return jsonify({"message": "Đã cập nhật bộ đề", "is_open": quiz.is_open, "is_public": quiz.is_public}), 200


@admin_bp.route('/quizzes/<int:quiz_id>', methods=['DELETE'])
def delete_admin_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    return jsonify({"message": "Đã xóa bộ đề"}), 200


@admin_bp.route('/attempts', methods=['GET'])
def get_admin_attempts():
    search = request.args.get('search', '').strip()
    quiz_id = request.args.get('quiz_id', '').strip()
    query = Attempt.query.join(Quiz, Attempt.quiz_id == Quiz.id, isouter=True)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Attempt.student_name.ilike(like), Quiz.title.ilike(like)))
    if quiz_id:
        try:
            query = query.filter(Attempt.quiz_id == int(quiz_id))
        except ValueError:
            return jsonify({"error": "quiz_id không hợp lệ"}), 400
    attempts = query.order_by(Attempt.started_at.desc()).all()
    result = []
    for a in attempts:
        result.append({
            "id": a.id,
            "student_name": a.student_name,
            "quiz": a.quiz.title if a.quiz else None,
            "quiz_id": a.quiz_id,
            "score": a.score,
            "status": a.status,
            "started_at": a.started_at.isoformat() if a.started_at else None,
            "finished_at": a.finished_at.isoformat() if a.finished_at else None,
        })
    return jsonify(result), 200


@admin_bp.route('/attempts/<int:attempt_id>', methods=['DELETE'])
def delete_admin_attempt(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    db.session.delete(attempt)
    db.session.commit()
    return jsonify({"message": "Đã xóa kết quả làm bài"}), 200


@admin_bp.route('/attempts/bulk-delete', methods=['POST'])
def bulk_delete_attempts():
    data = request.get_json() or {}
    ids = data.get('ids', [])
    if not isinstance(ids, list) or len(ids) == 0:
        return jsonify({"error": "ids phải là danh sách không rỗng"}), 400
    Attempt.query.filter(Attempt.id.in_(ids)).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({"message": f"Đã xóa {len(ids)} kết quả làm bài"}), 200


