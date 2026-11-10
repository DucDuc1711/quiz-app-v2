# TIẾN ĐỘ DỰ ÁN

## Trạng thái
- Phase đang làm: P5 xong, chờ thử tay — backend xong (93 pytest, verify_teacher.py PASS, verify_flow.py PASS), frontend P5 đã build xanh

(P0–P4 đã xong; chi tiết đã làm xem mục "Quyết định / thay đổi so với đặc tả" dưới đây.)

## Đã làm trước P4 (P2/P3, chuyển từ mục Trạng thái)
- Đã sửa lỗi thêm câu hỏi không lưu choices và thiếu validate theo spec (single/multiple/true_false, 2-6 đáp án, độ dài ký tự, ràng buộc đáp án đúng). Áp dụng cho thêm câu hỏi và cập nhật câu hỏi (PUT).
- Đã cập nhật GET /api/teacher/quizzes/<id> trả về đầy đủ thông tin bộ đề kèm danh sách câu hỏi và đáp án (is_correct).
- Đã sửa POST /api/play/<token>/next tính và trả seconds_left là số (không bị null) ở phase question.
- Đã sửa POST /api/play/<token>/answer trả 400 kèm thông báo "Thiếu question_id hoặc choice_ids." nếu thiếu trường.
- Đã viết test và chạy pytest toàn bộ xanh (dùng DB :memory:).

## Đang làm dở (đợt sửa P5 — ĐỢT 2)
- [x] Bước 1: Xác nhận nguyên nhân thật (đã đọc code thực tế: toast undefined do destructure sai { toast } thay vì { success, error }; thiếu Authorization do api/teacher.js tự tạo instance axios riêng không có interceptor; JWT callback còn tiếng Anh; chuỗi không dấu trong ErrorState/LoadingState/ResultView/ToastHost)
- [x] Chặng A (mục 1-4): sửa lỗi giao diện — toast thống nhất, axios gắn Authorization cho /api/teacher/*, JWT callback tiếng Việt, chuỗi có dấu, PasswordField, script quét không dấu
  - Đã sửa 10 file view dùng useToast: LoginView, RegisterView, DashboardView, AccessCodeBlock, ImportBlock, LibraryDetailView, QuestionList, QuizEditorView, QuizSettings, ResultsView
  - Đã đổi api/teacher.js dùng shared axios instance có interceptor
  - Đã cập nhật JWT callbacks trong backend/app/__init__.py (tất cả tiếng Việt có dấu)
  - Đã sửa ErrorState, LoadingState, ToastHost, ResultView header bảng
  - Đã tạo PasswordField.vue dùng chung, áp dụng cho LoginView, RegisterView
  - Đã chạy node scripts/check_vietnamese.mjs → PASS
  - npm run build → PASS
  - pytest test_play.py (30), test_codes.py (2), test_models.py (2), test_flow_p3.py (4), test_p3_fixes.py (2), test_uploads.py (7) → PASS
  - verify_teacher.py → PASS, verify_flow.py → PASS
- [x] Chặng B (mục 5-6): bỏ allow_retake, làm lại không giới hạn, xếp hạng lượt tốt nhất mỗi thiết bị
  - Xóa cột Quiz.allow_retake (model, migration batch_alter_table, áp dụng lên quiz.db)
  - Xóa mọi tham chiếu allow_retake trong teacher.py (GET, PUT), play.py (join), QuizSettings.vue, test_play.py
  - play.py join: không còn 409 "đã làm"; in_progress -> resume 200; finished/no attempt -> tạo mới 201
  - scoring.py compute_ranking: chỉ attempt finished, nhóm theo device_id lấy attempt tốt nhất (score cao -> time thấp -> finished_at sớm); cùng score & time -> cùng hạng; total_participants = số device đã finished; rank/is_me dựa trên device_id
  - play.py result/ranking: me_token dùng device_id, total_participants đếm distinct device
  - Frontend: HomeView.vue xóa error 409 "đã làm"; QuizSettings.vue xóa checkbox "Cho làm lại"
  - Test: test_play.py 30 pass (test_join_device_multiple_retakes mới), test_teacher.py 25 pass, test_auth.py 14 pass, test_admin.py 13 pass, test_codes.py 2, test_models.py 2, test_flow_p3.py (4), test_p3_fixes.py (2), test_uploads.py (7) = 99 test
  - verify_teacher.py PASS, verify_flow.py PASS
- [x] Chặng C1 (mục 7): Vitest — 8 file test (axios.test.js, useToast.test.js, auth.test.js, routerGuard.test.js, LoginView.test.js, RegisterView.test.js, DashboardView.test.js, PasswordField.test.js), 29 test pass; npx vitest run --reporter=dot PASS; npm run build PASS; pytest PASS; verify_flow.py PASS; verify_teacher.py PASS; node scripts/check_vietnamese.mjs PASS
- [ ] Chặng C2 (mục 8-9): Playwright e2e, báo cáo, commit
- [x] Bước 1: Sửa lỗi gốc backend (play.py): state() đọc attempt.phase, trả feedback khi phase == "feedback"; tự ghi "không trả lời" nếu quá hạn chưa answer; answer() nhận khi phase còn "question", quá hạn vẫn chấm, mảng rỗng hợp lệ, validate choice_ids là list và thuộc câu hỏi, 409 khi trả lời lại; lỗi cú pháp error_response chuẩn 2 tham số; _get_attempt_or_404 trả 2 phần tử; db.session.get thay Question.query.get; chuỗi tiếng Việt có dấu đầy đủ.
- [x] Bước 2: Test backend (pytest, DB :memory:) — thêm/sửa test: mảng rỗng 200 is_correct false; thiếu trường 400; choice_ids không phải list 400; chọn id không thuộc câu hỏi 400; gửi đúng hạn; gửi quá hạn chọn đúng (timed_out true và is_correct true) và chọn sai; state sau answer trả phase feedback (câu giữa, câu cuối, answer rỗng); gọi state nhiều lần ở feedback kết quả giống nhau không tạo thêm bản ghi; trả lời lại 409; token sai 404; question_id sai 409; next khi chưa answer 409. pytest xanh toàn bộ (93 test).
- [x] Bước 3: Kiểm tra PlayView với JSON thật — sửa loadState() không gán question.value = undefined ở phase feedback (khắc phục lỗi phản hồi không hiện); giữ selected_value = đáp án đã chọn ở feedback; backend _build_feedback_payload trả thêm object question để F5 ở phase feedback vẫn render; chuỗi thông báo FE có dấu ("Không lấy được trạng thái câu hỏi.", "Không nộp được đáp án.", "Không lấy câu tiếp theo.", "Câu {i} / {total}"). Xác minh: mount luôn GET state, không lưu sessionStorage, lỗi API hiện thông báo tiếng Việt + nút "Thử lại", nút "Chốt!" cố định, Enter chốt, chống bấm đúp, nhấp nháy ≤5 giây, hết giờ tự gửi đáp án đang chọn, mốc thời gian không đếm tick, giữ tab_hidden, cảnh báo rời trang, không nút quay lại, không nút "Câu tiếp".
- [x] Bước 4: Theme và thẻ đáp án — theme.css: --q-success #15803D, --q-danger #B91C1C (xóa #16A34A, #DC2626); thêm --q-success-dark/#14532D, --q-danger-dark/#7F1D1D để chữ trắng trên nền đậm đạt ≥4,5:1; LETTER_COLORS A (#7C3AED), E (#0369A1) đổi sắc đậm hơn; OptionCard.vue dùng biến CSS, chữ trắng, 4 trạng thái phản hồi (correct/wrong/skipped/idle), hết giờ không chọn chỉ hiện "Bỏ sót"; prefers-reduced-motion bỏ hiệu ứng còn giữ màu/viền/biểu tượng; CountdownRing đồng hồ báo thức SVG, số giây làm tròn lên, deadline tính từ seconds_left, thanh chạy tuyến tính, ≤5 giây đỏ + rung nhẹ, resync khi quay lại tab.
- [x] Bước 5: Script kiểm tra tự động — chuyển backend/verify_flow.py sang backend/scripts/verify_flow.py (chạy `python scripts/verify_flow.py` từ thư mục backend, thêm sys.path để import app, extensions, models), test client với DB :memory: (TestingConfig), hàm check(cond, msg, data=None) in PASS/FAIL kèm JSON khi FAIL, chạy hết rồi thoát mã khác 0 nếu có FAIL; bộ đề 3 câu gồm single, multiple, true_false; các ca: join; state question; answer có chọn; state NGAY SAU answer phải là feedback; gọi state lại nhiều lần ở phase feedback; next; answer mảng rỗng; state feedback; câu giữa và câu cuối; next đến hết; result (score đúng); state sau khi hoàn thành; quá hạn (sửa question_started_at trong DB) cho cả ca có chọn đúng và ca không chọn; thông báo lỗi 400/409/404 phải có dấu. Kết quả chạy script: 12/12 PASS.
- [x] Bước 6: Dọn file và git — xóa backend/pytest_out.txt, backend/r1.txt, backend/r2.txt, backend/verify_flow.py (đã chuyển sang scripts/), frontend/write_play_a.py, các script đọc tạm; xóa 65 file test rác trong backend/app/uploads/, thêm .gitkeep; .gitignore bổ sung backend/app/uploads/* (trừ .gitkeep) và *.txt; test_uploads.py dùng fixture tmp_path (monkeypatch UPLOAD_FOLDER) để không ghi vào thư mục thật.
- [x] Bước 7: Xác nhận config.py đã chuyển — không còn import kiểu cũ `from config import ...` ở run.py, app/__init__.py, conftest.py, migrations/env.py; .env vẫn được đọc qua load_dotenv(); đường dẫn DB backend/app/instance/quiz.db không lệch (không sinh quiz.db mới ở chỗ khác); chạy được pytest, flask db upgrade, python run.py (import app OK).
- [x] Bước 8: Ghi đè PROGRESS.md (đã hoàn thành).
- [ ] Bước 9: Kiểm tra cuối (pytest xanh, npm run build OK, verify_flow.py toàn PASS) rồi git commit.

## Đã làm ở P5
- 1. Hạ tầng giáo viên: api/teacher.js, store auth (khóa riêng quiz_teacher_token/quiz_teacher_user), axios Bearer + xử lý 401, router guard /teacher/*, composable useToast + ToastHost, ConfirmDialog/LoadingState/EmptyState/ErrorState, layout thanh trên.
- 2. Đăng ký/đăng nhập (/teacher/register, /teacher/login): validation spec, hiện/ẩn mật khẩu, lỗi từng ô, từ chối admin.
- 3. Dashboard (/teacher): thẻ bộ đề (mã in đậm, số câu, lượt làm, mở/đóng, công khai/riêng, ngày cập nhật), hành động Soạn/Kết quả/Nhân bản/Xóa, công tắc is_open, tìm kiếm, tạo mới.
- 4. Trình soạn bộ đề (/teacher/quizzes/:id): cài đặt, mã tham gia + sao chép link/QR/chiếu lên bảng, câu hỏi (3 loại, true_false cố định Đúng/Sai, không ô giải thích, ảnh upload), nhập Excel/CSV, cảnh báo & khóa khi có lượt làm, xóa kết quả để mở khóa, ErrorState 404.
- 5. Kết quả (/teacher/quizzes/:id/results): thẻ thống kê, tỉ lệ sai thanh CSS, bảng lượt làm sắp xếp/tìm/xóa, xuất Excel/CSV.
- 6. Thư viện (/teacher/library, /teacher/library/:id): tìm debounce, lọc thẻ, phân trang, chi tiết đánh dấu đáp án đúng, clone.
- 7. Chất lượng: loading/rỗng/lỗi, xác nhận xóa, nút ≥44px, responsive 360px, biến theme.css, không v-html, thông báo có dấu.

## Quyết định / thay đổi so với đặc tả
- Desktop-first 1280px, responsive 768px và 360px.
- Mọi câu học sinh bấm một nút "Chốt!" cố định (không có nút "Câu tiếp"); chạm thẻ chỉ chọn, không gửi; Enter chốt đáp án; chống bấm đúp qua cờ answering.
- Tự chuyển câu sau 5 giây (8 giây nếu explanation sau trim không rỗng); hết giờ (≤5 giây) đồng hồ đỏ #B91C1C và rung nhẹ, tự gửi đáp án đang chọn (mảng rỗng nếu chưa chọn) và vẫn chấm (timed_out = true, is_correct theo lựa chọn).
- Không ân hạn: server nhận answer khi phase còn "question" kể cả đã quá limit; quá hạn thì timed_out = true nhưng vẫn chấm lựa chọn đã chọn; time_taken = min(elapsed, limit).
- state() đọc attempt.phase: nếu phase == "feedback" trả feedback ngay (không trả lại câu hỏi); nếu phase == "question" và đã quá hạn chưa answer thì tự ghi "không trả lời", chuyển phase = "feedback", trả feedback.
- Cấu trúc backend thực tế: extensions.py, models.py, utils.py, cli.py ở backend/ root; config.py ở backend/app/.
- Uploads không đưa vào git (.gitignore: backend/app/uploads/* trừ .gitkeep); test dùng tmp_path.
- Màu: đúng #15803D (xanh lá), sai #B91C1C (đỏ); đã xóa #16A34A, #DC2626.
- P5: token giáo viên lưu localStorage khóa riêng (quiz_teacher_token / quiz_teacher_user) để không đè admin của P6.
- P5: đổi thứ tự câu hỏi bằng nút Lên/Xuống (PUT .../questions/order {ids}), không kéo thả.
- P5: biểu đồ tỉ lệ sai từng câu dùng thanh ngang CSS thuần, không thêm thư viện biểu đồ.
- P5: xóa kết quả dùng ConfirmDialog thường nêu rõ số lượt làm sẽ mất và không hoàn tác được; backend trả 409 thì hiện toast và tải lại.
- P5: bỏ ô giải thích khỏi form câu hỏi (theo spec mới).
- P5: open_at/close_at backend trả ISO (isoformat, có thể có múi giờ +00:00); frontend chuyển sang datetime-local theo múi giờ local và ngược lại.
- P5: trường backend đã thêm: question_count, attempt_count, is_open, is_public, updated_at (GET danh sách quizzes); correct_answers, time_spent, tab_switch_count (attempts); max_score, min_score (stats); is_correct (chi tiết library); PUT quizzes nhận thêm question_time, shuffle flags, is_open, open_at, close_at, tags.


## Quyết định P5 (fix đăng ký/đăng nhập)
- Username và email không phân biệt hoa thường: lưu chữ thường, tìm bằng func.lower(User.username/email) trong auth.py; dùng normalize_username/normalize_email/normalize_login_value trong utils.py cho mọi nơi (register, login, admin_login, cli create-admin/seed).
- Mật khẩu phân biệt hoa thường và giữ nguyên văn: không strip, không lower, so sánh bằng check_password_hash nguyên văn.
- Ô mã bộ đề học sinh là ô duy nhất được ép chữ hoa (HomeView.vue JS toUpperCase); mọi ô username/email/mật khẩu bỏ ép chữ hoa, dùng autocapitalize/autocorrect/spellcheck/autocomplete phù hợp.
- P5: có Vitest (8 file test, 29 test) cho axios interceptor, useToast, auth store, router guard, LoginView, RegisterView, DashboardView, PasswordField.

## Thiết kế giao diện (P4)
- Đồng hồ báo thức: SVG đồng hồ, số giây làm tròn lên ở giữa, thanh chạy tuyến tính bằng requestAnimationFrame/CSS animation, deadline tính từ lúc nhận seconds_left (không cộng dồn tick).
- Nút "Chốt!" cố định cho mọi câu; chạm thẻ không gửi; Enter chốt; chống bấm đúp; nhấp nháy ≤5 giây; không nút "Câu tiếp"; đồng hồ về 0 tự gửi đáp án đang chọn; dùng mốc thời gian không đếm tick; giữ tab_hidden; cảnh báo rời trang; không nút quay lại.
- Màu đúng #15803D, sai #B91C1C; chữ trắng trên nền đậm đạt tương phản ≥4,5:1 (6 chữ A–F đã kiểm tra, đổi sắc đậm nếu thiếu); 4 trạng thái phản hồi (đúng/sai/bỏ sót/bình thường); hết giờ không chọn gì chỉ hiện đáp án đúng kiểu "Bỏ sót", không thẻ đỏ; prefers-reduced-motion bỏ phóng to/nảy/rung/nhấp nháy nhưng giữ màu, viền, biểu tượng.
- Tất cả biến/style tập trung trong frontend/src/assets/theme.css.

## Lỗi đã biết
- Không có lỗi nghiêm trọng còn tồn tại sau khi sửa build (template Invalid end tag, chuỗi message thoát dấu nháy, debounce không export từ Vue đã khôi phục).
- P5 (đã sửa):
  * Ép chữ hoa toàn bộ ô nhập do CSS text-transform: uppercase trên .q-form-control trong theme.css (chỉ đổi hiển thị, không đổi giá trị gửi đi). Ô mã bộ đề học sinh giữ viết hoa bằng JS ở HomeView.vue (ô duy nhất được phép ép).
  * Báo "Đăng ký thất bại" giả dù backend đã tạo thành công: try/catch trong RegisterView/LoginView bao trộn lệnh gọi API lẫn bước sau (setAuth, toast, router.push), lỗi phía sau bị nuốt và hiện câu dự phòng. Sửa bằng tách try/catch.
  * Đăng nhập không phân biệt hoa thường: auth.py trước đây so sánh User.username == username_or_email (phân biệt). Sửa bằng func.lower(User.username) == giá trị đã lower OR func.lower(User.email) == giá trị đã lower, cùng normalize_login_value (strip + lower). Chuỗi thông báo backend không dấu → đã sửa thành có dấu.
- P5 lần 2 (đã sửa):
  * Toast: 14 chỗ viết const { toast } = useToast() trong khi composable trả { toasts, success, error, remove } → sửa thành const { toasts, success, error, remove } = useToast() và dùng toast.toasts.value trong test.
  * Thiếu Authorization: api/teacher.js tạo axios.create riêng không có interceptor → sửa dùng shared axios instance (@/api/axios) đã có interceptor gắn Bearer quiz_teacher_token cho /api/teacher/* (trừ /api/auth/* và /api/play/*), và xóa phiên + dispatch 'auth-logout' khi 401 trên endpoint không phải login.
  * JWT trả tiếng Anh → sửa tất cả JWT callbacks trong backend/app/__init__.py sang tiếng Việt có dấu.
  * Chuỗi không dấu trong ErrorState/LoadingState/ResultView/ToastHost → đã sửa sang có dấu đầy đủ.
  * Nút Hiện/Ẩn PasswordField: aria-label tiếng Việt ('Hiện mật khẩu' / 'Ẩn mật khẩu'), đổi type của ô input giữa 'password' và 'text'.

## Đề xuất sửa spec
- GET /api/teacher/library/:id cần trả choices kèm is_correct để giao diện thư viện chi tiết đánh dấu đáp án đúng (đã bổ sung vào backend và cập nhật test, pytest vẫn xanh, không đổi tên trường cũ).

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

Chạy kiểm tra frontend: npm test (Vitest, 29 test) và npm run build.

Chạy kiểm tra backend: pytest (toàn bộ 93 test, DB :memory:) và python scripts/verify_teacher.py (kiểm tra API giáo viên P5, toàn PASS, thoát mã 0).

Kiểm tra tiếng Việt: node scripts/check_vietnamese.mjs (PASS = không chuỗi tiếng Việt không dấu trong src/app).

Mẹo test làm lại cùng máy: nên dùng một địa chỉ cố định (localhost hoặc 127.0.0.1) vì mỗi địa chỉ có localStorage riêng. Có thể xóa hai khóa rác access_token, user trong localStorage (F12 Console gõ `localStorage.removeItem('access_token'); localStorage.removeItem('user')`) rồi tải lại trang để bắt đầu lượt làm mới.

Cách lấy mã bộ đề: xem access_code trong trang giáo viên hoặc dùng bộ đề seed (mã trong database/seeder).

## Checklist
- [x] P0–P4: đã xong (xem mục "Quyết định / thay đổi so với đặc tả")
- [x] P5: frontend giáo viên — build xanh, pytest 93 passed, verify_teacher.py PASS, verify_flow.py PASS (chờ thử tay)
- [ ] P6: admin — KHÔNG làm trong P5


