import re
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import or_, func
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, limiter
from models import User
from utils import normalize_username, normalize_email, normalize_login_value

auth_bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.]{4,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_register(data):
    errors = []
    username = normalize_username(data.get("username"))
    email = normalize_email(data.get("email"))
    password = data.get("password") or ""

    if not username:
        errors.append("Tên đăng nhập bắt buộc.")
    elif not USERNAME_RE.match(username):
        errors.append("Tên đăng nhập chỉ gồm chữ, số, dấu gạch dưới và dấu chấm (4–30 ký tự).")

    if not email:
        errors.append("Email bắt buộc.")
    elif not EMAIL_RE.match(email):
        errors.append("Email không hợp lệ.")

    if not password:
        errors.append("Mật khẩu bắt buộc.")
    elif len(password) < 8:
        errors.append("Mật khẩu tối thiểu 8 ký tự.")

    return errors, username, email, password


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5/hour")
def register():
    data = request.get_json(silent=True) or {}
    errors, username, email, password = _validate_register(data)
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    if User.query.filter(func.lower(User.username) == username).first():
        return jsonify({"error": "Tên đăng nhập đã tồn tại."}), 409
    if User.query.filter(func.lower(User.email) == email).first():
        return jsonify({"error": "Email đã được sử dụng."}), 409

    # Luon role teacher, bo qua truong role gui len
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role="teacher",
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        "message": "Đăng ký thành công.",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    }), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10/minute")
def login():
    data = request.get_json(silent=True) or {}
    username_or_email = normalize_login_value(data.get("username_or_email"))
    password = data.get("password") or ""

    if not username_or_email or not password:
        return jsonify({"error": "Vui lòng nhập đầy đủ thông tin."}), 400

    user = User.query.filter(
        or_(
            func.lower(User.username) == username_or_email,
            func.lower(User.email) == username_or_email,
        )
    ).first()

    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Tài khoản hoặc mật khẩu không chính xác."}), 401

    if user.role == "admin":
        return jsonify({"error": "Đăng nhập qua /api/auth/admin/login cho tài khoản admin."}), 403

    if not user.is_active:
        return jsonify({"error": "Tài khoản đã bị khóa. Vui lòng liên hệ admin."}), 403

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        "message": "Đăng nhập thành công.",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    }), 200


@auth_bp.route("/admin/login", methods=["POST"])
@limiter.limit("10/minute")
def admin_login():
    data = request.get_json(silent=True) or {}
    username_or_email = normalize_login_value(data.get("username_or_email"))
    password = data.get("password") or ""

    if not username_or_email or not password:
        return jsonify({"error": "Vui lòng nhập đầy đủ thông tin."}), 400

    user = User.query.filter(
        or_(
            func.lower(User.username) == username_or_email,
            func.lower(User.email) == username_or_email,
        )
    ).first()

    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Tài khoản hoặc mật khẩu không chính xác."}), 401

    if user.role != "admin":
        return jsonify({"error": "Chỉ tài khoản admin mới được đăng nhập tại đây."}), 403

    if not user.is_active:
        return jsonify({"error": "Tài khoản admin đã bị khóa."}), 403

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        "message": "Đăng nhập admin thành công.",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user is None or not user.is_active:
        return jsonify({"error": "Tài khoản không tồn tại hoặc đã bị khóa."}), 401
    return jsonify({
        "message": "Lấy thông tin người dùng thành công.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        },
    }), 200