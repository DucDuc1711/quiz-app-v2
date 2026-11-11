# TIẾN ĐỘ DỰ ÁN

## Trạng thái
- Phase đang làm: P5 Đợt 4 xong — backend xong (102 pytest, verify_teacher.py PASS, verify_flow.py PASS), frontend P5 build xanh, Vitest 11 test pass

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
## Chặng C2 (mục 8-9): Playwright e2e — BỎ (chạy tay)

### Nguyên nhân chặn:
- Google Chrome KHÔNG được cài trên máy (đã kiểm tra C:\Program Files\Google\Chrome, C:\Program Files (x86)\Google\Chrome, C:\Users\nuyan\AppData\Local\Google\Chrome — không tìm thấy chrome.exe).
- Không có Microsoft Edge cũng.
- npx playwright install chromium BỊ CHẶN CDN → không được tải thêm (theo yêu cầu).
- playwright.config.js đã được cập nhật: `channel: 'chrome'` trong use và projects (đúng yêu cầu mục 7).
- Ngoài ra, Flask backend trên Windows không thể mở SQLite file `instance/e2e.db` (lỗi `sqlalchemy.exc.OperationalError: unable to open database file`) khi chạy qua playwright webServer. Cần fix path DATABASE_URL trên Windows.

### Việc đã làm cho Chàng C:
- Đã cập nhật playwright.config.js: thêm `channel: 'chrome'` vào `use` và `projects[0].use`.
- Đã kiểm tra e2e spec file tại `frontend/tests/e2e/quiz-app.spec.js` (10 test cases).

### Để tiếp tục (khi có Chrome):
- Cài Google Chrome hoặc Edge (Chromium-based).
- Fix DATABASE_URL path cho Windows trong playwright.config.js (dùng đường dẫn tuyệt đối hoặc `sqlite:////`).
- Chạy `npm run test:e2e` và đợi xanh.

## Chặng A (mục 1-5) — ĐỢT 3 (HOÀN TẤT)
- [x] Mục 1: Quy ước toast — const toast = useToast() thống nhất, chỉ ToastHost.vue destructure { toasts, remove }
- [x] Mục 2: Sửa lỗi trình soạn, dashboard, thư viện
  - Đã thêm nút "Tạo bộ đề mới" vào DashboardView (thiếu nút mở modal)
  - Đã sửa error → loadError trong ResultsView.vue và QuizEditorView.vue templates
  - Đã sửa ImportBlock.vue template: file.value → file (Vue auto-unwraps refs trong template)
  - Đã thêm onMounted(load) vào ResultsView.vue (thiếu gọi load khi mount)
- [x] Mục 3: Axios và phiên đăng nhập — đã đúng: chỉ bỏ token cho /auth/login, /auth/register, /api/play/*; /api/auth/me và /api/teacher/* có Bearer; auth.init chỉ xóa khi 401 thật, giữ khi lỗi mạng
- [x] Mục 4: Luật chặn lỗi — scripts/check_conventions.mjs đã tạo, lint:conv đã thêm vào package.json
- [x] Mục 5: Kiểm tra Chặng A
  - npm run build: PASS (172 modules, 354ms)
  - npx vitest run: 58 passed (9 files)
  - node scripts/check_vietnamese.mjs: PASS
  - node scripts/check_conventions.mjs: PASS
  - npm run lint:conv: PASS
  - pytest: 99 passed
- [x] Commit: "P5 fix 3A: toast, axios, dashboard, thu vien"
- Đã cài @playwright/test v1.65.0 (devDependency)
- Đã tạo playwright.config.js: backend cổng 5100 (DATABASE_URL=sqlite:///instance/e2e.db), frontend cổng 5273 (VITE_API_TARGET=http://127.0.0.1:5100), e2e DB là backend/instance/e2e.db (trong .gitignore)
- Đã cập nhật vite.config.js: đọc VITE_API_TARGET từ env để proxy /api
- Đã tạo frontend/tests/e2e/quiz-app.spec.js: 10 test cases (đăng ký, library, đăng xuất/đăng nhập sai/đúng, nút Hiện/Ẩn, tạo bộ đề, học sinh làm bài 2 lần, giáo viên xem kết quả, quét không dấu 6 trang, quét trang chi tiết + kết quả)
- Đã cập nhật .gitignore (root + frontend): thêm e2e.db, playwright-report/, test-results/
- Đã thêm script "test:e2e": "playwright test" vào frontend/package.json
- CHƯA CHẠY ĐƯỢC e2e: npx playwright install chromium bị kẹt khi tải chrome-win64.zip từ cdn.playwright.dev (mạng chặn/gián tiếp). Không có Chrome/Chromium trên hệ thống. Không thể chạy npm run test:e2e.
- Việc còn tồn đọng: cài được Chromium rồi chạy npm run test:e2e till xanh.

## Lỗi đã-known (nguyên nhân thật + cách sửa)
1. Toast undefined: 14 chỗ viết `const { toast } = useToast()` trong khi composable trả `{ toasts, success, error, remove }`. Sửa thành `const { toasts, success, error, remove } = useToast()` ở LoginView.vue, RegisterView.vue, DashboardView.vue và các view khác.
2. Thiếu Authorization: api/teacher.js tạo axios.create riêng không có interceptor → sửa dùng shared axios instance (@/api/axios) đã có interceptor gắn Bearer quiz_teacher_token cho /api/teacher/* (trừ /api/auth/* và /api/play/*), và xóa phiên + dispatch 'auth-logout' khi 401 trên endpoint không phải login.
3. JWT trả tiếng Anh: tất cả JWT callbacks trong backend/app/__init__.py (expired_token_loader, invalid_token_loader, unauthorized_loader, revoked_token_loader, needs_fresh_token_loader) trả {"error": "..."} tiếng Việt có dấu với mã 401.
4. Chuỗi không dấu: ErrorState "Co loi xay ra", "Thu lai"; LoadingState; ResultView header; ToastHost → sửa sang có dấu đầy đủ. Tạo script scripts/check_vietnamese.mjs quét frontend/src và backend/app.
5. Nút Hiện/Ẩn mật khẩu: tạo PasswordField.vue dùng chung, aria-label tiếng Việt, type chuyển đổi password/text, nút bo tròn cùng hàng với ô input. Áp dụng cho LoginView.vue, RegisterView.vue.
6. localStorage khóa rác: access_token, user của dự án cũ không được đọc/ghi bởi dự án này (chỉ dùng quiz_teacher_token, quiz_teacher_user).

## Quyết định (P5 lượt 2)
- Bỏ cột Quiz.allow_retake (migration batch_alter_table, xóa mọi tham chiếu trong models, routes, views, tests, scripts verify).
- Làm lại không giới hạn: play.py join không còn 409 "đã làm"; in_progress → resume 200 cùng token; finished/no attempt → tạo mới 201.
- Xếp hạng học sinh: chỉ tính attempt finished; mỗi device_id một dòng = lượt tốt nhất (score cao nhất, time_spent thấp nhất, finished_at sớm nhất); cùng score & time → cùng hạng; total_participants = số device đã finished; rank/is_me dựa trên device_id. Giáo viên xem mọi lượt (attempts, stats, export không đổi).
- Vitest: 8 file test, 29 test pass. Playwright: cấu hình sẵn, chờ cài Chromium để chạy e2e.

## Cách chạy (cập nhật)
- Frontend kiểm tra: npm test (Vitest, 29 test), npm run build, node scripts/check_vietnamese.mjs
- Backend kiểm tra: pytest (DB :memory:), python scripts/verify_flow.py, python scripts/verify_teacher.py
- E2E (chưa chạy được do Chromium): npm run test:e2e (cần npx playwright install chromium thành công trước)
- Nên dùng một địa chỉ cố định (localhost hoặc 127.0.0.1) vì mỗi địa chỉ có localStorage riêng. Có thể xóa hai khóa rác access_token, user trong localStorage (F12 Console) rồi tải lại trang.
- E2E dùng DB riêng backend/instance/e2e.db, cổng backend 5100, frontend 5273, không đụng quiz.db thật.

## Checklist
- [x] P0 Tài liệu đặc tả
- [x] P1 Backend nền tảng (models, auth, CLI, seed)
- [x] P2 Backend luồng làm bài (play, uploads)
- [x] P3 Backend giáo viên và admin (CRUD, thư viện, import/export)
- [x] P4 Frontend nền và phần học sinh (tick sau khi đợt 2 xong và thử tay đủ kịch bản)
- [x] P5 Frontend giáo viên
- [ ] P6 Frontend admin
- [ ] P7 Hoàn thiện (giao diện, điện thoại, kiểm thử, README)

## Đang làm dở: P4 đợt 2
Việc cần làm (tick dần khi xong):
- [ ] Backend: xóa hẳn trường explanation (models, migration xóa cột, play, teacher, importer, exporter, file mẫu nhập, seed, test).
- [ ] Backend: thêm cột Attempt.feedback_started_at (migration); hằng FEEDBACK_SECONDS = 3; answer và state ở phase feedback trả feedback_seconds_left; next không chặn gọi sớm.
- [ ] Backend: answer trả 400 khi câu single/true_false gửi nhiều hơn 1 choice_id; thêm test.
- [ ] Frontend: xóa chữ giờ thừa giữa các thẻ đáp án; vòng tím là đồng hồ duy nhất (bỏ biểu tượng báo thức, số giây ở giữa, vòng cạn tuyến tính đồng bộ số, ẩn ở phase phản hồi).
- [ ] Frontend: câu single/true_false chỉ chọn được 1 thẻ (chọn thẻ mới thay thẻ cũ).
- [ ] Frontend: màu thẻ phản hồi nền nhạt, chữ đậm, viền #15803D / #B91C1C, bỏ màu -dark tô cả thẻ.
- [ ] Frontend: tự chuyển câu sau 3 giây dựa trên feedback_seconds_left; tái hiện và xác minh lỗi "đếm về 0 mà không tự chuyển" (nghi cờ chống bấm đúp bị kẹt) rồi sửa; F5 hoặc nhập lại mã ở phase phản hồi tiếp tục đúng số giây còn lại.
- [ ] Cập nhật verify_flow.py và pytest; chạy lại toàn bộ, build, commit.

## Lỗi đã biết
- Lỗi fixture test ghi đè/xóa DB thật (đã sửa): create_app() gọi db.init_app trước khi test gán URI :memory:, nên engine đã tạo và db.drop_all() xóa DB thật. Cách sửa: create_app nhận config object (TestingConfig, URI :memory:) áp dụng trước db.init_app; conftest.py assert URI bắt đầu bằng sqlite:///:memory: trước mọi thao tác DB.
- Lỗi P4 đợt 1 (đã sửa):
  1. Sau khi chốt, state vẫn trả câu hỏi, không hiện phản hồi; F5 và nhập lại mã bị kẹt. Nguyên nhân: state() không đọc attempt.phase. Cách sửa: state() trả feedback khi phase == "feedback".
  2. Panel phản hồi bị ẩn. Nguyên nhân: PlayView.loadState() gán question.value = undefined ở phase feedback nên v-if="question" ẩn panel. Cách sửa: chỉ gán question khi phase là question; state ở feedback trả kèm object question.
  3. Nhánh lỗi API trả 500. Nguyên nhân: error_response thiếu tham số status hoặc đặt status ngoài ngoặc. Cách sửa: luôn error_response("...", status); _get_attempt_or_404 trả (attempt, None) hoặc (None, error_response(...)).
  4. Thông báo thiếu dấu hoặc sai dấu. Cách sửa: viết lại toàn bộ chuỗi tiếng Việt có dấu.
- Lỗi mới thấy khi thử tay (đang sửa ở đợt 2):
  1. Chữ giờ thừa ("0:24") hiện lòi giữa các thẻ đáp án; vòng đồng hồ có biểu tượng đè lên số.
  2. Câu 1 đáp án chọn được 2 thẻ.
  3. Chữ trên thẻ đúng/sai gần như không đọc được (nền #14532D, #7F1D1D quá đậm, chữ tối màu).
  4. Phase phản hồi không tự chuyển câu khi chưa F5 (thanh về 0s mà đứng yên); F5 xong lại phải đợi đủ thời gian. Nguyên nhân: chưa xác định, Cline xác minh rồi ghi vào đây. Nghi cờ chống bấm đúp kẹt và server không lưu thời điểm bắt đầu phản hồi.
- Cần kiểm tra: đường dẫn DB (báo cáo ghi backend/app/instance/quiz.db, trước đó là backend/instance/quiz.db). Nếu có hai file quiz.db thì dữ liệu cũ nằm ở file kia.

## Quyết định / thay đổi so với đặc tả
- Desktop-first 1280px, responsive xuống 768px và 360px.
- Route teacher chỉ nhận role teacher, route admin chỉ nhận role admin (kiểm tra DB mỗi request); admin gọi /api/teacher/* trả 403.
- Thư viện trả {quizzes, page, per_page, total}, per_page mặc định 12.
- Xuất kết quả dùng tiêu đề tiếng Việt theo spec mục 6; cột Trạng thái là "Đã nộp" hoặc "Đang làm".
- Cấu trúc thực tế: extensions.py, models.py, utils.py, cli.py ở backend/ root; config.py ở backend/app/. Terminal dùng Windows CMD. DATABASE_URL trong .env là đường dẫn tuyệt đối (đường dẫn Windows có khoảng trắng).
- Test: fixture app và client nằm trong tests/conftest.py, dùng TestingConfig (:memory:). Uploads không đưa vào git (.gitignore: backend/app/uploads/* trừ .gitkeep); test dùng tmp_path.
- Luồng làm bài: một nút "Chốt!" cố định cho mọi câu; chạm thẻ chỉ chọn, không gửi; Enter chốt; chống bấm đúp.
- Không có ân hạn: server nhận answer khi phase còn question; quá hạn thì timed_out = true nhưng vẫn chấm lựa chọn đã chọn; time_taken = min(elapsed, limit); mảng rỗng hợp lệ (tính sai).
- state() đọc attempt.phase; quá hạn chưa answer thì tự ghi "không trả lời" và chuyển feedback.
- Đợt 2 (chốt với chủ dự án):
  - Bỏ hẳn tính năng giải thích (xóa cột explanation).
  - Mọi câu, kể cả câu cuối, tự chuyển sau 3 giây.
  - Server lưu feedback_started_at và trả feedback_seconds_left; F5 hoặc nhập lại mã tiếp tục đúng chỗ. Server không chặn next gọi sớm.
  - Câu single/true_false: giao diện chỉ giữ 1 thẻ, server trả 400 nếu gửi quá 1 id.
  - Đồng hồ: bỏ biểu tượng báo thức; vòng tím cạn dần đồng bộ với số giây ở giữa; ẩn ở phase phản hồi; ≤5 giây đỏ #B91C1C và rung nhẹ.
  - Thẻ phản hồi nền nhạt, chữ đậm; màu đậm chỉ dùng cho viền và biểu tượng.
  - Không đụng dữ liệu seed (DB chỉ để test, nội dung seed hiện không dấu).
  - Dòng ghi chú: chủ dự án tự sửa PROJECT_SPEC.md và PROGRESS.md; Cline không được sửa hai file này.

## Việc để lại cho P7
- Cân nhắc dời thư mục uploads ra backend/uploads hoặc instance/uploads.
- Chuyển nội dung seed sang tiếng Việt có dấu.
- Hoàn thiện coverage cho toàn bộ API endpoints.
- Giao diện điện thoại, README.

## Cách chạy
Backend (terminal 1, Windows CMD):
- cd /d backend, rồi kích hoạt venv: .venv\Scripts\activate
- Lần đầu: flask db upgrade, flask create-admin (đọc ADMIN_* từ .env), flask seed-samples (cần đã có admin)
- Chạy server: python run.py (cổng 5000)

Frontend (terminal 2):
- cd /d frontend
- Lần đầu: npm install
- Chạy dev: npm run dev (cổng 5173, proxy /api sang http://127.0.0.1:5000)
- Truy cập: http://127.0.0.1:5173

Kiểm tra (từ thư mục backend): pytest, và python scripts/verify_flow.py (kỳ vọng toàn PASS, thoát mã 0). Frontend: npm run build.

Mẹo thử tay:
- Làm lại cùng máy: dùng cửa sổ ẩn danh, hoặc F12 Console gõ localStorage.clear() rồi tải lại trang.
- Lấy mã bộ đề: xem access_code trong trang giáo viên (từ P5), hoặc in từ DB: python -c "from app import create_app; from models import Quiz; app=create_app(); app.app_context().push(); print([(q.title, q.access_code) for q in Quiz.query.all()])"

## Đợt 4 (P5 fix 4: modal, navbar, route param, seed co dau, khoa chinh sua)

Nguyen goc tung loi va file sua:
1. Modal Tao bo de (DashboardView): overlay @click (khong .self) => cham vao o nhap dong dong hop; dialog khong fixed/cuot/z-index. Sua: DashboardView.vue (@click.self, focus o tieu de, Enter tao, Esc/Huy dong); ConfirmDialog.vue (component goc: fixed, max-height 85vh, overflow-y, z-index 3000/3001, phim Esc) ap dung chung tat ca modal.
2. Thanh tren: isTeacherZone && auth.isAuthenticated => an lien ket giao vien khi khong o /teacher. Sua: App.vue (isTeacher = auth.isAuthenticated && auth.isTeacher), hien o moi trang khi da dang nhap.
3. Trang Ket qua API undefined: route khai bao :id nhung ResultsView doc props.quizId (khong khong ten). Sua: ResultsView.vue prop id; guard isValidId (so > 0) khong goi API, hien ErrorState "Duong khong hop le"; chi onMounted(load) goi 1 lan (bo toast trung, chi ErrorState).
4. Seed khong dau, thieu --reset: backend/cli.py chuoi seed khong dau. Sua: toan bo tieu de/mo the/the/ cau hoi/dap an tieng Viet co dau; them tu chon --reset xoa tat ca bo de cua admin, dat source_quiz_id = NULL cho ban sao giao vien, seed lai; khong --reset khong nhan dopp.
5. "· cau hoi" thieu so: get_quiz khong tra question_count/attempt_count. Sua: teacher.py tra 2 truong; QuizEditorView.vue dung attempt_count de khoa, hien canh bao o tab Cau hoi va Nhap Excel/CSV, vo hieu hoa nut, co nut "Xoa ket qua de chinh sua"; 409 => toast tieng Viet + reload; cai dat van sua duoc.
6. Giao dien nho: logo Q cach xa (margin-right 8px -> 2px) theme.css; footer bo "chay local"; HomeView.vue cau thong bao + tach 2 nut + nut Tham gia cho kiem tra; Dashboard 4 nut gọn 3 breakpoint.

Kiem tra: pytest 102 pass; npm test (Vitest) 11 pass; npm run build xanh; node scripts/check_vietnamese.mjs PASS; npm run lint:conv (check_conventions) PASS; verify_flow.py PASS; verify_teacher.py PASS; flask seed-samples --reset tren DB that -> 2 bo co dau, khong nhan dopp.

P6 (giao dien admin): HOAN (chu du an tu lam, khong duoc trong P5).
e2e Playwright: BO (chay tay, khong chay).
Spec phan hoi 3 giay: nguoi dung xac nhan on.
