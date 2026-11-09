import io
import re
import uuid
from datetime import datetime, timezone

from openpyxl import load_workbook
from extensions import db
from models import Attempt, AttemptAnswer, Question, Quiz

import pytest


def get_teacher_token(client, username="teacher1", email="teacher1@example.com", password="Password123"):
    resp = client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert resp.status_code == 201
    return resp.get_json()["access_token"]


def test_teacher_create_quiz(client):
    token = get_teacher_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/teacher/quizzes", json={
        "title": "De thi Toan",
        "description": "Kiem tra 1 tiet",
        "question_time": 30,
        "is_public": True
    }, headers=headers)

    assert resp.status_code == 201
    data = resp.get_json()
    assert "quiz" in data
    assert data["quiz"]["id"] is not None
    assert len(data["quiz"]["access_code"]) == 6


def test_teacher_get_quizzes_and_detail(client):
    token = get_teacher_token(client, username="teacher2", email="teacher2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post("/api/teacher/quizzes", json={
        "title": "De thi Ly",
        "description": "Kiem tra hoc ky"
    }, headers=headers)
    quiz_id = create_resp.get_json()["quiz"]["id"]

    resp = client.get("/api/teacher/quizzes", headers=headers)
    assert resp.status_code == 200
    quizzes = resp.get_json()
    assert len(quizzes) == 1
    assert quizzes[0]["id"] == quiz_id

    resp_detail = client.get(f"/api/teacher/quizzes/{quiz_id}", headers=headers)
    assert resp_detail.status_code == 200
    assert resp_detail.get_json()["id"] == quiz_id


def test_teacher_add_and_delete_question(client):
    token = get_teacher_token(client, username="teacher3", email="teacher3@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post("/api/teacher/quizzes", json={
        "title": "De thi Hoa"
    }, headers=headers)
    quiz_id = create_resp.get_json()["quiz"]["id"]

    q_resp = client.post(f"/api/teacher/quizzes/{quiz_id}/questions", json={
        "type": "single",
        "content": "Axiit la gi?",
        "time_limit": 30,
        "choices": [
            {"content": "A", "is_correct": True},
            {"content": "B", "is_correct": False}
        ]
    }, headers=headers)
    assert q_resp.status_code == 201
    q_id = q_resp.get_json()["id"]

    del_q_resp = client.delete(f"/api/teacher/questions/{q_id}", headers=headers)
    assert del_q_resp.status_code == 200
    
    # Verify deletion
    get_resp = client.get(f"/api/teacher/quizzes/{quiz_id}", headers=headers)
    assert get_resp.status_code == 200
    assert len(get_resp.get_json()["questions"]) == 0


def test_teacher_delete_quiz(client):
    token = get_teacher_token(client, username="teacher4", email="teacher4@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post("/api/teacher/quizzes", json={
        "title": "De thi Sinh"
    }, headers=headers)
    quiz_id = create_resp.get_json()["quiz"]["id"]

    del_resp = client.delete(f"/api/teacher/quizzes/{quiz_id}", headers=headers)
    assert del_resp.status_code == 200

    get_resp = client.get(f"/api/teacher/quizzes/{quiz_id}", headers=headers)
    assert get_resp.status_code == 404



def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _create_quiz(client, token, title="De thi test", **kwargs):
    payload = {"title": title}
    payload.update(kwargs)
    resp = client.post("/api/teacher/quizzes", json=payload, headers=_auth_headers(token))
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["quiz"]["id"]


def _add_question(client, token, quiz_id, content="Cau hoi test?", q_type="single"):
    choices = [{"content": "A", "is_correct": False}, {"content": "B", "is_correct": True}]
    resp = client.post(f"/api/teacher/quizzes/{quiz_id}/questions",
                       json={"type": q_type, "content": content, "choices": choices},
                       headers=_auth_headers(token))
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["id"]


def _add_attempts(app, quiz_id, attempts_data, question_ids=None):
    question_ids = question_ids or []
    with app.app_context():
        objs = []
        for data in attempts_data:
            token = f"att-{uuid.uuid4().hex[:12]}"
            is_finished = data.get("status", "finished") == "finished"
            a = Attempt(
                token=token, quiz_id=quiz_id, student_name=data["student_name"],
                device_id="dev-01", status=data.get("status", "finished"), phase="question",
                current_index=data["total"] if is_finished else 0, total_questions=data["total"],
                correct_answers=data["correct"], score=data["score"],
                time_spent=60.0, finished_at=datetime.now(timezone.utc) if is_finished else None,
            )
            db.session.add(a)
            db.session.flush()
            for qid in question_ids:
                is_correct = qid not in data.get("wrong_q_ids", set())
                db.session.add(AttemptAnswer(
                    attempt_id=a.id, question_id=qid,
                    selected_choice_ids=[], is_correct=is_correct,
                    timed_out=False, time_taken=10.0
                ))
            objs.append(a)
        db.session.commit()
        return [o.id for o in objs]


def test_teacher_update_quiz(client):
    token = get_teacher_token(client, username="upt1", email="upt1@example.com")
    quiz_id = _create_quiz(client, token, title="Cu de cu", description="Mo ta cu")
    resp = client.put(f"/api/teacher/quizzes/{quiz_id}", json={
        "title": "Cu de moi", "description": "Mo ta moi", "is_public": False
    }, headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Cập nhật bộ đề thành công"
    get_resp = client.get(f"/api/teacher/quizzes/{quiz_id}", headers=_auth_headers(token))
    gdata = get_resp.get_json()
    assert gdata["title"] == "Cu de moi"
    assert gdata["description"] == "Mo ta moi"
    assert gdata["is_public"] is False


def test_teacher_update_quiz_title_allowed_with_attempts(client, app):
    token = get_teacher_token(client, username="upt2", email="upt2@example.com")
    quiz_id = _create_quiz(client, token)
    _add_attempts(app, quiz_id, [{"student_name": "A", "score": 8.0, "correct": 4, "total": 5}])
    resp = client.put(f"/api/teacher/quizzes/{quiz_id}", json={"title": "Da sua sau khi co luot lam"},
                      headers=_auth_headers(token))
    assert resp.status_code == 200


def test_teacher_quiz_isolation_404(client):
    token_a = get_teacher_token(client, username="isoa", email="isoa@example.com")
    token_b = get_teacher_token(client, username="isob", email="isob@example.com")


def test_teacher_regenerate_code(client):
    token = get_teacher_token(client, username="rc01", email="rc1@example.com")
    quiz_id = _create_quiz(client, token)
    before = client.get(f"/api/teacher/quizzes/{quiz_id}", headers=_auth_headers(token)).get_json()["access_code"]
    resp = client.post(f"/api/teacher/quizzes/{quiz_id}/regenerate-code", headers=_auth_headers(token))
    assert resp.status_code == 200
    new_code = resp.get_json()["access_code"]
    assert new_code != before
    assert re.fullmatch(r"[2-9A-HJ-NP-Z]{6}", new_code) is not None, new_code
    client.post("/api/teacher/quizzes", json={"title": "Khac"}, headers=_auth_headers(token))
    all_codes = [q["access_code"] for q in client.get("/api/teacher/quizzes", headers=_auth_headers(token)).get_json()]
    assert all_codes.count(new_code) == 1


def test_teacher_duplicate(client):
    token = get_teacher_token(client, username="dup1", email="dup1@example.com")
    quiz_id = _create_quiz(client, token, title="Bo de goc")
    q_id = _add_question(client, token, quiz_id)
    client.put(f"/api/teacher/questions/{q_id}", json={
        "type": "single", "content": "Cau goc?", "image_url": "/api/uploads/img.png",
        "choices": [{"content": "A", "is_correct": False}, {"content": "B", "is_correct": True}]
    }, headers=_auth_headers(token))
    resp = client.post(f"/api/teacher/quizzes/{quiz_id}/duplicate", headers=_auth_headers(token))
    assert resp.status_code == 201, resp.get_json()
    data = resp.get_json()
    new_id = data["quiz"]["id"]
    old_code = client.get(f"/api/teacher/quizzes/{quiz_id}", headers=_auth_headers(token)).get_json()["access_code"]
    assert data["quiz"]["access_code"] != old_code
    assert data["quiz"]["is_public"] is False
    assert data["quiz"]["source_quiz_id"] == quiz_id
    detail = client.get(f"/api/teacher/quizzes/{new_id}", headers=_auth_headers(token)).get_json()
    assert len(detail["questions"]) == 1
    dq = detail["questions"][0]
    assert dq["content"] == "Cau goc?"
    assert dq["image_url"] == "/api/uploads/img.png"
    assert len(dq["choices"]) == 2
    assert any(c["is_correct"] for c in dq["choices"])


def test_teacher_publish(client):
    token = get_teacher_token(client, username="pub1", email="pub1@example.com")
    quiz_id = _create_quiz(client, token, is_public=True)
    resp = client.patch(f"/api/teacher/quizzes/{quiz_id}/publish", json={"is_public": False}, headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["is_public"] is False
    lib = client.get("/api/teacher/library", headers=_auth_headers(token)).get_json()
    ids = [q["id"] for q in lib["quizzes"]]
    assert quiz_id not in ids
    resp = client.patch(f"/api/teacher/quizzes/{quiz_id}/publish", json={"is_public": True}, headers=_auth_headers(token))
    assert resp.status_code == 200
    lib = client.get("/api/teacher/library", headers=_auth_headers(token)).get_json()
    ids = [q["id"] for q in lib["quizzes"]]
    assert quiz_id in ids


def test_teacher_questions_order(client):
    token = get_teacher_token(client, username="ord1", email="ord1@example.com")
    quiz_id = _create_quiz(client, token)
    q1 = _add_question(client, token, quiz_id, content="Cau 1")
    q2 = _add_question(client, token, quiz_id, content="Cau 2")
    q3 = _add_question(client, token, quiz_id, content="Cau 3")
    resp = client.put(f"/api/teacher/quizzes/{quiz_id}/questions/order",
                      json={"ids": [q3, q1, q2]}, headers=_auth_headers(token))
    assert resp.status_code == 200
    detail = client.get(f"/api/teacher/quizzes/{quiz_id}", headers=_auth_headers(token)).get_json()
    order = [q["content"] for q in detail["questions"]]
    assert order == ["Cau 3", "Cau 1", "Cau 2"]


def test_teacher_questions_order_409_when_attempts(client, app):
    token = get_teacher_token(client, username="ord2", email="ord2@example.com")
    quiz_id = _create_quiz(client, token)
    q_id = _add_question(client, token, quiz_id)
    _add_attempts(app, quiz_id, [{"student_name": "A", "score": 5.0, "correct": 1, "total": 1}], [q_id])
    resp = client.put(f"/api/teacher/quizzes/{quiz_id}/questions/order", json={"ids": [q_id]}, headers=_auth_headers(token))
    assert resp.status_code == 409
    del_resp = client.delete(f"/api/teacher/quizzes/{quiz_id}/attempts", headers=_auth_headers(token))
    assert del_resp.status_code == 200
    resp = client.put(f"/api/teacher/quizzes/{quiz_id}/questions/order", json={"ids": [q_id]}, headers=_auth_headers(token))
    assert resp.status_code == 200, resp.get_json()


def test_teacher_question_crud_409_when_attempts(client, app):
    token = get_teacher_token(client, username="q409", email="q409@example.com")
    headers = _auth_headers(token)
    quiz_id = _create_quiz(client, token)
    q_id = _add_question(client, token, quiz_id)
    _add_attempts(app, quiz_id, [{"student_name": "A", "score": 5.0, "correct": 1, "total": 1}], [q_id])

    # POST thêm câu hỏi -> 409
    resp = client.post(f"/api/teacher/quizzes/{quiz_id}/questions", json={
        "type": "single", "content": "Cau them?",
        "choices": [{"content": "A", "is_correct": True}, {"content": "B", "is_correct": False}]
    }, headers=headers)
    assert resp.status_code == 409, resp.get_json()

    # PUT sửa câu hỏi -> 409
    resp = client.put(f"/api/teacher/questions/{q_id}", json={
        "type": "single", "content": "Cau sua?",
        "choices": [{"content": "A", "is_correct": True}, {"content": "B", "is_correct": False}]
    }, headers=headers)
    assert resp.status_code == 409, resp.get_json()

    # DELETE xóa câu hỏi -> 409
    resp = client.delete(f"/api/teacher/questions/{q_id}", headers=headers)
    assert resp.status_code == 409, resp.get_json()

    # POST import -> 409 (kiểm tra attempts xác thực trước khi đọc file, không cần gửi file)
    resp = client.post(f"/api/teacher/quizzes/{quiz_id}/import", headers=headers)
    assert resp.status_code == 409, resp.get_json()

    # Van sua duoc tieu bo de va cai dat khac
    resp = client.put(f"/api/teacher/quizzes/{quiz_id}", json={"title": "De da cap nhat", "question_time": 60}, headers=headers)
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["quiz"]["title"] == "De da cap nhat"


def test_teacher_update_question(client):
    token = get_teacher_token(client, username="uptq", email="uptq@example.com")
    headers = _auth_headers(token)
    quiz_id = _create_quiz(client, token)
    q_id = _add_question(client, token, quiz_id, content="Cau goc?")

    # Sua thanh cong: doi noi dung, loai va cac dap an
    resp = client.put(f"/api/teacher/questions/{q_id}", json={
        "type": "multiple", "content": "Cau hoi da sua?",
        "choices": [
            {"content": "A", "is_correct": True},
            {"content": "B", "is_correct": True},
            {"content": "C", "is_correct": False}
        ]
    }, headers=headers)
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["message"] == "Cập nhật câu hỏi thành công"
    assert resp.get_json()["id"] == q_id

    detail = client.get(f"/api/teacher/quizzes/{quiz_id}", headers=headers).get_json()
    q = next(q for q in detail["questions"] if q["id"] == q_id)
    assert q["content"] == "Cau hoi da sua?"
    assert q["type"] == "multiple"
    assert len(q["choices"]) == 3
    assert sum(1 for c in q["choices"] if c["is_correct"]) == 2

    # Du lieu sai: single co 2 dap an dung -> 400
    resp = client.put(f"/api/teacher/questions/{q_id}", json={
        "type": "single", "content": "Cau sai?",
        "choices": [
            {"content": "A", "is_correct": True},
            {"content": "B", "is_correct": True}
        ]
    }, headers=headers)
    assert resp.status_code == 400, resp.get_json()


def _make_xlsx(rows):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def test_teacher_import_xlsx(client):
    token = get_teacher_token(client, username="imp1", email="imp1@example.com")
    quiz_id = _create_quiz(client, token)
    xlsx = _make_xlsx([
        ["Câu hỏi", "Loại (1 đáp án / nhiều đáp án / đúng-sai)", "Đáp án A", "Đáp án B", "Đáp án C", "Đáp án D", "Đáp án E", "Đáp án F", "Đáp án đúng", "Giải thích", "Thời gian (giây)"],
        ["", "1 đáp án", "A", "B", "", "", "", "", "A", "", 30],
        ["2+2 bằng mấy?", "1 đáp án", "3", "4", "", "", "", "", "A,C", "", 30],
        ["Thủ đô của Việt Nam là gì?", "1 đáp án", "Hà Nội", "TP.HCM", "Đà Nẵng", "", "", "", "A", "Nội dung giải thích", 30],
        ["Một cái gì đó?", "nhiều đáp án", "X", "Y", "", "", "", "", "A,B", "", 30],
    ])
    resp = client.post(f"/api/teacher/quizzes/{quiz_id}/import",
                       data={"file": (xlsx, "nhap.xlsx")}, headers=_auth_headers(token))
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()
    assert data["imported"] == 2
    assert any("dòng 2 –" in e for e in data["errors"]), data["errors"]
    assert any("dòng 3 –" in e for e in data["errors"]), data["errors"]
    detail = client.get(f"/api/teacher/quizzes/{quiz_id}", headers=_auth_headers(token)).get_json()
    assert len(detail["questions"]) == 2


def test_teacher_import_csv(client):
    token = get_teacher_token(client, username="imp2", email="imp2@example.com")
    quiz_id = _create_quiz(client, token)
    csv_content = ("Câu hỏi,Loại (1 đáp án / nhiều đáp án / đúng-sai),Đáp án A,Đáp án B,Đáp án C,Đáp án D,Đáp án E,Đáp án F,Đáp án đúng,Giải thích,Thời gian (giây)\n"
                   "Sao của Việt Nam là gì?,1 đáp án,Đà Nẵng,Hà Nội,TP.HCM,,,,A,,30\n"
                   ",\n")
    resp = client.post(f"/api/teacher/quizzes/{quiz_id}/import",
                       data={"file": (io.BytesIO(csv_content.encode("utf-8-sig")), "nhap.csv")},
                       headers=_auth_headers(token))
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()
    assert data["imported"] == 1
    assert data["errors"] == [], data["errors"]


def test_teacher_import_template(client):
    token = get_teacher_token(client, username="tpl1", email="tpl1@example.com")
    resp = client.get("/api/teacher/import-template", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert "spreadsheetml.sheet" in (resp.headers.get("Content-Type") or "")
    disp = resp.headers.get("Content-Disposition") or ""
    assert "attachment" in disp and "import-template.xlsx" in disp

    # Roundtrip: import chính file mẫu vừa tải về phải chạy được
    quiz_id = _create_quiz(client, token)
    resp2 = client.post(f"/api/teacher/quizzes/{quiz_id}/import",
                        data={"file": (io.BytesIO(resp.data), "import_template.xlsx")},
                        headers=_auth_headers(token))
    assert resp2.status_code == 200, resp2.get_json()
    data2 = resp2.get_json()
    assert data2["imported"] >= 1
    assert data2["errors"] == [], data2["errors"]

    # Không token → 401
    assert client.get("/api/teacher/import-template").status_code == 401


def test_teacher_library_public_search_tag_page(client):
    token_a = get_teacher_token(client, username="liba", email="liba@example.com")
    token_b = get_teacher_token(client, username="libb", email="libb@example.com")
    _create_quiz(client, token_a, title="Toan co ban", tags="toan, easy", is_public=True)
    _create_quiz(client, token_a, title="Toan nang cao", tags="toan, hard", is_public=True)
    _create_quiz(client, token_a, title="Van co ban", tags="van", is_public=False)
    _create_quiz(client, token_b, title="Anh van", tags="anh", is_public=True)

    lib = client.get("/api/teacher/library?search=Toan&tag=toan&page=1", headers=_auth_headers(token_a)).get_json()
    assert lib["total"] == 2
    titles = [q["title"] for q in lib["quizzes"]]
    assert "Toan co ban" in titles and "Toan nang cao" in titles

    lib2 = client.get("/api/teacher/library?page=1", headers=_auth_headers(token_a)).get_json()
    assert lib2["total"] == 3
    assert len(lib2["quizzes"]) == 3

    lib3 = client.get("/api/teacher/library?page=2", headers=_auth_headers(token_a)).get_json()
    assert lib3["quizzes"] == []
    assert lib3["total"] == 3


def test_teacher_library_detail(client):
    token_a = get_teacher_token(client, username="lib2a", email="lib2a@example.com")
    token_b = get_teacher_token(client, username="lib2b", email="lib2b@example.com")
    pub_id = _create_quiz(client, token_a, title="Cong khai", is_public=True)
    _add_question(client, token_a, pub_id)
    priv_id = _create_quiz(client, token_b, title="Ri mat", is_public=False)

    resp = client.get(f"/api/teacher/library/{pub_id}", headers=_auth_headers(token_b))
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()
    assert data["id"] == pub_id
    assert "is_correct" in data["questions"][0]["choices"][0]

    assert client.get(f"/api/teacher/library/{priv_id}", headers=_auth_headers(token_a)).status_code == 404


def test_teacher_library_clone(client):
    token_a = get_teacher_token(client, username="cl1a", email="cl1a@example.com")
    token_b = get_teacher_token(client, username="cl1b", email="cl1b@example.com")
    src_id = _create_quiz(client, token_a, title="Goc cong khai", is_public=True)
    q_id = _add_question(client, token_a, src_id, content="Cau goc")
    client.put(f"/api/teacher/questions/{q_id}", json={
        "type": "single", "content": "Cau goc cap nhat", "image_url": "/api/uploads/img.png",
        "choices": [{"content": "A", "is_correct": True}, {"content": "B", "is_correct": False}]
    }, headers=_auth_headers(token_a))
    resp = client.post(f"/api/teacher/library/{src_id}/clone", headers=_auth_headers(token_b))
    assert resp.status_code == 201, resp.get_json()
    data = resp.get_json()
    new_id = data["quiz"]["id"]
    assert data["quiz"]["is_public"] is False
    assert data["quiz"]["source_quiz_id"] == src_id
    new_code = data["quiz"]["access_code"]
    assert re.fullmatch(r"[2-9A-HJ-NP-Z]{6}", new_code) is not None, new_code
    detail = client.get(f"/api/teacher/quizzes/{new_id}", headers=_auth_headers(token_b)).get_json()
    assert detail["questions"][0]["content"] == "Cau goc cap nhat"
    assert detail["questions"][0]["image_url"] == "/api/uploads/img.png"
    assert len(detail["questions"][0]["choices"]) == 2

    priv = _create_quiz(client, token_a, title="Bi mat", is_public=False)
    assert client.post(f"/api/teacher/library/{priv}/clone", headers=_auth_headers(token_b)).status_code == 404
    quiz_id = _create_quiz(client, token_a)
    headers_b = _auth_headers(token_b)
    assert client.get(f"/api/teacher/quizzes/{quiz_id}", headers=headers_b).status_code == 404
    assert client.put(f"/api/teacher/quizzes/{quiz_id}", json={"title": "x"}, headers=headers_b).status_code == 404
    assert client.delete(f"/api/teacher/quizzes/{quiz_id}", headers=headers_b).status_code == 404
def test_teacher_quizzes_attempts(client, app):
    token = get_teacher_token(client, username="att1", email="att1@example.com")
    quiz_id = _create_quiz(client, token)
    _add_attempts(app, quiz_id, [
        {"student_name": "Hoc sinh A", "score": 8.0, "correct": 4, "total": 5},
        {"student_name": "Hoc sinh B", "score": 6.0, "correct": 3, "total": 5},
    ], [])
    resp = client.get(f"/api/teacher/quizzes/{quiz_id}/attempts", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 2
    names = [a["student_name"] for a in data]
    assert "Hoc sinh A" in names and "Hoc sinh B" in names


def test_teacher_stats_ti_le_sai(client, app):
    token = get_teacher_token(client, username="st01", email="st1@example.com")
    quiz_id = _create_quiz(client, token)
    q1 = _add_question(client, token, quiz_id, content="Cau 1")
    q2 = _add_question(client, token, quiz_id, content="Cau 2")
    _add_attempts(app, quiz_id, [
        {"student_name": "A", "score": 10.0, "correct": 2, "total": 2},
        {"student_name": "B", "score": 5.0, "correct": 1, "total": 2, "wrong_q_ids": {q2}},
    ], [q1, q2])
    resp = client.get(f"/api/teacher/quizzes/{quiz_id}/stats", headers=_auth_headers(token))
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()
    assert data["total_attempts"] == 2
    assert abs(data["average_score"] - 7.5) < 1e-9
    qmap = {q["id"]: q for q in data["questions"]}
    assert qmap[q1]["wrong_count"] == 0
    assert qmap[q1]["wrong_rate"] == 0.0
    assert qmap[q2]["wrong_count"] == 1
    assert qmap[q2]["wrong_rate"] == 0.5


def test_teacher_export_xlsx_and_csv(client, app):
    token = get_teacher_token(client, username="ex01", email="ex1@example.com")
    quiz_id = _create_quiz(client, token)
    _add_attempts(app, quiz_id, [
        {"student_name": "=1+1", "score": 9.0, "correct": 4, "total": 5},
        {"student_name": "Nguyen Van A", "score": 7.0, "correct": 3, "total": 5},
        {"student_name": "Dang lam B", "score": 0.0, "correct": 0, "total": 5, "status": "in_progress"},
    ], [])

    header = ["Tên", "Điểm", "Số câu đúng", "Tổng câu", "Thời gian", "Số lần rời tab", "Trạng thái", "Thời điểm nộp"]

    resp = client.get(f"/api/teacher/quizzes/{quiz_id}/export?format=xlsx", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert "spreadsheetml.sheet" in (resp.headers.get("Content-Type") or "")
    wb = load_workbook(io.BytesIO(resp.data))
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    assert list(rows[0]) == header
    assert rows[1][0] == "'=1+1"
    assert rows[1][1] == 9.0
    assert rows[1][6] == "Đã nộp"
    assert rows[2][6] == "Đã nộp"
    assert rows[3][0] == "Dang lam B"
    assert rows[3][6] == "Đang làm"
    assert not rows[3][7]

    resp = client.get(f"/api/teacher/quizzes/{quiz_id}/export?format=csv", headers=_auth_headers(token))
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    lines = text.strip().splitlines()
    assert lines[0] == ",".join(header)
    assert any(line.startswith("'=1+1,") for line in lines)
    assert any("Dang lam B" in line and "Đang làm" in line for line in lines)
    assert any("Nguyen Van A" in line and "Đã nộp" in line for line in lines)


def test_teacher_delete_one_attempt(client, app):
    token = get_teacher_token(client, username="da01", email="da1@example.com")
    quiz_id = _create_quiz(client, token)
    objs = _add_attempts(app, quiz_id, [
        {"student_name": "A", "score": 5.0, "correct": 1, "total": 1},
        {"student_name": "B", "score": 10.0, "correct": 1, "total": 1},
    ], [])
    aid_a = objs[0]
    resp = client.delete(f"/api/teacher/attempts/{aid_a}", headers=_auth_headers(token))
    assert resp.status_code == 200
    get_resp = client.get(f"/api/teacher/quizzes/{quiz_id}/attempts", headers=_auth_headers(token))
    assert len(get_resp.get_json()) == 1
    assert get_resp.get_json()[0]["student_name"] == "B"
    token_b = get_teacher_token(client, username="da02", email="da2@example.com")
    assert client.delete(f"/api/teacher/attempts/{aid_a}", headers=_auth_headers(token_b)).status_code == 404


def test_teacher_delete_all_attempts(client, app):
    token = get_teacher_token(client, username="dal1", email="dal1@example.com")
    quiz_id = _create_quiz(client, token)
    _add_attempts(app, quiz_id, [
        {"student_name": "A", "score": 5.0, "correct": 1, "total": 1},
        {"student_name": "B", "score": 6.0, "correct": 1, "total": 1},
    ], [])
    resp = client.delete(f"/api/teacher/quizzes/{quiz_id}/attempts", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["deleted"] == 2
    get_resp = client.get(f"/api/teacher/quizzes/{quiz_id}/attempts", headers=_auth_headers(token))
    assert len(get_resp.get_json()) == 0
    q_id = _add_question(client, token, quiz_id)
    resp2 = client.put(f"/api/teacher/quizzes/{quiz_id}/questions/order", json={"ids": [q_id]}, headers=_auth_headers(token))
    assert resp2.status_code == 200