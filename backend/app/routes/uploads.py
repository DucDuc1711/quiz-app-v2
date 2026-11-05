import os
import secrets
from flask import Blueprint, jsonify, request, send_from_directory, current_app
from werkzeug.utils import secure_filename

from extensions import db
from utils import teacher_required, error_response

uploads_bp = Blueprint("uploads", __name__)

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
ALLOWED_MAGIC = {
    b"\x89PNG\r\n\x1a\n": ".png",
    b"\xff\xd8\xff": ".jpg",
    b"GIF87a": ".gif",
    b"GIF89a": ".gif",
    b"RIFF": ".webp",
}
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")


def _detect_ext(data):
    for magic, ext in ALLOWED_MAGIC.items():
        if data.startswith(magic):
            if ext == ".webp" and b"WEBP" not in data[8:12]:
                continue
            return ext
    return None


@uploads_bp.route("/teacher/uploads", methods=["POST"])
@teacher_required
def upload_file():
    if "file" not in request.files:
        return error_response("Khong co file duoc tai len.", 400)

    file = request.files["file"]
    if file.filename == "":
        return error_response("Khong chon file.", 400)

    data = file.read()
    if len(data) > MAX_FILE_SIZE:
        return error_response("File qua lon. Gioi han la 2 MB.", 413)

    ext = _detect_ext(data)
    if ext is None:
        return error_response("Chi nhan anh png, jpg, webp, gif (kiem tra dang file).", 400)
    if ext == ".svg" or file.filename.lower().endswith(".svg"):
        return error_response("Khong chap nhan file svg.", 400)

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = secrets.token_hex(16) + ext
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(file_path, "wb") as f:
        f.write(data)

    url = f"/api/uploads/{filename}"
    return jsonify({"message": "Tai len thanh cong.", "url": url}), 201


@uploads_bp.route("/uploads/<filename>", methods=["GET"])
def get_uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)