import io
import csv
import re
import unicodedata
from openpyxl import Workbook, load_workbook


def strip_accents(text):
    if not text:
        return ""
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower().strip()


def generate_import_template():
    wb = Workbook()
    ws = wb.active
    ws.title = "Template"
    headers = [
        "Câu hỏi", "Loại (1 đáp án / nhiều đáp án / đúng-sai)",
        "Đáp án A", "Đáp án B", "Đáp án C", "Đáp án D", "Đáp án E", "Đáp án F",
        "Đáp án đúng", "Thời gian (giây)"
    ]
    ws.append(headers)
    ws.append([
        "Thủ đô của Việt Nam là gì?", "1 đáp án",
        "Hà Nội", "TP.HCM", "Đà Nẵng", "Cần Thơ", "", "",
        "A", 30
    ])
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def parse_import_file(file_storage):
    filename = file_storage.filename.lower() if file_storage.filename else ""
    rows = []

    if filename.endswith(".csv"):
        data = file_storage.read()
        stream = io.StringIO(data.decode("utf-8-sig", errors="replace"))
        reader = csv.reader(stream)
        header = True
        for idx, row in enumerate(reader, start=1):
            if header:
                header = False
                continue
            if not any(cell.strip() for cell in row if isinstance(cell, str)):
                continue
            rows.append((idx, row))
    else:
        wb = load_workbook(file_storage, data_only=True)
        ws = wb.active
        for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if idx == 1:
                continue
            if not row or not any(cell is not None and str(cell).strip() != "" for cell in row):
                continue
            row_vals = [str(cell).strip() if cell is not None else "" for cell in row]
            rows.append((idx, row_vals))

    return rows


def process_imported_questions(rows):
    valid_questions = []
    errors = []

    LETTER_MAP = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5}

    for row_num, row in rows:
        content = row[0].strip() if len(row) > 0 else ""
        raw_type = row[1].strip() if len(row) > 1 else ""
        normalized_type = strip_accents(raw_type)

        if not content:
            errors.append(f"dòng {row_num} – Thiếu nội dung câu hỏi")
            continue

        q_type = None
        if "1 dap an" in normalized_type or normalized_type == "single":
            q_type = "single"
        elif "nhieu dap an" in normalized_type or normalized_type == "multiple":
            q_type = "multiple"
        elif "dung-sai" in normalized_type or "dung/sai" in normalized_type or normalized_type == "true_false":
            q_type = "true_false"

        if not q_type:
            errors.append(f"dòng {row_num} – Loại câu hỏi không hợp lệ")
            continue

        raw_choices = [row[i].strip() if len(row) > i else "" for i in range(2, 8)]
        choices_list = [c for c in raw_choices if c != ""]
        if len(choices_list) < 2 or len(choices_list) > 6:
            errors.append(f"dòng {row_num} – Số lượng đáp án phải từ 2-6")
            continue

        raw_correct = row[8].strip() if len(row) > 8 else ""
        if not raw_correct:
            errors.append(f"dòng {row_num} – Thiếu đáp án đúng")
            continue

        correct_indices = set()
        invalid_letter = False

        parts = [p.strip() for p in re.split(r'[,;\s]+', raw_correct) if p.strip()]
        for part in parts:
            part_upper = part.upper()
            part_norm = strip_accents(part)
            if part_upper in LETTER_MAP and LETTER_MAP[part_upper] < len(choices_list):
                correct_indices.add(LETTER_MAP[part_upper])
            elif part.isdigit() and 1 <= int(part) <= len(choices_list):
                correct_indices.add(int(part) - 1)
            else:
                matched = False
                for idx_c, c_text in enumerate(choices_list):
                    if strip_accents(c_text) == part_norm:
                        correct_indices.add(idx_c)
                        matched = True
                        break
                if not matched:
                    invalid_letter = True
                    break

        if invalid_letter or not correct_indices:
            errors.append(f"dòng {row_num} – Đáp án đúng không hợp lệ")
            continue

        if q_type == "single" and len(correct_indices) != 1:
            errors.append(f"dòng {row_num} – Câu hỏi 1 đáp án phải có đúng 1 đáp án đúng")
            continue
        elif q_type == "true_false":
            if len(choices_list) != 2:
                errors.append(f"dòng {row_num} – Câu đúng/sai phải có đúng 2 đáp án")
                continue
            if len(correct_indices) != 1:
                errors.append(f"dòng {row_num} – Câu đúng/sai phải có đúng 1 đáp án đúng")
                continue
        elif q_type == "multiple" and len(correct_indices) < 1:
            errors.append(f"dòng {row_num} – Câu hỏi nhiều đáp án phải có ít nhất 1 đáp án đúng")
            continue

        time_col_idx = 10 if len(row) >= 11 else 9
        time_limit = None
        if len(row) > time_col_idx and row[time_col_idx]:
            try:
                time_limit = int(float(str(row[time_col_idx]).strip()))
                if not (5 <= time_limit <= 600):
                    time_limit = None
            except ValueError:
                time_limit = None

        formatted_choices = []
        for idx_c, c_text in enumerate(choices_list):
            formatted_choices.append({
                "content": c_text,
                "is_correct": idx_c in correct_indices,
                "order_num": idx_c + 1
            })

        valid_questions.append({
            "type": q_type,
            "content": content,
            "choices": formatted_choices,
            "time_limit": time_limit
        })

    return valid_questions, errors

