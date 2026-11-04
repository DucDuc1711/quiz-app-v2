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
        """Tao tai khoan admin duy nhat tu bien moi truong."""
        username = current_app.config.get("ADMIN_USERNAME") or os.environ.get("ADMIN_USERNAME")
        email = current_app.config.get("ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL")
        password = current_app.config.get("ADMIN_PASSWORD") or os.environ.get("ADMIN_PASSWORD")

        if not username or not email or not password:
            click.echo("Thieu ADMIN_USERNAME, ADMIN_EMAIL hoac ADMIN_PASSWORD trong .env")
            return

        if len(password) < 8:
            click.echo("Mat khau admin phai it thieu 8 ky tu.")
            return
        if password == "123456":
            click.echo("Mat khau admin khong duoc bang 123456.")
            return

        existing_admin = User.query.filter_by(role="admin").first()
        if existing_admin:
            click.echo(f"He thong da co admin: {existing_admin.username}. Khong them them.")
            return

        if User.query.filter_by(username=username).first():
            click.echo(f"Username '{username}' da ton tai.")
            return
        if User.query.filter_by(email=email).first():
            click.echo(f"Email '{email}' da ton tai.")
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
        click.echo(f"Da tao admin: {username} ({email})")

    @app.cli.command("seed-samples")
    @with_appcontext
    def seed_samples():
        """Tao 2 bo de mau chu admin, is_public=True, co ma tham gia."""
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            click.echo("Chua co admin. Chay flask create-admin truoc.")
            return

        if Quiz.query.filter_by(title="Lap trinh Python co ban").first():
            click.echo("Du lieu mau da duoc seed truoc do. Khong nhan nay.")
            return

        def _create_quiz(title, description, questions_data):
            access_code = generate_unique_code()
            quiz = Quiz(
                owner_id=admin.id,
                title=title,
                description=description,
                tags="mau, hoc tap",
                access_code=access_code,
                is_open=True,
                question_time=30,
                is_public=True,
            )
            db.session.add(quiz)
            db.session.flush()

            for order_num, (qtype, content, explanation, choices_data) in enumerate(questions_data, start=1):
                question = Question(
                    quiz_id=quiz.id,
                    type=qtype,
                    content=content,
                    explanation=explanation,
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
            "Lap trinh Python co ban",
            "Bo de kiem tra ki nang lap trinh Python co ban cho hoc sinh moi bat dau.",
            [
                ("single", "Cach khai bao bien trong Python la gi?", "Su dung ten bien, khong can khoi tao kieu.",
                 [("Bien = gia tri", True), ("kieu bien = gia tri", False), ("var bien = gia tri", False), ("let bien = gia tri", False)]),
                ("single", "Ham len() trong Python dung lam gi?", "Tra ve do dai cua doi tuong.",
                 [("Tra ve do dai chuoi/danh sach", True), ("Phep nhan hai so", False), ("Sap xep danh sach", False), ("Xoa phan tu khoi danh sach", False)]),
                ("multiple", "Cau truc du lieu nao sau day la co thu tu?", "Danh sach va bo luu giu thu tu phan tu.",
                 [("Danh sach (list)", True), ("Bo (tuple)", True), ("Tap hop (set)", False), ("Tu dien (dict)", True)]),
                ("true_false", "Python la ngon ngu lap trinh duoc dien giai.", "Python duoc dien giai boi trinh dien giai Python.",
                 [("Dung", True), ("Sai", False)]),
                ("single", "Tu khoa nao duoc dung de dinh dang ham trong Python?", "Su dung tu khoa def.",
                 [("def", True), ("function", False), ("fun", False), ("define", False)]),
                ("multiple", "Cach xu ly ngoai le trong Python la gi?", "Su dung try...except de bat va xu ly ngoai le.",
                 [("try...except", True), ("if...else", False), ("try...catch", False), ("raise", True)]),
                ("true_false", "Chi so cua danh sach trong Python bat dau tu 1.", "Chi so bat dau tu 0.",
                 [("Dung", False), ("Sai", True)]),
                ("single", "Ham nao duoc dung de xuat du lieu ra man hinh trong Python?", "Su dung print() de hien thi du lieu.",
                 [("print()", True), ("input()", False), ("scan()", False), ("show()", False)]),
            ],
        )

        _create_quiz(
            "Kien thuc chung vui ve",
            "Bo de trai tim voi cac cau hoi kien thuc chung, phu hop cho tro choi lop hoc.",
            [
                ("single", "Thanh pho nao la dau cua Viet Nam?", "Ha Noi la thanh pho dau cua Viet Nam.",
                 [("Ho Chi Minh", False), ("Ha Noi", True), ("Da Nang", False), ("Can Tho", False)]),
                ("single", "Con vat nao co thay da cao nhat the gioi?", "Hirassai la con dap voi thay da cao nhat.",
                 [("Tu tinh", False), ("Hirassai", True), ("Vo cuong", False), ("Vo cuong", False)]),
                ("multiple", "Quoc gia nao nam o chau Au?", "Phap va Duc nam o chau Au.",
                 [("Phap", True), ("Duc", True), ("Trung Quoc", False), ("Nhat Ban", False)]),
                ("true_false", "Mat troi la sao trong he mat troi.", "Mat troi la sao trung tam cua he mat troi.",
                 [("Dung", True), ("Sai", False)]),
                ("single", "Khoa hoc nao khiam sat ca cuoc song?", "Sinh hoc la mon hoc khiam sat ca cuoc song.",
                 [("Sinh hoc", True), ("Vat li", False), ("Hoa hoc", False), ("Dia ly", False)]),
                ("multiple", "Cach bao ve moi truong la gi?", "Tap thai va tiet kiem nang luong giup bao ve moi truong.",
                 [("Tap thai", True), ("Tiet kiem nang luong", True), ("Thai thai nhiua", False), ("Bo rung doc lap", False)]),
                ("true_false", "Nuoc kep co mau xanh la cay.", "Nuoc kep trong trang, khong co mau.",
                 [("Dung", False), ("Sai", True)]),
                ("single", "Cach nao de chia het cho 3?", "Tong cac chu so chia het cho 3.",
                 [("Tong chu so chia het cho 3", True), ("Chu so cuoi la 0", False), ("Lai so chan", False), ("Lai so le", False)]),
            ],
        )

        db.session.commit()
        click.echo("Da seed 2 bo de mau cho admin.")