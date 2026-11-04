from flask import Blueprint, request, jsonify, send_file, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Quiz, Question
from app.services.exporter import export_results_to_xlsx, export_results_to_csv
from utils import teacher_required
import secrets

teacher_bp = Blueprint('teacher', __name__, url_prefix='/api/teacher')

@teacher_bp.before_request
@teacher_required
def before_teacher_request():
    pass

@teacher_bp.route('/quizzes', methods=['POST'])
def create_quiz():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    if not (5 <= data.get('question_time', 30) <= 600):
        return jsonify({"error": "Thời gian câu hỏi từ 5-600 giây"}), 400
    access_code = secrets.token_urlsafe(4)[:6].upper()
    new_quiz = Quiz(
        owner_id=current_user_id,
        title=data.get('title'),
        description=data.get('description'),
        access_code=access_code,
        question_time=data.get('question_time', 30),
        is_public=data.get('is_public', True)
    )
    db.session.add(new_quiz)
    db.session.commit()
    return jsonify({"message": "Tạo bộ đề thành công", "quiz": {"id": new_quiz.id, "access_code": access_code}}), 201

@teacher_bp.route('/quizzes', methods=['GET'])
def get_quizzes():
    current_user_id = int(get_jwt_identity())
    quizzes = Quiz.query.filter_by(owner_id=current_user_id).all()
    return jsonify([{"id": q.id, "title": q.title, "access_code": q.access_code} for q in quizzes])

@teacher_bp.route('/quizzes/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    return jsonify({"id": quiz.id, "title": quiz.title, "access_code": quiz.access_code})

@teacher_bp.route('/quizzes/<int:quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    db.session.delete(quiz)
    db.session.commit()
    return jsonify({"message": "Đã xóa bộ đề"})

@teacher_bp.route('/quizzes/<int:quiz_id>/questions', methods=['POST'])
def add_question(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    if quiz.attempts:
        return jsonify({"error": "Không thể thêm câu hỏi khi đã có lượt làm bài"}), 409
    data = request.get_json() or {}
    new_q = Question(
        quiz_id=quiz_id,
        type=data.get('type'),
        content=data.get('content'),
        image_url=data.get('image_url'),
        time_limit=data.get('time_limit')
    )
    db.session.add(new_q)
    db.session.commit()
    return jsonify({"message": "Thêm câu hỏi thành công", "id": new_q.id}), 201

@teacher_bp.route('/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    current_user_id = int(get_jwt_identity())
    q = Question.query.join(Quiz).filter(Question.id == question_id, Quiz.owner_id == current_user_id).first_or_404()
    if q.quiz.attempts:
        return jsonify({"error": "Không thể xóa câu hỏi khi đã có lượt làm bài"}), 409
    db.session.delete(q)
    db.session.commit()
    return jsonify({"message": "Đã xóa câu hỏi"})

@teacher_bp.route('/quizzes/<int:quiz_id>/results', methods=['GET'])
def get_results(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    return jsonify([{"id": a.id, "student_name": a.student_name, "score": a.score, "status": a.status} for a in quiz.attempts])

@teacher_bp.route('/quizzes/<int:quiz_id>/stats', methods=['GET'])
def get_stats(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    total = len(quiz.attempts)
    avg_score = sum(a.score for a in quiz.attempts) / total if total > 0 else 0
    return jsonify({"total_attempts": total, "average_score": avg_score})

@teacher_bp.route('/quizzes/<int:quiz_id>/export', methods=['GET'])
def export_results(quiz_id):
    current_user_id = int(get_jwt_identity())
    quiz = Quiz.query.filter_by(id=quiz_id, owner_id=current_user_id).first_or_404()
    fmt = request.args.get('format', 'xlsx')
    if fmt == 'xlsx':
        output = export_results_to_xlsx(quiz.attempts)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name=f'results_{quiz_id}.xlsx')
    else:
        csv_data = export_results_to_csv(quiz.attempts)
        return Response(csv_data, mimetype='text/csv', headers={"Content-Disposition": f"attachment;filename=results_{quiz_id}.csv"})

@teacher_bp.route('/library', methods=['GET'])
def get_library():
    quizzes = Quiz.query.filter_by(is_public=True).all()
    return jsonify([{"id": q.id, "title": q.title, "owner": q.owner.username} for q in quizzes])



