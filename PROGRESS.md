# TIẾN ĐỘ DỰ ÁN

## Trạng thái
- Phase đang làm: P3 (P0, P1, P2 đã xong)
- 

- đang sửa lỗi p3
- 


- Đã sửa lỗi thêm câu hỏi không lưu choices và thiếu validate theo spec (single/multiple/true_false, 2-6 đáp án, độ dài ký tự, ràng buộc đáp án đúng). Áp dụng cho thêm câu hỏi và cập nhật câu hỏi (PUT).
- Đã cập nhật GET /api/teacher/quizzes/<id> trả về đầy đủ thông tin bộ đề kèm danh sách câu hỏi và đáp án (is_correct).
- Đã sửa POST /api/play/<token>/next tính và trả `seconds_left` là số (không bị null) ở phase question.
- Đã sửa POST /api/play/<token>/answer trả 400 kèm thông báo "Thieu question_id hoac choice_ids." nếu thiếu trường.
- Đã viết test và chạy pytest toàn bộ xanh (dùng DB :memory:).

- Quyết định: Route teacher dùng `teacher_required` (chỉ role teacher), route admin dùng `admin_required` (chỉ role admin). Kiểm tra quyền qua DB tại mỗi request.
- Thay đổi: Cập nhật các test case để lấy access_token thông qua endpoint thật thay vì tự tạo token thủ công.
- Đã thêm test hồi quy kiểm tra phân quyền cho giáo viên và admin.

## Dang lam do
- P3: DA HOAN TAT. Da them day du cac route trong spec muc 7 (teacher: import, import-template, library/<id>, clone, attempts CRUD, stats chi tiet, export xlsx/csv, regenerate-code, duplicate, publish, questions/order; admin: PATCH teachers/<id>, GET/PATCH/DELETE quizzes, GET/DELETE/bulk-delete attempts). Da viet test chep tat ca endpoint Teacher va Admin. Chay pytest toan bo xanh (71 test, 0 fail) dung DB :memory:.

## Checklist
- [x] P0 Tài liệu đặc tả
- [x] P1 Backend nền tảng (models, auth, CLI, seed)
- [x] P2 Backend luồng làm bài (play, uploads)
- [x] P3 Backend giáo viên và admin (CRUD, thư viện, import/export)
- [ ] P4 Frontend nền và phần học sinh
- [ ] P5 Frontend giáo viên
- [ ] P6 Frontend admin
- [ ] P7 Hoàn thiện (giao diện, điện thoại, kiểm thử, README)

## Việc để lại cho P7
- Chuyển Query.get() sang db.session.get() để消除 LegacyAPIWarning toàn bộ codebase
- thống nhất thông báo tiếng Việt có dấu trong auth.py và utils.py (chỉ còn thiếu một vài chuỗi khác)
- Bổ sung test cho các endpoint còn thiếu (theo spec mục 7)
- Hoàn thiện coverage cho toàn bộ API endpoints

## Quyết định / thay đổi so với đặc tả
- Route chi tiet giao vien chi nhan role teacher; admin goi /api/teacher/* tra 403.
- Thong thu vien tra object phan trang {quizzes, page, per_page, total}; per_page mac dinh 12.
- P0 duoc tao thu cong bang script setup-p0.bat (khong qua Cline). Terminal dung Windows CMD.
- extensions.py, models.py, utils.py, cli.py dat tai backend/ root (khong phai trong app/) theo cau truc thuc te.
- DATABASE_URL trong .env duong dan tuyet do vi Windows path co khoang trang.
- Da sua fixture test: cho create_app nhan config_object (vi du TestingConfig) va ap dung cau truoc khi db.init_app duoc goi. Tao backend/tests/conftest.py tap trung fixture app va client ketch chot an toan assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///:memory:") truoc db.create_all() va db.drop_all().

## Lỗi đã biết
- Lỗi fixture test ghi đè / xóa DB thật:
  - **Nguyên nhân**: `create_app()` gọi `db.init_app(app)` trước khi các test fixture gán `app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"`. Do Flask-SQLAlchemy khởi tạo engine ngay tại `init_app()`, việc gán sau đó bị vô tác dụng và `db.drop_all()` cuối fixture đã xóa sạch các bảng trong CSDL thật (`backend/instance/quiz.db`).
  - **Cách sửa**: Cập nhật `create_app` hỗ trợ truyền object/dict cấu hình (dùng `TestingConfig` với URI `:memory:` và `TESTING=True`) áp dụng trước `db.init_app(app)`. Chuyển fixture `app` và `client` về `conftest.py` với chốt an toàn assert URI bắt đầu bằng `sqlite:///:memory:` trước mọi thao tác DB.

## Cách chạy
- Kích hoạt venv: .venv\Scripts\activate
- Khởi tạo DB: flask db upgrade (hoặc flask db init + flask db migrate + flask db upgrade)
- Tạo admin: flask create-admin (đọc ADMIN_* từ .env)
- Seed dữ liệu mẫu: flask seed-samples (yêu cầu đã có admin)
- Chạy server: python run.py (cổng 5000)
- Chạy kiểm tra: pytest
