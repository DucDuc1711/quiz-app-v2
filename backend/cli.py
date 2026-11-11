import os

import click
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from extensions import db
from models import User, Quiz, Question, Choice
from app.services.codes import generate_unique_code


def register_cli(app):
    @app.cli.command("create-admin")
    @with_appcontext
    def create_admin():
        """Tạo tài khoản admin duy nhất từ biến môi trường."""
        username = current_app.config.get("ADMIN_USERNAME") or os.environ.get("ADMIN_USERNAME")
        email = current_app.config.get("ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL")
        password = current_app.config.get("ADMIN_PASSWORD") or os.environ.get("ADMIN_PASSWORD")

        if not username or not email or not password:
            click.echo("Thiếu ADMIN_USERNAME, ADMIN_EMAIL hoặc ADMIN_PASSWORD trong .env")
            return

        if len(password) < 8:
            click.echo("Mật khẩu admin phải ít nhất 8 ký tự.")
            return
        if password == "123456":
            click.echo("Mật khẩu admin không được bằng 123456.")
            return

        existing_admin = User.query.filter_by(role="admin").first()
        if existing_admin:
            click.echo(f"Hệ thống đã có admin: {username}. Không thêm nữa.")
            return

        if User.query.filter_by(username=username).first():
            click.echo(f"Username '{username}' đã tồn tại.")
            return
        if User.query.filter_by(email=email).first():
            click.echo(f"Email '{email}' đã tồn tại.")
            return

        admin = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role="admin",
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Đã tạo admin: {username} ({email})")

    @app.cli.command("seed-samples")
    @click.option("--reset", is_flag=True, default=False, help="Xóa các bộ đề mẫu của admin rồi seed lại.")
    @with_appcontext
    def seed_samples(reset):
        """Tạo 2 bộ đề mẫu cho admin, is_public=True, có mã tham gia."""
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            click.echo("Chưa có admin. Chạy flask create-admin trước.")
            return

        SAMPLE_TITLES = ["Lập trình Python cơ bản", "Kiến thức chung vui Việt"]

        if reset:
            # Xóa TẤT CẢ bộ đề mẫu do admin sở hữu (không chỉ 2 tiêu đề mẫu).
            # Khi xóa, đặt source_quiz_id = NULL cho các bản sao của giáo viên
            # để không vỡ khóa ngoại; bản sao của giáo viên giữ nguyên.
            samples = Quiz.query.filter_by(owner_id=admin.id).all()
            for q in samples:
                Quiz.query.filter(Quiz.source_quiz_id == q.id).update(
                    {Quiz.source_quiz_id: None}, synchronize_session=False
                )
                db.session.delete(q)
            db.session.commit()
            click.echo(f"Đã xóa {len(samples)} bộ đề mẫu cũ (bản sao của giáo viên giữ nguyên).")

        if Quiz.query.filter_by(title="Lập trình Python cơ bản").first() or \
           Quiz.query.filter_by(title="Kiến thức chung vui Việt").first():
            click.echo("Dữ liệu mẫu đã được seed trước đó. Chạy --reset để seed lại.")
            return

        def _create_quiz(title, description, questions_data):
            access_code = generate_unique_code()
            quiz = Quiz(
                owner_id=admin.id,
                title=title,
                description=description,
                tags="mẫu, học tập",
                access_code=access_code,
                is_open=True,
                question_time=30,
                is_public=True,
            )
            db.session.add(quiz)
            db.session.flush()

            for order_num, (qtype, content, choices_data) in enumerate(questions_data, start=1):
                question = Question(
                    quiz_id=quiz.id,
                    type=qtype,
                    content=content,
                    order_num=order_num,
                )
                db.session.add(question)
                db.session.flush()

                for choice_order, (choice_content, is_correct) in enumerate(choices_data, start=1):
                    choice = Choice(
                        question_id=question.id,
                        content=choice_content,
                        is_correct=is_correct,
                        order_num=choice_order,
                    )
                    db.session.add(choice)

        _create_quiz(
            "Lập trình Python cơ bản",
            "Bộ đề mẫu về lập trình Python cho người mới bắt đầu.",
            [
                ("single", "Cách khai báo biến trong Python là gì?",
                    [("Biến = giá trị", True), ("kiểu biến = giá trị", False), ("var biến = giá trị", False), ("let biến = giá trị", False)]),
                ("single", "Hàm len() trong Python dùng làm gì?",
                    [("Trả về độ dài chuỗi/danh sách", True), ("Phép nhân hai số", False), ("Sắp xếp danh sách", False), ("Xóa phần tử khỏi danh sách", False)]),
                ("multiple", "Cấu trúc dữ liệu nào sau đây là có thứ tự?",
                    [("Danh sách (list)", True), ("Bộ (tuple)", True), ("Tập hợp (set)", False), ("Từ điển (dict)", True)]),
                ("true_false", "Python là ngôn ngữ lập trình được dịch giai.", [("Đúng", True), ("Sai", False)]),
                ("single", "Từ khóa nào được dùng để định nghĩa hàm trong Python?",
                    [("def", True), ("function", False), ("fun", False), ("define", False)]),
                ("multiple", "Cách xử lý ngoại lệ trong Python là gì?",
                    [("try...except", True), ("if...else", False), ("try...catch", False), ("raise", True)]),
                ("true_false", "Chỉ số của danh sách trong Python bắt đầu từ 1.", [("Đúng", False), ("Sai", True)]),
                ("single", "Hàm nào được dùng để xuất dữ liệu ra màn hình trong Python?",
                    [("print()", True), ("input()", False), ("scan()", False), ("show()", False)]),
            ],
        )

        _create_quiz(
            "Kiến thức chung vui Việt",
            "Bộ đề kiểm tra kiến thức tổng hợp về Việt Nam.",
            [
                ("single", "Thành phố nào là thủ đô của Việt Nam?",
                    [("Hồ Chí Minh", False), ("Hà Nội", True), ("Đà Nẵng", False), ("Cần Thơ", False)]),
                ("single", "Con vật nào có chiều cao cao nhất thế giới?",
                    [("Tư tinh", False), ("Hươu cao cổ", True), ("Vo cuồng", False), ("Vo cuồng", False)]),
                ("multiple", "Quốc gia nào nằm ở châu Âu?",
                    [("Pháp", True), ("Đức", True), ("Trung Quốc", False), ("Nhật Bản", False)]),
                ("true_false", "Mặt trời là sao trong hệ mặt trời.", [("Đúng", True), ("Sai", False)]),
                ("single", "Khoa học nào khiam sát ca cuộc sống?",
                    [("Sinh học", True), ("Vật lý", False), ("Hóa học", False), ("Địa lý", False)]),
                ("multiple", "Cách bảo vệ môi trường là gì?",
                    [("Sử dụng túi nhựa", True), ("Tiết kiệm năng lượng", True), ("Bỏ rừng", False), ("Thải thải nhựa", False)]),
                ("true_false", "Nước biển có màu xanh lá cây.", [("Đúng", False), ("Sai", True)]),
                ("single", "Cách nào để chia hết cho 3?",
                    [("Tổng chữ số chia hết cho 3", True), ("Chữ số cuối là 0", False), ("Số chẵn", False), ("Số lẻ", False)]),
            ],
        )

        db.session.commit()
        click.echo("Đã seed 2 bộ đề mẫu cho admin.")