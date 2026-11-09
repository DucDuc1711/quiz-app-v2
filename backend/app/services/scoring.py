from datetime import datetime, timezone


def check_answer(selected_ids, correct_ids):
    """Kiểm tra đáp án chính xác: tập chọn khớp hoàn toàn tập đúng (không chốt điểm một phần).

    selected_ids: danh sách id đã chọn (có thể rỗng nếu bỏ qua).
    correct_ids: danh sách id đáp án đúng của câu hỏi.
    Trả về True nếu hai tập giống nhau, nếu cả hai đều rỗng thì coi như bỏ qua (không dung).
    """
    if selected_ids is None:
        selected_ids = []
    if correct_ids is None:
        correct_ids = []
    return set(selected_ids) == set(correct_ids) and len(correct_ids) > 0


def compute_score(correct_count, total):
    """Tinh diem theo he 10: correct / total * 10, lam tron 2 chu so."""
    if total <= 0:
        return 0.0
    return round(correct_count / total * 10, 2)


def compute_time_spent(answers):
    """Tinh tong thoi gian lam bai (giay) tu danh sach AttemptAnswer."""
    return round(sum((a.time_taken or 0.0) for a in answers), 2)


def compute_ranking(attempts, me_token=None):
    """Tinh bang xep hang cho cac attempt da finished.

    Sap xep: score giam dan, time_spent tang dan, finished_at tang dan.
    Cung score va cung time_spent thi cung hang (1, 2, 2, 4).
    Tra ve list dict: {rank, name, score, correct_answers, time_spent, finished_at, is_me}.
    """
    finished = [a for a in attempts if a.status == "finished" and a.finished_at is not None]
    finished.sort(key=lambda a: (-a.score, a.time_spent, a.finished_at))

    ranking = []
    prev_score = None
    prev_time = None
    prev_rank = 0
    for idx, attempt in enumerate(finished, start=1):
        if attempt.score == prev_score and attempt.time_spent == prev_time:
            rank = prev_rank
        else:
            rank = idx
        ranking.append({
            "rank": rank,
            "name": attempt.student_name,
            "score": attempt.score,
            "correct_answers": attempt.correct_answers,
            "time_spent": attempt.time_spent,
            "finished_at": attempt.finished_at.isoformat() if attempt.finished_at else None,
            "is_me": attempt.token == me_token,
        })
        prev_score = attempt.score
        prev_time = attempt.time_spent
        prev_rank = rank
    return ranking