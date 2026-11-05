# TIẾN ĐỘ DỰ ÁN

## Trạng thái
- Phase đang làm: P4 (P0, P1, P2,p3 đã xong)
- 


- Đã sửa lỗi thêm câu hỏi không lưu choices và thiếu validate theo spec (single/multiple/true_false, 2-6 đáp án, độ dài ký tự, ràng buộc đáp án đúng). Áp dụng cho thêm câu hỏi và cập nhật câu hỏi (PUT).
- Đã cập nhật GET /api/teacher/quizzes/<id> trả về đầy đủ thông tin bộ đề kèm danh sách câu hỏi và đáp án (is_correct).
- Đã sửa POST /api/play/<token>/next tính và trả `seconds_left` là số (không bị null) ở phase question.
- Đã sửa POST /api/play/<token>/answer trả 400 kèm thông báo "Thieu question_id hoac choice_ids." nếu thiếu trường.
- Đã viết test và chạy pytest toàn bộ xanh (dùng DB :memory:).

## Endpoint đã xong (P3)

Giao vien (JWT, role teacher, url_prefix /api/teacher):
- POST /quizzes — tao bo de (sinh access_code 6 ky tu)
- GET /quizzes — danh sach bo de cua giao vien
- GET /quizzes/<id> — chi tiet bo de kèm danh sach cau hoi va đap án (is_correct)
- DELETE /quizzes/<id> — xóa bo de
- PUT /quizzes/<id> — cap nhat bo de
- PATCH /quizzes/<id>/publish — cong khuyen/bo cong khuyen (is_public)
- PUT /quizzes/<id>/questions/order — sap xep thu tu cau hoi
- POST /quizzes/<id>/questions — them cau hoi
- DELETE /questions/<id> — xóa cau hoi
- PUT /questions/<id> — cap nhat cau hoi
- GET /quizzes/<id>/attempts — danh sach luot lam
- GET /quizzes/<id>/stats — thong ke (so nguoi lam, diem trung binh, ti le sai tung cau)
- GET /quizzes/<id>/export?format=xlsx|csv — xuat ket qua ra Excel/CSV
- GET /library — thu vien bo de cong khuyen (search, tag, phan trang)
- GET /library/<id> — chi tiet bo de trong thu vien
- POST /library/<id>/clone — sao chep bo de cong khuyen
- GET /import-template — tai file mau nhap
- POST /quizzes/<id>/import — nhap cau hoi tu file
- DELETE /attempts/<id> — xóa mot luot lam
- DELETE /quizzes/<id>/attempts — xóa toan bo ket qua cua bo de
- POST /quizzes/<id>/regenerate-code — sinh ma tham gia moi
- POST /quizzes/<id>/duplicate — sao chep bo de cua minh

Admin (JWT, role admin, url_prefix /api/admin):
- GET /stats
- GET /teachers
- PATCH /teachers/<id> {is_active}
- DELETE /teachers/<id>?quizzes=delete|transfer
- GET /quizzes
- PATCH /quizzes/<id> {is_open, is_public}
- DELETE /quizzes/<id>
- GET /attempts
- DELETE /attempts/<id>
- POST /attempts/bulk-delete {ids: []}

- Quyết định: Route teacher dùng `teacher_required` (chỉ role teacher), route admin dùng `admin_required` (chỉ role admin). Kiểm tra quyền qua DB tại mỗi request.
- Thay đổi: Cập nhật các test case để lấy access_token thông qua endpoint thật thay vì tự tạo token thủ công.
- Đã thêm test hồi quy kiểm tra phân quyền cho giáo viên và admin.

## Dang lam do
- P3: DA HOAN TAT. Da them day du cac route trong spec muc 7 (teacher: import, import-template, library/<id>, clone, attempts CRUD, stats chi tiet, export xlsx/csv, regenerate-code, duplicate, publish, questions/order; admin: PATCH teachers/<id>, GET/PATCH/DELETE quizzes, GET/DELETE/bulk-delete attempts). Da viet test chep tat ca endpoint Teacher va Admin. Chay pytest toan bo xanh (80 test, 0 fail) dung DB :memory:.
- DA sua loi exporter xuat tieu de cot lech spec muc 6 va bo sung test nhom: export tieu de tieng Viet, 409 khi da co luot lam, uploads, xoa giao vien transfer, PUT cau hop le.

## Checklist
- [x] P0 Tài liệu đặc tả
- [x] P1 Backend nền tảng (models, auth, CLI, seed)
- [x] P2 Backend luồng làm bài (play, uploads)
- [x] P3 Backend giáo viên và admin (CRUD, thư viện, import/export)
- [x] P4 Frontend nền và phần học sinh
- [ ] P5 Frontend giáo viên
- [ ] P6 Frontend admin
- [ ] P7 Hoàn thiện (giao diện, điện thoại, kiểm thử, README)

## Việc để lại cho P7
- Chuyển Query.get() sang db.session.get() để loại bỏ LegacyAPIWarning toàn bộ codebase
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
- Xuat ket qua dung tieu de tieng Viet theo spec muc 6 (Ten | Diem | So cau dung | Tong cau | Thoi gian | So lan roi tab | Trang thai | Thoi diem nop); cot Trang thai hien "Da nop" khi finished va "Dang lam" khi in_progress.

## Thiet ke giao dien (P4 — chot tu script `scripts/search.py --design-system` cua skill ui-ux-pro-max)

- Mau chinh: #6C5CE7 (tim); chu chon dap án A-F: tim #8B5CF6, xanh duong #2563EB, cam #EA580C, hong #DB2777 (+ #0891B2, #D97706 cho E-F). Xanh la #16A34A va do #DC2626 DUOC DU TRU CHO trang thai dung/sai — KHONG dung cho the dap an thuong.
- Nen: #FBFDFF; card: trang bo goc 28px, do dem nhẹ; nut it thieu 44px, co hover/active feedback.
- Font: Noto Sans Vietnamese (@fontsource, subset tieng Viet, tu host, khong can Internet).
- Layout: desktop-first 1280px; breakpoint 768px xep thanh mot cot; khung lam bai rong 900-1000px can giua; lưới đáp án 2 cot (1 cot duoi 768px).
- Huong ung: fade 220ms, hover translateY(-1px); tat het khi prefers-reduced-motion: reduce.
- Tuong tac may tinh: chon dap án bang phim 1-6 hoac A-F, Enter de chot/sang cau tiep.

## Lỗi đã biết
- Lỗi fixture test ghi đè / xóa DB thật:
  - **Nguyên nhân**: `create_app()` gọi `db.init_app(app)` trước khi các test fixture gán `app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"`. Do Flask-SQLAlchemy khởi tạo engine ngay tại `init_app()`, việc gán sau đó bị vô tác dụng và `db.drop_all()` cuối fixture đã xóa sạch các bảng trong CSDL thật (`backend/instance/quiz.db`).
  - **Cách sửa**: Cập nhật `create_app` hỗ trợ truyền object/dict cấu hình (dùng `TestingConfig` với URI `:memory:` và `TESTING=True`) áp dụng trước `db.init_app(app)`. Chuyển fixture `app` và `client` về `conftest.py` với chốt an toàn assert URI bắt đầu bằng `sqlite:///:memory:` trước mọi thao tác DB.

## Cách chạy

Backend (terminal 1):
- Kích hoạt venv: .venv\Scripts\activate
- Khởi tạo DB: flask db upgrade (hoặc flask db init + flask db migrate + flask db upgrade)
- Tạo admin: flask create-admin (đọc ADMIN_* từ .env)
- Seed dữ liệu mẫu: flask seed-samples (yêu cầu đã có admin)
- Chạy server: python run.py (cổng 5000)

Frontend (terminal 2, chạy song song với backend):
- cd /d frontend
- Cài đặt (lần đầu): npm install
- Chạy dev: npm run dev (mặc định cổng 5173, vite proxy /api sang http://127.0.0.1:5000)
- Truy cập: http://127.0.0.1:5173

Chạy kiểm tra backend: pytest
