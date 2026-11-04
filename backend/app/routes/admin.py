from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from models import db, User, Quiz, Attempt

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.before_request
@jwt_required()
def check_admin():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"error": "Chỉ dành cho admin"}), 403

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

@admin_bp.route('/teachers/<int:user_id>', methods=['DELETE'])
def delete_teacher(user_id):
    if user_id == get_jwt_identity():
        return jsonify({"error": "Không thể xóa chính mình"}), 403
    user = User.query.get_or_404(user_id)
    mode = request.args.get('quizzes', 'delete')
    if mode == 'transfer':
        admin = User.query.filter_by(role='admin').first()
        for q in user.quizzes:
            q.owner_id = admin.id
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Đã xóa giáo viên"})

