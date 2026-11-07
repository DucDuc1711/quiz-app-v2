# -*- coding: utf-8 -*-
"""Script kiểm tra tự động toàn bộ luồng làm bài (verify_flow.py).
Chạy từ thư mục backend bằng: python scripts/verify_flow.py
"""
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.config import TestingConfig
from extensions import db
from models import User, Quiz, Question, Choice, Attempt, AttemptAnswer

failed_count = 0

def check(cond, msg, data=None):
    global failed_count
    if cond:
        print(f"  [PASS] {msg}")
    else:
        print(f"  [FAIL] {msg}")
        if data is not None: print(f"         DATA: {data}")
        failed_count += 1

def run_verification():
    global failed_count
    app = create_app(TestingConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()
        admin = User(username='admin', email='admin@test.com', password_hash='hash', role='admin', is_active=True)
        db.session.add(admin)
        db.session.flush()

        quiz = Quiz(
            owner_id=admin.id, title='Verify Flow', description='Test 3 types',
            access_code='VERIFY3', is_open=True, question_time=30,
            shuffle_questions=False, shuffle_choices=False,
            show_ranking=True, allow_retake=False, is_public=True
        )
        db.session.add(quiz)
        db.session.flush()

        q1 = Question(quiz_id=quiz.id, type='single', content='Cau 1?', order_num=1)
        db.session.add(q1); db.session.flush()
        db.session.add_all([
            Choice(question_id=q1.id, content='D1', is_correct=True, order_num=1),
            Choice(question_id=q1.id, content='S1', is_correct=False, order_num=2),
        ])

        q2 = Question(quiz_id=quiz.id, type='multiple', content='Cau 2?', order_num=2)
        db.session.add(q2); db.session.flush()
        db.session.add_all([
            Choice(question_id=q2.id, content='D2', is_correct=True, order_num=1),
            Choice(question_id=q2.id, content='S2', is_correct=False, order_num=2),
        ])

        q3 = Question(quiz_id=quiz.id, type='true_false', content='Cau 3?', order_num=3)
        db.session.add(q3); db.session.flush()
        db.session.add_all([
            Choice(question_id=q3.id, content='D3', is_correct=True, order_num=1),
            Choice(question_id=q3.id, content='S3', is_correct=False, order_num=2),
        ])
        db.session.commit()

        q1_id, q2_id, q3_id = q1.id, q2.id, q3.id
        c1_correct = [c.id for c in q1.choices if c.is_correct]
        q3_correct = [c.id for c in q3.choices if c.is_correct]

    print("--- 1. Kiểm tra lỗi đầu vào & mã lỗi có dấu ---")
    r = client.get('/api/play/lookup?code=WRONG')
    check(r.status_code == 404, "Lookup mã sai trả 404")
    check("Không tìm thấy bộ đề" in r.get_json().get("error", ""), "Thông báo 404 có dấu")

    r = client.post('/api/play/join', json={'code': 'VERIFY3', 'name': '', 'device_id': 'd1'})
    check(r.status_code == 400, "Join thiếu tên trả 400")
    check("không được để trống" in r.get_json().get("error", ""), "Thông báo thiếu tên có dấu")

    print("--- 2. Join và làm bài 3 câu ---")
    r = client.post('/api/play/join', json={'code': 'VERIFY3', 'name': 'Học Sinh', 'device_id': 'dev-flow'})
    check(r.status_code == 201, "Join thành công trả 201")
    token = r.get_json()['attempt_token']

    r = client.get(f'/api/play/{token}/state')
    check(r.status_code == 200 and r.get_json()['phase'] == 'question', "State câu 1 trả question")

    r = client.post(f'/api/play/{token}/answer', json={'question_id': q1_id, 'choice_ids': c1_correct})
    check(r.status_code == 200 and r.get_json()['feedback']['is_correct'] is True, "Answer câu 1 đúng")

    r1 = client.get(f'/api/play/{token}/state')
    r2 = client.get(f'/api/play/{token}/state')
    check(r1.get_json()['phase'] == 'feedback' and r1.get_json() == r2.get_json(), "State sau answer là feedback, gọi nhiều lần ổn định")

    r = client.post(f'/api/play/{token}/answer', json={'question_id': q1_id, 'choice_ids': c1_correct})
    check(r.status_code == 409, "Trả lời lại câu cũ trả 409")

    client.post(f'/api/play/{token}/next')
    r = client.post(f'/api/play/{token}/answer', json={'question_id': q2_id, 'choice_ids': []})
    check(r.status_code == 200 and r.get_json()['feedback']['is_correct'] is False, "Answer mảng rỗng tính là sai")

    client.post(f'/api/play/{token}/next')
    with app.app_context():
        att = Attempt.query.filter_by(token=token).first()
        att.question_started_at = datetime.now(timezone.utc) - timedelta(seconds=60)
        db.session.commit()

    r = client.post(f'/api/play/{token}/answer', json={'question_id': q3_id, 'choice_ids': q3_correct})
    check(r.status_code == 200 and r.get_json()['feedback']['timed_out'] is True and r.get_json()['feedback']['is_correct'] is True, "Answer quá hạn vẫn chấm lựa chọn đúng")

    r = client.post(f'/api/play/{token}/next')
    check(r.status_code == 200 and r.get_json().get('status') == 'finished', "Next cuối cùng hoàn thành bài")

    r = client.get(f'/api/play/{token}/state')
    check(r.status_code == 200 and r.get_json().get('status') == 'finished', "State sau khi xong trả finished")

    r = client.get(f'/api/play/{token}/result')
    check(r.status_code == 200 and r.get_json()['score'] > 0, "Xem kết quả thành công")

    print(f"\nKẾT QUẢ VERIFY FLOW: {'THẤT BẠI (' + str(failed_count) + ' lỗi)' if failed_count > 0 else 'TOÀN BỘ PASS!'}")
    if failed_count > 0: sys.exit(1)

if __name__ == '__main__':
    run_verification()
