import secrets
import string

from models import Quiz, db

_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # bo 0, O, 1, I, L


def generate_unique_code(length=6, max_attempts=1000):
    for _ in range(max_attempts):
        code = "".join(secrets.choice(_ALPHABET) for _ in range(length))
        if not Quiz.query.filter_by(access_code=code).first():
            return code
    raise RuntimeError("Khong sinh duoc ma tham gia duy nhat sau nhieu lan thu.")