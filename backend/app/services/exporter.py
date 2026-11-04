from openpyxl import Workbook
from openpyxl.styles import Protection
import csv
import io

def sanitize_cell(value):
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return f"'{value}"
    return value

def export_results_to_xlsx(attempts):
    wb = Workbook()
    ws = wb.active
    ws.append(["Tên học sinh", "Điểm", "Số câu đúng", "Thời gian (s)", "Trạng thái"])
    for a in attempts:
        ws.append([
            sanitize_cell(a.student_name),
            a.score,
            a.correct_answers,
            a.time_spent,
            a.status
        ])
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

def export_results_to_csv(attempts):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Tên học sinh", "Điểm", "Số câu đúng", "Thời gian (s)", "Trạng thái"])
    for a in attempts:
        writer.writerow([
            sanitize_cell(a.student_name),
            a.score,
            a.correct_answers,
            a.time_spent,
            a.status
        ])
    return output.getvalue()

