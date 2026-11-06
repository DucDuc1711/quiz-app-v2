# TIẾN ĐỘ DỰ ÁN

## Trạng thái
- Phase đang làm: P4 (đang sửa lỗi và điều chỉnh)

(P0–P3 đã xong; chi tiết đã làm xem mục "Quyết định / thay đổi so với đặc tả" dưới đây.)

## Đã làm trước P4 (P2/P3, chuyển từ mục Trạng thái)
- Đã sửa lỗi thêm câu hỏi không lưu choices và thiếu validate theo spec (single/multiple/true_false, 2-6 đáp án, độ dài ký tự, ràng buộc đáp án đúng). Áp dụng cho thêm câu hỏi và cập nhật câu hỏi (PUT).
- Đã cập nhật GET /api/teacher/quizzes/<id> trả về đầy đủ thông tin bộ đề kèm danh sách câu hỏi và đáp án (is_correct).
- Đã sửa POST /api/play/<token>/next tính và trả seconds_left là số (không bị null) ở phase question.
- Đã sửa POST /api/play/<token>/answer trả 400 kèm thông báo "Thiếu question_id hoặc choice_ids." nếu thiếu trường.
- Đã viết test và chạy pytest toàn bộ xanh (dùng DB :memory:).

## Đang làm dở (đợt sửa P4)
- [x] Bước 1: Sửa lỗi gốc backend (play.py): state() đọc attempt.phase, trả feedback khi phase == "feedback"; tự ghi "không trả lời" nếu quá hạn chưa answer; answer() nhận khi phase còn "question", quá hạn vẫn chấm, mảng rỗng hợp lệ, validate choice_ids là list và thuộc câu hỏi, 409 khi trả lời lại; lỗi cú pháp error_response chuẩn 2 tham số; _get_attempt_or_404 trả 2 phần tử; db.session.get thay Question.query.get; chuỗi tiếng Việt có dấu đầy đủ.
- [x] Bước 2: Test backend (pytest, DB :memory:) — thêm/sửa test: mảng rỗng 200 is_correct false; thiếu trường 400; choice_ids không phải list 400; chọn id không thuộc câu hỏi 400; gửi đúng hạn; gửi quá hạn chọn đúng (timed_out true và is_correct true) và chọn sai; state sau answer trả phase feedback (câu giữa, câu cuối, answer rỗng); gọi state nhiều lần ở feedback kết quả giống nhau không tạo thêm bản ghi; trả lời lại 409; token sai 404; question_id sai 409; next khi chưa answer 409. pytest xanh toàn bộ (93 test).
- [x] Bước 3: Kiểm tra PlayView với JSON thật — sửa loadState() không gán question.value = undefined ở phase feedback (khắc phục lỗi phản hồi không hiện); giữ selected_value = đáp án đã chọn ở feedback; backend _build_feedback_payload trả thêm object question để F5 ở phase feedback vẫn render; chuỗi thông báo FE có dấu ("Không lấy được trạng thái câu hỏi.", "Không nộp được đáp án.", "Không lấy câu tiếp theo.", "Câu {i} / {total}"). Xác minh: mount luôn GET state, không lưu sessionStorage, lỗi API hiện thông báo tiếng Việt + nút "Thử lại", nút "Chốt!" cố định, Enter chốt, chống bấm đúp, nhấp nháy ≤5 giây, hết giờ tự gửi đáp án đang chọn, mốc thời gian không đếm tick, giữ tab_hidden, cảnh báo rời trang, không nút quay lại, không nút "Câu tiếp".
- [x] Bước 4: Theme và thẻ đáp án — theme.css: --q-success #15803D, --q-danger #B91C1C (xóa #16A34A, #DC2626); thêm --q-success-dark/#14532D, --q-danger-dark/#7F1D1D để chữ trắng trên nền đậm đạt ≥4,5:1; LETTER_COLORS A (#7C3AED), E (#0369A1) đổi sắc đậm hơn; OptionCard.vue dùng biến CSS, chữ trắng, 4 trạng thái phản hồi (correct/wrong/skipped/idle), hết giờ không chọn chỉ hiện "Bỏ sót"; prefers-reduced-motion bỏ hiệu ứng còn giữ màu/viền/biểu tượng; CountdownRing đồng hồ báo thức SVG, số giây làm tròn lên, deadline tính từ seconds_left, thanh chạy tuyến tính, ≤5 giây đỏ + rung nhẹ, resync khi quay lại tab.
- [x] Bước 5: Script kiểm tra tự động — chuyển backend/verify_flow.py sang backend/scripts/verify_flow.py (chạy `python scripts/verify_flow.py` từ thư mục backend, thêm sys.path để import app, extensions, models), test client với DB :memory: (TestingConfig), hàm check(cond, msg, data=None) in PASS/FAIL kèm JSON khi FAIL, chạy hết rồi thoát mã khác 0 nếu có FAIL; bộ đề 3 câu gồm single, multiple, true_false; các ca: join; state question; answer có chọn; state NGAY SAU answer phải là feedback; gọi state lại nhiều lần ở phase feedback; next; answer mảng rỗng; state feedback; câu giữa và câu cuối; next đến hết; result (score đúng); state sau khi hoàn thành; quá hạn (sửa question_started_at trong DB) cho cả ca có chọn đúng và ca không chọn; thông báo lỗi 400/409/404 phải có dấu. Kết quả chạy script: 12/12 PASS.
- [x] Bước 6: Dọn file và git — xóa backend/pytest_out.txt, backend/r1.txt, backend/r2.txt, backend/verify_flow.py (đã chuyển sang scripts/), frontend/write_play_a.py, các script đọc tạm; xóa 65 file test rác trong backend/app/uploads/, thêm .gitkeep; .gitignore bổ sung backend/app/uploads/* (trừ .gitkeep) và *.txt; test_uploads.py dùng fixture tmp_path (monkeypatch UPLOAD_FOLDER) để không ghi vào thư mục thật.
- [x] Bước 7: Xác nhận config.py đã chuyển — không còn import kiểu cũ `from config import ...` ở run.py, app/__init__.py, conftest.py, migrations/env.py; .env vẫn được đọc qua load_dotenv(); đường dẫn DB backend/app/instance/quiz.db không lệch (không sinh quiz.db mới ở chỗ khác); chạy được pytest, flask db upgrade, python run.py (import app OK).
- [x] Bước 8: Ghi đè PROGRESS.md (đã hoàn thành).
- [ ] Bước 9: Kiểm tra cuối (pytest xanh, npm run build OK, verify_flow.py toàn PASS) rồi git commit.

## Checklist
- [x] P0 Tài liệu đặc tả
- [x] P1 Backend nền tảng (models, auth, CLI, seed)
- [x] P2 Backend luồng làm bài (play, uploads)
- [x] P3 Backend giáo viên và admin (CRUD, thư viện, import/export)
- [ ] P4 Frontend nền và phần học sinh (đã xong chi tiết, tick sau khi bước 9 qua hết)
- [ ] P5 Frontend giáo viên
- [ ] P6 Frontend admin
- [ ] P7 Hoàn thiện (giao diện, điện thoại, kiểm thử, README)

## Lỗi đã known (đang theo dõi)
- Lỗi fixture test ghi đè/xóa DB thật: đã sửa bằng TestingConfig `:memory:` + conftest assert URI bắt đầu bằng `sqlite:///:memory:` trước db.create_all().
- 4 lỗi mục A (đợt P4):
  1. Sau chốt đáp án, state lại trả câu hỏi (không hiện phản hồi). Nguyên nhân gốc: backend `state()` không đọc `attempt.phase` → trả payload question thay vì feedback. Cách sửa: state() đọc attempt.phase; nếu phase == "feedback" trả _build_feedback_payload (tự ghi "không trả lời" nếu chưa có bản ghi); PlayView loadState() không gán question.value = undefined ở phase feedback; backend _build_feedback_payload trả thêm object question để F5 ở phase feedback vẫn render.
  2. Phản hồi không hiện sau khi chốt (vùng q-question-panel ẩn vì `v-if="question"` và question.value = undefined). Nguyên nhân: PlayView loadState() gán `question.value = d.question` (undefined ở phase feedback). Cách sửa: chỉ gán question khi phase == "question"; ở phase feedback giữ question và selected từ feedback.selected_choice_ids.
  3. Nhánh lỗi API trả 500 thay vì 400/409. Nguyên nhân: `error_response(...)` thiếu tham số status_code hoặc đặt status ngoài ngoặc (`error_response("..."), 409`). Cách sửa: chuẩn `return error_response("...", 404)`; _get_attempt_or_404 trả đúng 2 phần tử `(attempt, None)` hoặc `(None, error_response(...))`.
  4. Thông báo giao diện/backend không dấu/sai dấu. Nguyên nhân: chuỗi như "Thieu question_id hoac choice_ids", "Khong lay duoc trang thai cau hoi", ... Cách sửa: viết lại toàn bộ chuỗi tiếng Việt có dấu đầy đủ UTF-8 (play.py, auth.py, cli.py, teacher.py, PlayView.vue, test assertions).

## Quyết định / thay đổi so với đặc tả
- Desktop-first 1280px, responsive 768px và 360px.
- Mọi câu học sinh bấm một nút "Chốt!" cố định (không có nút "Câu tiếp"); chạm thẻ chỉ chọn, không gửi; Enter chốt đáp án; chống bấm đúp qua cờ answering.
- Tự chuyển câu sau 5 giây (8 giây nếu explanation sau trim không rỗng); hết giờ (≤5 giây) đồng hồ đỏ #B91C1C và rung nhẹ, tự gửi đáp án đang chọn (mảng rỗng nếu chưa chọn) và vẫn chấm (timed_out = true, is_correct theo lựa chọn).
- Không ân hạn: server nhận answer khi phase còn "question" kể cả đã quá limit; quá hạn thì timed_out = true nhưng vẫn chấm lựa chọn đã chọn; time_taken = min(elapsed, limit).
- state() đọc attempt.phase: nếu phase == "feedback" trả feedback ngay (không trả lại câu hỏi); nếu phase == "question" và đã quá hạn chưa answer thì tự ghi "không trả lời", chuyển phase = "feedback", trả feedback.
- Cấu trúc backend thực tế: extensions.py, models.py, utils.py, cli.py ở backend/ root; config.py ở backend/app/.
- Uploads không đưa vào git (.gitignore: backend/app/uploads/* trừ .gitkeep); test dùng tmp_path.
- Màu: đúng #15803D (xanh lá), sai #B91C1C (đỏ); đã xóa #16A34A, #DC2626.

## Thiết kế giao diện (P4)
- Đồng hồ báo thức: SVG đồng hồ, số giây làm tròn lên ở giữa, thanh chạy tuyến tính bằng requestAnimationFrame/CSS animation, deadline tính từ lúc nhận seconds_left (không cộng dồn tick).
- Nút "Chốt!" cố định cho mọi câu; chạm thẻ không gửi; Enter chốt; chống bấm đúp; nhấp nháy ≤5 giây; không nút "Câu tiếp"; đồng hồ về 0 tự gửi đáp án đang chọn; dùng mốc thời gian không đếm tick; giữ tab_hidden; cảnh báo rời trang; không nút quay lại.
- Màu đúng #15803D, sai #B91C1C; chữ trắng trên nền đậm đạt tương phản ≥4,5:1 (6 chữ A–F đã kiểm tra, đổi sắc đậm nếu thiếu); 4 trạng thái phản hồi (đúng/sai/bỏ sót/bình thường); hết giờ không chọn gì chỉ hiện đáp án đúng kiểu "Bỏ sót", không thẻ đỏ; prefers-reduced-motion bỏ phóng to/nảy/rung/nhấp nháy nhưng giữ màu, viền, biểu tượng.
- Tất cả biến/style tập trung trong frontend/src/assets/theme.css.

## Việc để lại cho P7
- Cân nhắc dời thư mục uploads ra backend/uploads hoặc instance/uploads.
- Hoàn thiện coverage cho toàn bộ API endpoints.
- Giao diện điện thoại, README.

## Cách chạy
Backend (terminal 1):
- Kích hoạt venv: .venv\Scripts\activate
- Khởi tạo DB: flask db upgrade
- Tạo admin: flask create-admin (đọc ADMIN_* từ .env)
- Seed dữ liệu mẫu: flask seed-samples (yêu cầu đã có admin)
- Chạy server: python run.py (cổng 5000)

Frontend (terminal 2, chạy song song với backend):
- cd /d frontend
- Cài đặt (lần đầu): npm install
- Chạy dev: npm run dev (mặc định cổng 5173, vite proxy /api sang http://127.0.0.1:5000)
- Truy cập: http://127.0.0.1:5173

Chạy kiểm tra backend: pytest (toàn bộ 93 test, DB :memory:).

Mẹo test làm lại cùng máy: mở cửa sổ ẩn danh hoặc vào F12 Console gõ `localStorage.clear()` rồi tải lại trang để bắt đầu lượt làm mới.

Cách lấy mã bộ đề: xem access_code trong trang giáo viên hoặc dùng bộ đề seed (mã trong database/seeder).

Chạy script kiểm tra tự động (từ thư mục backend): python scripts/verify_flow.py (kết quả mong đợi: toàn PASS, thoát mã 0).

