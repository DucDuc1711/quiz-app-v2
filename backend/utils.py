from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models import User


def error_response(message, status_code):
    return jsonify({"error": message}), status_code


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Yeu cau khong hop le."}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Chua xac thuc hoac het han quyen truy cap."}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Ban khong co quyen thuc thao tac nay."}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Khong tim duat tai nguyen yeu cau."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Phuong thuc khong duoc phep."}), 405

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "File qua lon. Gioi han la 5 MB."}), 413

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"error": "Qua nhieu yeu cau. Vui long thu lai sau."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Loi he thong. Vui long thu lai sau."}), 500


def teacher_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if user is None or not user.is_active:
            return jsonify({"error": "Tai khoan khong hop le da bi khoa hoac xoa."}), 401
        if user.role not in ("teacher", "admin"):
            return jsonify({"error": "Chi giao vien hoac admin moi duoc phep."}), 403
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if user is None or not user.is_active:
            return jsonify({"error": "Tai khoan khong hop le da bi khoa hoac xoa."}), 401
        if user.role != "admin":
            return jsonify({"error": "Chi admin moi duoc phep."}), 403
        return fn(*args, **kwargs)
    return wrapper