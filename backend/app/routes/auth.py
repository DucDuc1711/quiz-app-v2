import re
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, limiter
from models import User

auth_bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.]{4,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_register(data):
    errors = []
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not username:
        errors.append("Username bat buoc.")
    elif not USERNAME_RE.match(username):
        errors.append("Username 4-30 ky tu, chi chua chu, so, dau _ va dau cham.")

    if not email:
        errors.append("Email bat buoc.")
    elif not EMAIL_RE.match(email):
        errors.append("Email khong hop le.")

    if not password:
        errors.append("Mat khau bat buoc.")
    elif len(password) < 8:
        errors.append("Mat khau toi thieu 8 ky tu.")

    return errors, username, email, password


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5/hour")
def register():
    data = request.get_json(silent=True) or {}
    errors, username, email, password = _validate_register(data)
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username da ton tai."}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email da ton tai."}), 409

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
        "message": "Dang ky thanh cong.",
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
    username_or_email = (data.get("username_or_email") or "").strip()
    password = data.get("password") or ""

    if not username_or_email or not password:
        return jsonify({"error": "Vui long nhap day du thong tin."}), 400

    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email.lower())
    ).first()

    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Tai khoan hoac mat khau khong chinh xac."}), 401

    if user.role == "admin":
        return jsonify({"error": "Dang nhap qua /api/auth/admin/login cho tai khoan admin."}), 403

    if not user.is_active:
        return jsonify({"error": "Tai khoan da bi khoa. Vui long lien he admin."}), 403

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        "message": "Dang nhap thanh cong.",
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
    username_or_email = (data.get("username_or_email") or "").strip()
    password = data.get("password") or ""

    if not username_or_email or not password:
        return jsonify({"error": "Vui long nhap day du thong tin."}), 400

    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email.lower())
    ).first()

    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Tai khoan hoac mat khau khong chinh xac."}), 401

    if user.role != "admin":
        return jsonify({"error": "Chi tai khoan admin moi duoc dang nhap tai day."}), 403

    if not user.is_active:
        return jsonify({"error": "Tai khoan admin da bi khoa."}), 403

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        "message": "Dang nhap admin thanh cong.",
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
        return jsonify({"error": "Tai khoan khong ton tai da bi khoa."}), 401
    return jsonify({
        "message": "Lay thong tin nguoi dung thanh cong.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        },
    }), 200