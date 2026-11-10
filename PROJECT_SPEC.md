# QUIZ APP v2 — ĐẶC TẢ DỰ ÁN

## 1. Mục tiêu
Web thi trắc nghiệm cho lớp học. Học sinh không cần tài khoản: nhập mã bộ đề và tên (tên nhập tự do, được phép trùng) rồi làm bài. Mỗi câu có đồng hồ riêng, chọn rồi bấm Chốt! (hoặc hết giờ) thì thấy đúng/sai, cuối bài xem điểm và bảng xếp hạng đầy đủ. Giáo viên tự đăng ký, tạo bộ đề, sinh mã tham gia, xem kết quả. Admin là chủ hệ thống (duy nhất một tài khoản, tạo bằng lệnh CLI) quản lý mọi thứ tại /admin. Ưu tiên giao diện máy tính (bản demo chạy local); vẫn phải hiển thị tốt trên điện thoại.

## 2. Công nghệ
- Backend: Python 3.10+, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flask-CORS, Flask-Limiter, python-dotenv, openpyxl, pytest, SQLite.
- Frontend: Vue 3 (Composition API, `<script setup>`, JavaScript), Vite, Vue Router 4, Pinia, Axios, Bootstrap 5, Bootstrap Icons, qrcode, canvas-confetti, font tự host bằng @fontsource (chạy được khi không có Internet).
- Cổng: backend 5000, frontend 5173. Vite proxy /api sang http://127.0.0.1:5000.
- Chọn phiên bản Vite và plugin tương thích với Node đang cài (kiểm tra `node -v` trước).

## 3. Quy ước chung
- Giao diện và thông báo lỗi bằng tiếng Việt; tên hàm, biến, file bằng tiếng Anh; comment tiếng Việt khi cần.
- Backend trả JSON: lỗi dạng {"error": "..."}; thành công dạng {"message": "...", ...dữ liệu}. Dùng mã HTTP đúng ngữ nghĩa (400, 401, 403, 404, 409, 413, 429). Hàm lỗi chuẩn: `error_response(message, status_code)` (đã trả sẵn tuple, luôn truyền đủ 2 tham số).
- Validation đăng ký: username 4–30 ký tự gồm chữ, số, dấu _ và dấu chấm; email hợp lệ; mật khẩu tối thiểu 8 ký tự. Backend và frontend phải đồng nhất.
- Tên đăng nhập và email KHÔNG phân biệt hoa thường: cắt khoảng trắng hai đầu, hạ chữ thường rồi mới validate, kiểm tra trùng và lưu; khi đăng nhập tìm bằng so sánh không phân biệt hoa thường. Mật khẩu PHÂN BIỆT hoa thường và giữ nguyên văn (không cắt, không đổi chữ).
- Frontend: không dùng CSS hay JS ép chữ hoa cho ô nhập; ô duy nhất được hiển thị chữ hoa là ô mã bộ đề của học sinh. Mọi thông báo, nhãn, nút, kể cả thông báo lỗi chung (ví dụ trạng thái "Có lỗi xảy ra", "Thử lại") phải có dấu. Phiên giáo viên lưu localStorage với khóa quiz_teacher_token và quiz_teacher_user (admin dùng khóa riêng ở P6); mọi lời gọi /api/teacher/* phải gắn Authorization: Bearer.
- Mỗi phase xong: chạy kiểm tra, cập nhật PROGRESS.md, git commit.
- Mọi chuỗi hiển thị cho người dùng (giao diện, thông báo lỗi từ backend) phải là tiếng Việt CÓ DẤU đầy đủ, đúng chính tả, lưu file UTF-8.

## 4. Cấu trúc thư mục
```
backend/
  run.py, requirements.txt, .env.example, .env
  extensions.py, models.py, utils.py, cli.py
  app/__init__.py (app factory), config.py
  app/routes/: auth.py, play.py, teacher.py, admin.py, uploads.py
  app/services/: codes.py, scoring.py, importer.py, exporter.py
  app/uploads/ (không đưa vào git, trừ .gitkeep)
  scripts/verify_flow.py (kiểm tra luồng làm bài, DB :memory:)
  tests/
  instance/ (quiz.db)
frontend/
  index.html, package.json, vite.config.js
  src/main.js, App.vue
  src/api/ (axios.js và các module gọi API)
  src/stores/ (auth.js)
  src/router/index.js
  src/composables/ (useCountdown.js, useDeviceId.js, ...)
  src/components/ (dùng chung)
  src/views/student/, src/views/teacher/, src/views/admin/
  src/assets/theme.css, main.css
```

## 5. Mô hình dữ liệu
- User: id, username (unique), email (unique), password_hash, role ('teacher' | 'admin'), is_active (mặc định True), created_at.
- Quiz: id, owner_id (User), title, description, tags (chuỗi cách nhau dấu phẩy), access_code (unique, 6 ký tự), is_open (True), open_at và close_at (nullable), question_time (giây, mặc định 30, từ 5 đến 600), shuffle_questions (False), shuffle_choices (False), show_ranking (True), is_public (True), source_quiz_id (nullable), created_at, updated_at.
- Question: id, quiz_id, type ('single' | 'multiple' | 'true_false'), content, image_url (nullable), order_num, time_limit (giây, nullable; rỗng thì dùng question_time của bộ đề). Không có trường giải thích.
- Choice: id, question_id, content, is_correct, order_num.
- Attempt: id, token (unique, secrets.token_urlsafe(24)), quiz_id, student_name, device_id, status ('in_progress' | 'finished'), phase ('question' | 'feedback'), current_index (từ 0), question_started_at (nullable), feedback_started_at (nullable; thời điểm vào phase feedback), question_order (JSON danh sách id câu), choice_orders (JSON {question_id: [choice_id, ...]}), total_questions, correct_answers, score (0–10, làm tròn 2 chữ số), time_spent (giây, float), tab_switch_count, started_at, finished_at.
- AttemptAnswer: id, attempt_id, question_id, selected_choice_ids (JSON, rỗng nếu bỏ qua), is_correct, timed_out, time_taken (giây). Unique (attempt_id, question_id).
- Xóa Quiz thì xóa theo Question, Choice, Attempt, AttemptAnswer (cascade).

## 6. Quy tắc nghiệp vụ

### Mã tham gia và mở/đóng
- Mã 6 ký tự in hoa, bảng ký tự bỏ 0, O, 1, I, L; sinh bằng secrets, kiểm tra trùng toàn hệ thống, có thể sinh lại. Tra mã không phân biệt hoa thường.
- Bộ đề nhận bài khi: is_open = True, đã tới open_at (nếu có), chưa quá close_at (nếu có), và có ít nhất 1 câu hỏi.

### Câu hỏi
- single và true_false: đúng 1 đáp án đúng. multiple: ít nhất 1 đáp án đúng. Mỗi câu 2–6 đáp án; true_false cố định hai đáp án "Đúng" và "Sai". Nội dung câu 1–1000 ký tự, mỗi đáp án 1–300 ký tự.
- Bộ đề đã có lượt làm bài thì chặn thêm/sửa/xóa/đổi thứ tự câu hỏi (HTTP 409 kèm hướng dẫn xóa kết quả trước). Vẫn sửa được tiêu đề, mô tả, thẻ và các cài đặt khác.

### Máy trạng thái làm bài (server là nguồn sự thật)
- Hằng số FEEDBACK_SECONDS = 3: thời gian xem phản hồi trước khi tự chuyển câu, dùng cho mọi câu, kể cả câu cuối.
- join tạo Attempt: xáo trộn thứ tự câu và đáp án (nếu bật) rồi lưu vào question_order và choice_orders; phase = question; question_started_at = null; feedback_started_at = null.
- state (hoặc next) ở phase question: nếu question_started_at còn null thì đặt bằng thời điểm hiện tại (giờ bắt đầu tính khi câu được gửi đi lần đầu); trả câu hỏi KHÔNG kèm is_correct, kèm seconds_left. Nếu đã quá hạn (vượt limit) mà chưa có answer nào thì tự ghi nhận không trả lời (timed_out = true, selected_choice_ids rỗng), đặt phase = feedback và feedback_started_at = thời điểm hiện tại, rồi trả feedback. Không có thời gian ân hạn.
- answer: chỉ nhận cho câu hiện tại ở phase question (miễn phase còn là question thì server vẫn nhận, để bù độ trễ mạng khi giao diện tự gửi lúc đồng hồ về 0). Tính time_taken ở server, tối đa bằng limit. Nếu gửi sau limit thì timed_out = true nhưng VẪN chấm đáp án đã chọn. choice_ids rỗng là hợp lệ, tính là không trả lời. Trả 400 khi: thiếu hẳn trường question_id hoặc choice_ids; choice_ids không phải mảng; có id không thuộc câu hiện tại; câu single hoặc true_false mà gửi nhiều hơn 1 id. Trả lời lại câu đã trả lời: 409. Ghi AttemptAnswer, đặt phase = feedback và feedback_started_at = thời điểm hiện tại, trả feedback gồm đáp án đúng.
- state ở phase feedback: trả lại feedback của câu hiện tại (không tạo thêm bản ghi), kèm feedback_seconds_left = max(0, FEEDBACK_SECONDS − (bây giờ − feedback_started_at)), tối đa FEEDBACK_SECONDS.
- next: chỉ hợp lệ ở phase feedback. Server KHÔNG chặn gọi sớm (đồng hồ 3 giây chỉ chạy ở giao diện). Tăng current_index, phase = question, question_started_at = null, feedback_started_at = null (giờ của câu kế tiếp chỉ bắt đầu khi câu đó được gửi đi, nên thời gian xem phản hồi không bị tính). Hết câu thì status = finished và tính score, time_spent, finished_at.
- Không có thao tác quay lại câu trước. Tải lại trang chỉ nhận lại đúng trạng thái hiện tại; không thể trả lời lại.
- Câu đúng khi tập đáp án chọn khớp hoàn toàn tập đáp án đúng (không chấm điểm một phần). Không chọn gì = sai; có chọn thì chấm theo lựa chọn, kể cả khi hết giờ. score = correct/total × 10, làm tròn 2 chữ số; time_spent = tổng time_taken.
- Học sinh không bao giờ nhận is_correct hay đáp án đúng của một câu trước khi trả lời xong (hoặc hết giờ) câu đó.
- Tải lại trang (F5) hoặc nhập lại mã khi đang xem phản hồi: giao diện lấy lại feedback và feedback_seconds_left từ state, thanh chờ tiếp tục đúng số giây còn lại; nếu đã hết thì tự gọi next ngay.

### Xếp hạng và kết quả
- Chỉ tính attempt đã finished. Mỗi device_id chỉ có MỘT dòng trong bảng xếp hạng của học sinh: lượt tốt nhất (score cao nhất, rồi time_spent thấp nhất, rồi finished_at sớm nhất). Sắp các dòng theo score giảm dần, rồi time_spent tăng dần, rồi finished_at tăng dần. Cùng score và time_spent thì chung hạng (1, 2, 2, 4). total_participants là số thiết bị đã hoàn thành; rank của người xem là hạng của dòng tốt nhất thuộc thiết bị của họ (is_me đánh dấu dòng đó), còn score, correct_answers, time_spent trong result là của chính lượt vừa làm. Bảng kết quả, thống kê và xuất file của giáo viên vẫn liệt kê MỌI lượt làm.
- Cuối bài học sinh chỉ xem điểm, số câu đúng, thời gian, hạng và bảng xếp hạng đầy đủ. KHÔNG có màn xem lại từng câu. Nếu show_ranking = False thì ẩn bảng xếp hạng.

### Tên và giới hạn lượt làm
- Tên học sinh: cắt khoảng trắng đầu/cuối, gộp khoảng trắng liên tiếp, 1–40 ký tự, bỏ ký tự điều khiển; cho phép bất kỳ nội dung nào khác và cho phép trùng.
- Làm lại KHÔNG giới hạn số lần (không có cài đặt allow_retake). device_id là uuid do trình duyệt tự sinh, lưu localStorage. join: nếu thiết bị đó đang có lượt in_progress của bộ đề thì tiếp tục lượt cũ (resumed = true, kể cả đóng tab rồi nhập lại mã); nếu không có (chưa làm hoặc lượt cũ đã nộp) thì tạo lượt mới. Không có lỗi "đã làm bộ đề này".
- Sự kiện tab_hidden chỉ tăng tab_switch_count để giáo viên xem, không chặn học sinh.

### Thư viện đề và phân quyền
- Bộ đề is_public = True (mặc định khi tạo) xuất hiện trong Thư viện cho mọi giáo viên xem. Sao chép (clone) tạo bản mới thuộc người sao chép: mã mới, is_public = False, source_quiz_id trỏ bản gốc, chép toàn bộ câu hỏi và đáp án (ảnh dùng chung đường dẫn). Chỉ chủ bộ đề và admin sửa/xóa bản gốc.
- Bộ đề mẫu được seed với chủ là admin, is_public = True.
- Giáo viên chỉ thao tác trên bộ đề của mình (bộ đề người khác trả 404). Giáo viên không có quyền nào của admin và không sửa được cấu hình hệ thống.
- Giáo viên bị khóa (is_active = False): không đăng nhập được, token cũ mất hiệu lực ngay (kiểm tra DB ở mỗi request), dữ liệu giữ nguyên. Khi xóa hẳn một giáo viên, admin chọn xóa hay chuyển bộ đề của họ sang admin.
- Chỉ có một admin, tạo bằng lệnh `flask create-admin` từ biến môi trường. Không có API nào tạo hay nâng quyền admin; đăng ký luôn tạo role teacher và bỏ qua mọi trường role gửi lên.

### Nhập/xuất Excel
- File mẫu .xlsx có cột: Câu hỏi | Loại (1 đáp án / nhiều đáp án / đúng-sai) | Đáp án A … Đáp án F | Đáp án đúng (chữ cái, cách nhau dấu phẩy, ví dụ A hoặc A,C) | Thời gian (giây). Nhập CSV cũng được. Dòng lỗi bị bỏ qua và trả về danh sách "dòng số – lỗi"; dòng hợp lệ vẫn được nhập.
- Xuất kết quả .xlsx và .csv: Tên | Điểm | Số câu đúng | Tổng câu | Thời gian | Số lần rời tab | Trạng thái | Thời điểm nộp.

## 7. API

### Auth
- POST /api/auth/register {username, email, password} → {message, access_token, user}
- POST /api/auth/login {username_or_email, password} (từ chối tài khoản admin)
- POST /api/auth/admin/login (chỉ nhận tài khoản admin)
- GET /api/auth/me (Bearer)

### Play (học sinh, không JWT; định danh bằng token của lượt làm bài)
- GET /api/play/lookup?code= → {quiz: {title, description, total_questions, question_time, is_open, message}}
- POST /api/play/join {code, name, device_id} → {attempt_token, quiz: {title, total_questions}, resumed}
- GET /api/play/<token>/state → một trong ba dạng:
  - {status: 'in_progress', phase: 'question', index, total, question: {id, type, content, image_url, choices: [{id, content}]}, time_limit, seconds_left}
  - {status: 'in_progress', phase: 'feedback', index, total, question: {id, type, content, image_url, choices: [{id, content}]}, feedback: {question_id, is_correct, timed_out, correct_choice_ids, selected_choice_ids}, is_last, feedback_seconds_left}
  - {status: 'finished'}
- POST /api/play/<token>/answer {question_id, choice_ids (mảng, có thể rỗng)} → {feedback, is_last, feedback_seconds_left}
- POST /api/play/<token>/next → dạng question hoặc {status: 'finished'}
- GET /api/play/<token>/result → {student_name, quiz_title, score, correct_answers, total_questions, time_spent, rank, total_participants, show_ranking}
- GET /api/play/<token>/ranking → {ranking: [{rank, name, score, correct_answers, time_spent, is_me}]}
- POST /api/play/<token>/event {type: 'tab_hidden'} → 204

### Teacher (JWT role teacher)
- GET, POST /api/teacher/quizzes; GET, PUT, DELETE /api/teacher/quizzes/<id> (GET kèm câu hỏi và đáp án đúng)
- POST /api/teacher/quizzes/<id>/regenerate-code; POST .../duplicate; PATCH .../publish {is_public}
- POST /api/teacher/quizzes/<id>/questions; PUT, DELETE /api/teacher/questions/<id>; PUT /api/teacher/quizzes/<id>/questions/order {ids: []}
- POST /api/teacher/quizzes/<id>/import (multipart); GET /api/teacher/import-template
- GET /api/teacher/quizzes/<id>/attempts; GET .../stats (số người làm, điểm trung bình, tỉ lệ sai từng câu); GET .../export?format=xlsx|csv
- DELETE /api/teacher/attempts/<id>; DELETE /api/teacher/quizzes/<id>/attempts (xóa toàn bộ kết quả)
- GET /api/teacher/library?search=&tag=&page= → {quizzes: [...], page, per_page, total}; per_page mặc định 12
- GET /api/teacher/library/<id>; POST /api/teacher/library/<id>/clone
- POST /api/teacher/uploads (multipart, trường file) → {url}; GET /api/uploads/<filename> (công khai)

### Admin (JWT role admin)
- GET /api/admin/stats
- GET /api/admin/teachers?search=&status=; PATCH /api/admin/teachers/<id> {is_active}; DELETE /api/admin/teachers/<id>?quizzes=delete|transfer
- GET /api/admin/quizzes?search=; PATCH /api/admin/quizzes/<id> {is_open, is_public}; DELETE /api/admin/quizzes/<id>
- GET /api/admin/attempts?search=&quiz_id=; DELETE /api/admin/attempts/<id>; POST /api/admin/attempts/bulk-delete {ids: []}

## 8. Giao diện

### Routes
- Học sinh: / (nhập mã và tên), /join/:code (mã điền sẵn), /play/:token, /result/:token.
- Giáo viên: /teacher/login, /teacher/register, /teacher (danh sách bộ đề), /teacher/quizzes/:id (soạn bộ đề), /teacher/quizzes/:id/results, /teacher/library, /teacher/library/:id.
- Admin: /admin/login, /admin, /admin/teachers, /admin/quizzes, /admin/attempts.
- Trang 404.

### Màn làm bài
- Mỗi lần tải trang (kể cả F5) LUÔN gọi GET state rồi render theo phase (question, feedback, finished → chuyển /result/:token). Không lưu câu hỏi hay trạng thái vào sessionStorage. Lỗi API: hiện thông báo tiếng Việt kèm nút "Thử lại", không để màn trắng.
- Thanh tiến độ "Câu x/y"; vòng tròn tím là đồng hồ đếm ngược duy nhất: số giây còn lại (làm tròn lên) ở giữa, KHÔNG có biểu tượng đồng hồ và không có chữ giờ nào khác ở chỗ nào trên màn hình. Vòng cạn dần tuyến tính, mượt (requestAnimationFrame hoặc CSS animation), hết đúng lúc số về 0. Deadline = thời điểm nhận seconds_left cộng seconds_left (không cộng dồn tick); quay lại tab thì đồng bộ lại với server. Khi còn ≤5 giây: số và vòng đổi đỏ đậm (#B91C1C) và rung nhẹ. Ở phase phản hồi, vòng ẩn đi.
- Thẻ đáp án lớn có chữ cái A–F, dùng các màu tím, xanh dương, cam, hồng (cùng hai màu phụ cho E, F). KHÔNG dùng xanh lá hoặc đỏ cho thẻ thường vì hai màu này dành riêng cho đúng/sai.
- Hình dạng thẻ: câu 1 đáp án (single, true_false) bo tròn góc lớn kèm chấm tròn chọn; câu nhiều đáp án hình chữ nhật bo 4px kèm ô vuông đánh dấu. Hình dạng giữ nguyên sau phản hồi.
- Luồng chung cho mọi câu:
  1) Chọn đáp án: chỉ hiện hiệu ứng "đang chọn" (phóng to nhẹ khoảng 3%, viền tím đậm, vầng sáng, biểu tượng đã chọn, không có chữ). Chưa hiện đúng/sai, chưa lộ đáp án đúng. Các thẻ khác giữ nguyên. Câu single và true_false chỉ giữ tối đa 1 thẻ được chọn (chọn thẻ mới thì thay thẻ cũ); câu multiple bật/tắt từng thẻ. Chạm thẻ KHÔNG gửi đáp án. Phím 1–6 và A–F để chọn.
  2) Nút "Chốt!" cố định một vị trí cuối khung: xám và khóa khi chưa chọn, tím khi đã chọn, Enter cũng chốt, chống bấm đúp, nhấp nháy nhẹ khi còn ≤5 giây. Bấm Chốt! hoặc đồng hồ về 0 thì gửi đáp án đang chọn (mảng rỗng nếu chưa chọn).
  3) Có phản hồi (thẻ nền nhạt, chữ đậm, dễ đọc; màu đậm chỉ dùng cho viền và biểu tượng, không tô cả thẻ):
     - Đúng đã chọn: nền xanh lá nhạt, viền liền xanh #15803D, ✓, nảy nhẹ.
     - Sai đã chọn: nền đỏ nhạt, viền liền đỏ #B91C1C, ✗, rung ngang ngắn.
     - Đúng nhưng chưa chọn (câu multiple, hoặc hết giờ không chọn gì, kể cả câu 1 đáp án): nền xanh nhạt, viền nét đứt xanh lá, ✓ rỗng và nhãn "Bỏ sót"; hết giờ không chọn gì thì không có thẻ đỏ.
     - Thẻ còn lại giữ nguyên, không làm mờ.
     - Hết giờ thì hiện "Hết giờ!". Không có phần giải thích.
  4) Không có nút "Câu tiếp": nút Chốt! được thay bằng thanh chạy ngược cùng vị trí, kèm chữ "Sang câu sau trong Ns". Thời gian lấy từ feedback_seconds_left của server (tối đa 3 giây), tính bằng mốc thời gian (không đếm tick) nên vẫn chạy đúng khi tab bị ẩn. Hết thì tự gọi POST next. Câu cuối hiện "Đang chuyển tới kết quả..." rồi sang /result/:token sau cùng khoảng thời gian đó.
- Không có nút quay lại; cảnh báo khi định rời trang; gửi sự kiện tab_hidden khi chuyển tab.

### Màn kết quả
- Điểm lớn, hạng, số câu đúng, thời gian; pháo giấy nếu vào top 3; bảng xếp hạng đầy đủ (dòng của mình nổi bật, cuộn được); nút "Làm bộ đề khác".

### Phong cách
- Đột phá, vui nhộn, tươi tắn; thiết kế desktop-first, đẹp nhất ở 1280px, responsive xuống 360px không tràn ngang, bo góc lớn, nút cao tối thiểu 44px, hiệu ứng nhỏ vui mắt.
- prefers-reduced-motion: bỏ phóng to, nảy, rung, nhấp nháy; vẫn giữ màu, viền, biểu tượng.
- Đúng/sai luôn kèm biểu tượng (không chỉ dựa vào màu); độ tương phản chữ tối thiểu 4.5:1 (kiểm tra cả chữ trắng trên chữ cái A–F và chữ đậm trên nền nhạt).
- Font hỗ trợ đầy đủ tiếng Việt, tự host bằng @fontsource.
- Mọi biến màu, cỡ chữ, bo góc nằm trong theme.css (đúng #15803D, sai #B91C1C); dùng Bootstrap 5 làm nền và ghi đè bằng biến CSS.
- Trang giáo viên và admin: gọn, bảng cuộn ngang trên điện thoại, xác nhận trước khi xóa, có trạng thái đang tải, trống và lỗi.

## 9. Bảo mật
- Giới hạn tần suất (Flask-Limiter): đăng nhập 10 lần/phút/IP, đăng ký 5 lần/giờ/IP, join và lookup 30 lần/phút/IP, answer 120 lần/phút/IP, event 60 lần/phút/IP.
- MAX_CONTENT_LENGTH 5 MB. Ảnh tải lên tối đa 2 MB, chỉ nhận png, jpg, webp, gif; kiểm tra chữ ký file (magic bytes), đặt tên file ngẫu nhiên, không nhận svg.
- JWT hết hạn sau 24 giờ; SECRET_KEY, JWT_SECRET_KEY lấy từ .env; CORS theo CORS_ORIGINS.
- Mật khẩu hash bằng werkzeug; không bao giờ trả password_hash. Mật khẩu admin tối thiểu 8 ký tự và khác 123456.
- Khi xuất Excel/CSV, ô bắt đầu bằng = + - @ thì thêm dấu nháy đơn phía trước (chống công thức độc hại).
- Frontend không dùng v-html; mọi dữ liệu người dùng nhập đều hiển thị dạng văn bản.