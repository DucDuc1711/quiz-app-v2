from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from sqlalchemy import func
from models import db, User


def normalize_username(value):
    """Chuan hoa ten dang nhap: cat khoang trang dau/cuoi va viet thuong. Khong chuan hoa mat khau."""
    return (value or "").strip().lower()


def normalize_email(value):
    """Chuan hoa email: cat khoang trang dau/cuoi va viet thuong."""
    return (value or "").strip().lower()


def normalize_login_value(value):
    """Chuan hoa gia tri tim kiem dang nhap (ten dang nhap hoac email): cat khoang trang dau/cuoi, viet thuong."""
    return (value or "").strip().lower()


def error_response(message, status_code):
    return jsonify({"error": message}), status_code


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Yêu cầu không hợp lệ."}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Chưa xác thực hoặc hết hạn quyền truy cập."}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Bạn không có quyền thực hiện thao tác này."}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Không tìm thấy tài nguyên yêu cầu."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Phương thức không được phép."}), 405

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "File quá lớn. Giới hạn là 5 MB."}), 413

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"error": "Quá nhiều yêu cầu. Vui lòng thử lại sau."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Lỗi hệ thống. Vui lòng thử lại sau."}), 500


def teacher_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = db.session.get(User, int(user_id))
        if user is None or not user.is_active:
            return jsonify({"error": "Tài khoản không hợp lệ hoặc đã bị khóa."}), 401
        if user.role != "teacher":
            return jsonify({"error": "Chỉ giáo viên mới được phép."}), 403
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = db.session.get(User, int(user_id))
        if user is None or not user.is_active:
            return jsonify({"error": "Tài khoản không hợp lệ hoặc đã bị khóa."}), 401
        if user.role != "admin":
            return jsonify({"error": "Chỉ admin mới được phép."}), 403
        return fn(*args, **kwargs)
    return wrapper
