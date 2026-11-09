# -*- coding: utf-8 -*-
"""Script kiem tra tu dong cac goi API giao vien P5 su dung giao dien.
Chay tu thu muc backend bang: python scripts/verify_teacher.py
"""
import sys
import os
import io

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.config import TestingConfig
from extensions import db
from models import User, Quiz, Question, Choice, Attempt

failed_count = 0


def check(cond, msg, data=None):
    global failed_count
    if cond:
        print(f"  [PASS] {msg}")
    else:
        print(f"  [FAIL] {msg}")
        if data is not None:
            print(f"         DATA: {data}")
        failed_count += 1


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def get_teacher_token(client, username="teacher1", email="t1@example.com", password="Password123"):
    resp = client.post("/api/auth/register", json={
        "username": username, "email": email, "password": password
    })
    check(resp.status_code == 201, f"Dang ky giao vien {username}")
    return resp.get_json()["access_token"]


def create_quiz(client, token, title="De thi P5"):
    resp = client.post("/api/teacher/quizzes", json={
        "title": title, "description": "Mo ta", "question_time": 30, "is_public": True
    }, headers=auth_headers(token))
    check(resp.status_code == 201, "Tao bo de thanh cong")
    return resp.get_json()["quiz"]["id"]
def add_question(client, token, quiz_id, q_type, content, choices):
    resp = client.post(f"/api/teacher/quizzes/{quiz_id}/questions", json={
        "type": q_type, "content": content, "choices": choices
    }, headers=auth_headers(token))
    return resp


def run_verification():
    global failed_count
    app = create_app(TestingConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()

    print("--- 1. Dang ky & dang nhap giao vien ---")
    token = get_teacher_token(client)

    resp = client.post("/api/auth/login", json={
        "username_or_email": "teacher1", "password": "Password123"
    })
    check(resp.status_code == 200, "Dang nhap thanh cong, co access_token")
    token = resp.get_json()["access_token"]

    # Kiểm tra không phân biệt hoa thường (tên đăng nhập và email)
    resp = client.post("/api/auth/register", json={
        "username": "GiaoVien1", "email": "GiaoVien1@Gmail.com", "password": "GiaoVien1",
    })
    check(resp.status_code == 201, "Dang ky GiaoVien1 / GiaoVien1@Gmail.com")
    if resp.status_code == 201:
        u = resp.get_json()["user"]
        check(u["username"] == u["username"].lower(), "Username luu thanh chu thuong")
        check(u["email"] == u["email"].lower(), "Email luu thanh chu thuong")
        check(u["username"] == "giaovien1", "Username gia tri khong dau")
        check(u["email"] == "giaovien1@gmail.com", "Email gia tri khong dau")

    for login in ["giaovien1", "GIAOVIEN1", "GiaoVien1", "giaovien1@gmail.com", "GIAOVIEN1@GMAIL.COM"]:
        r = client.post("/api/auth/login", json={
            "username_or_email": login, "password": "GiaoVien1",
        })
        check(r.status_code == 200, f"Đăng nhập không phân biệt hoa thường: {login}")

    r = client.post("/api/auth/login", json={
        "username_or_email": "giaovien1", "password": "giavien1",
    })
    check(r.status_code == 401, "Mật khẩu sai hoa thường tra 401")
    check(r.get_json().get("error") == "Tài khoản hoặc mật khẩu không chính xác.",
          "Thông báo sai tài khoản có dấu")

    r = client.post("/api/auth/register", json={
        "username": "GIAOVIEN1", "email": "other@example.com", "password": "Password123",
    })
    check(r.status_code == 409, "Dang ky trung khac hoa thuong tra 409")
    check(r.get_json().get("error") == "Tên đăng nhập đã tồn tại.", "Thông báo trùng tên có dấu")


    resp = client.get("/api/auth/me", headers=auth_headers(token))
    check(resp.status_code == 200 and resp.get_json()["user"]["role"] == "teacher",
          "GET /api/auth/me tra vai tro teacher")

    print("--- 2. Tao bo de & danh sach bo de ---")
    quiz_id = create_quiz(client, token)

    resp = client.get("/api/teacher/quizzes", headers=auth_headers(token))
    data = resp.get_json()
    check(resp.status_code == 200 and len(data) == 1, "Danh sach bo de co 1 mon")
    q = data[0]
    for field in ["question_count", "attempt_count", "is_open", "is_public", "updated_at"]:
        check(field in q, f"Trung tu {field} trong danh sach bo de")

    print("--- 3. Them 3 loai cau hoi (single, multiple, true_false) ---")
    r_single = add_question(client, token, quiz_id, "single", "Thu do Viet Nam la gi?",
                            [{"content": "Ha Noi", "is_correct": True},
                             {"content": "TP.HCM", "is_correct": False}])
    check(r_single.status_code == 201, "Them cau single thanh cong")
    single_id = r_single.get_json()["id"]

    r_multi = add_question(client, token, quiz_id, "multiple", "Cau gi la mau?",
                           [{"content": "Do", "is_correct": True},
                            {"content": "Xanh", "is_correct": True},
                            {"content": "Tim", "is_correct": False}])
    check(r_multi.status_code == 201, "Them cau multiple thanh cong")

    r_tf = add_question(client, token, quiz_id, "true_false", "Tr\u1ef1c \u0111\u1ea5t xoay quanh m\u1eadt tr\u1eddi?",
                        [{"content": "\u0110\u00fang", "is_correct": True},
                         {"content": "Sai", "is_correct": False}])
    check(r_tf.status_code == 201, "Them cau true_false thanh cong")

    resp = client.get(f"/api/teacher/quizzes/{quiz_id}", headers=auth_headers(token))
    detail = resp.get_json()
    check(resp.status_code == 200 and len(detail["questions"]) == 3, "Chi tiet bo de co 3 cau hoi")

    print("--- 4. Tra ve 400 khi sai rang buoc ---")
    r_bad = add_question(client, token, quiz_id, "single", "X",
                         [{"content": "A", "is_correct": True}])
    check(r_bad.status_code == 400, "It hon 2 dap an tra 400", data=r_bad.get_json())

    r_bad2 = add_question(client, token, quiz_id, "single", "Y",
                          [{"content": "A", "is_correct": True},
                           {"content": "B", "is_correct": True}])
    check(r_bad2.status_code == 400, "Single 2 dap an dung tra 400", data=r_bad2.get_json())

    print("--- 5. Tai anh hop le qua /teacher/uploads ---")
    img_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    data = io.BytesIO(img_data)
    data.name = "test.png"
    resp = client.post("/api/teacher/uploads",
                       content_type="multipart/form-data",
                       data={"file": (data, "test.png")},
                       headers=auth_headers(token))
    check(resp.status_code == 201 and "url" in resp.get_json(), "Tai anh PNG hop le thanh cong",
          data=resp.get_json())
    print("--- 6. Tai file sample va nhap CSV co 1 dong loi ---")
    resp = client.get("/api/teacher/import-template", headers=auth_headers(token))
    check(resp.status_code == 200 and resp.headers.get("Content-Type", "").find("spreadsheet") >= 0,
          "Tai file sample xlsx thanh cong")

    csv_content = "Cau hoi,Loai (1 dap an / nhieu dap an / dung-sai),Dap an A,Dap an B,Dap an C,Dap an D,Dap an E,Dap an F,Dap an dung,Thoi gian (giay)\n"
    csv_content += "Cau hop le,1 dap an,A,B,,,,,A,30\n"
    csv_content += "Câu lỗi,loại không hợp lệ,A,B,,,,,X,30\n"
    resp = client.post(f"/api/teacher/quizzes/{quiz_id}/import",
                       content_type="multipart/form-data",
                       data={"file": (io.BytesIO(csv_content.encode("utf-8-sig")), "import.csv")},
                       headers=auth_headers(token))
    check(resp.status_code == 200, "Nhap CSV tra 200")
    result = resp.get_json()
    check(result.get("imported", 0) == 1, f"Nhap duoc 1 cau (actual={result.get('imported')})")
    check(len(result.get("errors", [])) == 1, f"Co 1 dong loi (actual={len(result.get('errors', []))})",
          data=result.get("errors"))

    print("--- 7. Co luot lam => them/sua/xoa cau tra 409 ---")
    with app.app_context():
        attempt = Attempt(quiz_id=quiz_id, token="attempt-token-p5", student_name="Hoc sinh",
                          device_id="dev1", status="finished", total_questions=3, correct_answers=2,
                          score=7.5, time_spent=60.0, tab_switch_count=1,
                          started_at=datetime.now(timezone.utc), finished_at=datetime.now(timezone.utc))
        db.session.add(attempt)
        db.session.commit()

    r_add = add_question(client, token, quiz_id, "single", "Cau moi?",
                         [{"content": "A", "is_correct": True}, {"content": "B", "is_correct": False}])
    check(r_add.status_code == 409, "Them cau khi co luot lam tra 409", data=r_add.get_json())

    r_del = client.delete(f"/api/teacher/questions/{single_id}", headers=auth_headers(token))
    check(r_del.status_code == 409, "Xoa cau khi co luot lam tra 409", data=r_del.get_json())

    r_put = client.put(f"/api/teacher/questions/{single_id}", json={"content": "Sua"},
                       headers=auth_headers(token))
    check(r_put.status_code == 409, "Sua cau khi co luot lam tra 409", data=r_put.get_json())

    print("--- 8. Xoa ket qua => mo khoa thao tac lai ---")
    resp = client.delete(f"/api/teacher/quizzes/{quiz_id}/attempts", headers=auth_headers(token))
    check(resp.status_code == 200 and resp.get_json().get("deleted") == 1,
          "Xoa tat ca ket qua thanh cong", data=resp.get_json())

    r_add2 = add_question(client, token, quiz_id, "single", "Cau sau khi xoa ket qua?",
                          [{"content": "A", "is_correct": True}, {"content": "B", "is_correct": False}])
    check(r_add2.status_code == 201, "Sau khi xoa ket qua, them cau lai duoc thanh cong")

    print("--- 9. Stats ---")
    resp = client.get(f"/api/teacher/quizzes/{quiz_id}/stats", headers=auth_headers(token))
    stats = resp.get_json()
    check(resp.status_code == 200 and "total_attempts" in stats and "average_score" in stats
          and "max_score" in stats and "min_score" in stats, "Stats co truong can thiet", data=stats)

    print("--- 10. Export xlsx & csv ---")
    resp = client.get(f"/api/teacher/quizzes/{quiz_id}/export?format=xlsx", headers=auth_headers(token))
    check(resp.status_code == 200 and "spreadsheet" in (resp.headers.get("Content-Type") or ""),
          "Xuat xlsx thanh cong")

    resp = client.get(f"/api/teacher/quizzes/{quiz_id}/export?format=csv", headers=auth_headers(token))
    check(resp.status_code == 200 and "T\u00ean" in resp.get_data(as_text=True), "Xuat csv thanh cong")

    print("--- 11. Library & clone ---")
    resp = client.get("/api/teacher/library", headers=auth_headers(token))
    check(resp.status_code == 200 and "quizzes" in resp.get_json(), "Library danh sach bo de",
          data=resp.get_json())

    # Tao giao vien thu hai va bo de cong khai cua ho
    token2 = get_teacher_token(client, username="teacher2", email="t2@example.com")
    quiz_pub = create_quiz(client, token2, title="Bo de cong khai")
    add_question(client, token2, quiz_pub, "single", "Cau ghep?",
                 [{"content": "A", "is_correct": True}, {"content": "B", "is_correct": False}])
    with app.app_context():
        q = db.session.get(Quiz, quiz_pub)
        q.is_public = True
        db.session.commit()

    # Giao vien dau tien xem chi tiet bo de cong khai cua giao vien hai
    resp = client.get(f"/api/teacher/library/{quiz_pub}", headers=auth_headers(token))
    check(resp.status_code == 200 and "is_correct" in resp.get_json()["questions"][0]["choices"][0],
          "Chi tiet library co is_correct trong dap an", data=resp.get_json())

    # Giao vien dau tien clone bo de cua giao vien hai
    resp = client.post(f"/api/teacher/library/{quiz_pub}/clone", headers=auth_headers(token))
    check(resp.status_code == 201 and "quiz" in resp.get_json() and "id" in resp.get_json()["quiz"],
          "Clone bo de thanh cong", data=resp.get_json())

    print(f"\nKET QUUA VERIFY TEACHER: {'THAT BAI (' + str(failed_count) + ' loi)' if failed_count > 0 else 'TOAN BO PASS!'}")
    if failed_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    run_verification()