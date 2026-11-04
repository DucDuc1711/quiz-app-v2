import pytest
from extensions import db
from models import User, Quiz, Question, Choice, Attempt, AttemptAnswer


def test_user_unique_constraints(app):
    """Rang buoc unique cua username va email."""
    with app.app_context():
        u1 = User(username="user1", email="a@test.com", password_hash="hash", role="teacher")
        db.session.add(u1)
        db.session.commit()

        u2 = User(username="user1", email="b@test.com", password_hash="hash", role="teacher")
        db.session.add(u2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()


def test_quiz_cascade_delete(app):
    """Xoa Quiz thi xoa Question, Choice, Attempt, AttemptAnswer (cascade)."""
    with app.app_context():
        user = User(username="owner", email="o@test.com", password_hash="hash", role="teacher")
        db.session.add(user)
        db.session.flush()

        quiz = Quiz(owner_id=user.id, title="Test Quiz", access_code="ABC123")
        db.session.add(quiz)
        db.session.flush()

        q = Question(quiz_id=quiz.id, type="single", content="Cau hoi?", order_num=1)
        db.session.add(q)
        db.session.flush()

        c = Choice(question_id=q.id, content="Dap an", is_correct=True, order_num=1)
        db.session.add(c)
        db.session.commit()

        quiz_id = quiz.id
        db.session.delete(quiz)
        db.session.commit()

        assert db.session.get(Quiz, quiz_id) is None
        assert Question.query.filter_by(quiz_id=quiz_id).count() == 0
        assert Choice.query.filter_by(question_id=q.id).count() == 0