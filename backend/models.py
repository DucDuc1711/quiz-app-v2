from datetime import datetime, timezone

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="teacher")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    quizzes = db.relationship("Quiz", backref="owner", lazy=True, cascade="all, delete-orphan")


class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(500), nullable=True)
    access_code = db.Column(db.String(6), unique=True, nullable=False, index=True)
    is_open = db.Column(db.Boolean, nullable=False, default=True)
    open_at = db.Column(db.DateTime, nullable=True)
    close_at = db.Column(db.DateTime, nullable=True)
    question_time = db.Column(db.Integer, nullable=False, default=30)
    shuffle_questions = db.Column(db.Boolean, nullable=False, default=False)
    shuffle_choices = db.Column(db.Boolean, nullable=False, default=False)
    show_ranking = db.Column(db.Boolean, nullable=False, default=True)
    allow_retake = db.Column(db.Boolean, nullable=False, default=False)
    is_public = db.Column(db.Boolean, nullable=False, default=True)
    source_quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    questions = db.relationship("Question", backref="quiz", lazy=True, cascade="all, delete-orphan")
    attempts = db.relationship("Attempt", backref="quiz", lazy=True, cascade="all, delete-orphan")


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    type = db.Column(db.String(20), nullable=False)  # 'single' | 'multiple' | 'true_false'
    content = db.Column(db.String(1000), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    order_num = db.Column(db.Integer, nullable=False, default=0)
    time_limit = db.Column(db.Integer, nullable=True)

    choices = db.relationship("Choice", backref="question", lazy=True, cascade="all, delete-orphan")
    answers = db.relationship("AttemptAnswer", backref="question", lazy=True, cascade="all, delete-orphan")


class Choice(db.Model):
    __tablename__ = "choices"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    content = db.Column(db.String(300), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    order_num = db.Column(db.Integer, nullable=False, default=0)


class Attempt(db.Model):
    __tablename__ = "attempts"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_name = db.Column(db.String(40), nullable=False)
    device_id = db.Column(db.String(100), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="in_progress")  # 'in_progress' | 'finished'
    phase = db.Column(db.String(20), nullable=False, default="question")  # 'question' | 'feedback'
    current_index = db.Column(db.Integer, nullable=False, default=0)
    question_started_at = db.Column(db.DateTime, nullable=True)
    feedback_started_at = db.Column(db.DateTime, nullable=True)
    question_order = db.Column(db.JSON, nullable=True)  # danh sách id câu
    choice_orders = db.Column(db.JSON, nullable=True)  # {question_id: [choice_id, ...]}
    total_questions = db.Column(db.Integer, nullable=False, default=0)
    correct_answers = db.Column(db.Integer, nullable=False, default=0)
    score = db.Column(db.Float, nullable=False, default=0.0)
    time_spent = db.Column(db.Float, nullable=False, default=0.0)
    tab_switch_count = db.Column(db.Integer, nullable=False, default=0)
    started_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    finished_at = db.Column(db.DateTime, nullable=True)

    answers = db.relationship("AttemptAnswer", backref="attempt", lazy=True, cascade="all, delete-orphan")


class AttemptAnswer(db.Model):
    __tablename__ = "attempt_answers"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_choice_ids = db.Column(db.JSON, nullable=True)  # rỗng nếu bỏ qua
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    timed_out = db.Column(db.Boolean, nullable=False, default=False)
    time_taken = db.Column(db.Float, nullable=False, default=0.0)

    __table_args__ = (
        db.UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),
    )