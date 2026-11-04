import pytest
from extensions import db
from models import Quiz
from app.services.codes import generate_unique_code


def test_generate_unique_code_format(app):
    """Ma tham gia luon 6 ky tu, dung bang ky tu bo 0, O, 1, I, L."""
    with app.app_context():
        code = generate_unique_code()
        assert len(code) == 6
        allowed = set("23456789ABCDEFGHJKLMNPQRSTUVWXYZ")
        assert all(c in allowed for c in code)
        assert code == code.upper()


def test_generate_unique_code_no_duplicates(app):
    """Khong sinh ma trung lap."""
    with app.app_context():
        codes = set()
        for _ in range(100):
            code = generate_unique_code()
            assert code not in codes
            codes.add(code)