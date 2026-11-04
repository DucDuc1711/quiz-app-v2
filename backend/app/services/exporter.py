from openpyxl import Workbook
import csv
import io


def sanitize_cell(value):
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return f"'{value}"
    return value


def export_results_to_xlsx(attempts):
    wb = Workbook()
    ws = wb.active
    ws.append(["Tên học sinh", "Điểm", "Số câu đúng", "Tổng câu", "Thời gian (s)", "Số lần rời tab", "Trạng thái", "Thời điểm nộp"])
    for a in attempts:
        submitted_at = a.finished_at.strftime("%Y-%m-%d %H:%M:%S") if getattr(a, "finished_at", None) else ""
        ws.append([
            sanitize_cell(a.student_name or ""),
            a.score if a.score is not None else 0,
            a.correct_answers if a.correct_answers is not None else 0,
            a.total_questions if a.total_questions is not None else 0,
            round(a.time_spent, 1) if a.time_spent is not None else 0,
            a.tab_switch_count if a.tab_switch_count is not None else 0,
            a.status or "",
            submitted_at
        ])
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def export_results_to_csv(attempts):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Tên học sinh", "Điểm", "Số câu đúng", "Tổng câu", "Thời gian (s)", "Số lần rời tab", "Trạng thái", "Thời điểm nộp"])
    for a in attempts:
        submitted_at = a.finished_at.strftime("%Y-%m-%d %H:%M:%S") if getattr(a, "finished_at", None) else ""
        writer.writerow([
            sanitize_cell(a.student_name or ""),
            a.score if a.score is not None else 0,
            a.correct_answers if a.correct_answers is not None else 0,
            a.total_questions if a.total_questions is not None else 0,
            round(a.time_spent, 1) if a.time_spent is not None else 0,
            a.tab_switch_count if a.tab_switch_count is not None else 0,
            a.status or "",
            submitted_at
        ])
    return output.getvalue()


