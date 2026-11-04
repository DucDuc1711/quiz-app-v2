# TIẾN ĐỘ DỰ ÁN

## Trạng thái
- Phase đang làm: P3 (P0, P1, P2 đã xong)
- Đang làm dở (file và việc kế tiếp): chưa bắt đầu P3

## Checklist
- [x] P0 Tài liệu đặc tả
- [x] P1 Backend nền tảng (models, auth, CLI, seed)
- [x] P2 Backend luồng làm bài (play, uploads)
- [ ] P3 Backend giáo viên và admin (CRUD, thư viện, import/export)
- [ ] P4 Frontend nền và phần học sinh
- [ ] P5 Frontend giáo viên
- [ ] P6 Frontend admin
- [ ] P7 Hoàn thiện (giao diện, điện thoại, kiểm thử, README)

## Quyết định / thay đổi so với đặc tả
- P0 được tạo thủ công bằng script setup-p0.bat (không qua Cline). Terminal dùng Windows CMD.
- extensions.py, models.py, utils.py, cli.py đặt tại backend/ root (không phải trong app/) theo cấu trúc thực tế.
- DATABASE_URL trong .env dùng đường dẫn tuyệt đối do Windows path có khoảng trắng.

## Lỗi đã biết
(chưa có)

## Cách chạy
- Kích hoạt venv: .venv\Scripts\activate
- Khởi tạo DB: flask db upgrade (hoặc flask db init + flask db migrate + flask db upgrade)
- Tạo admin: flask create-admin (đọc ADMIN_* từ .env)
- Seed dữ liệu mẫu: flask seed-samples (yêu cầu đã có admin)
- Chạy server: python run.py (cổng 5000)
- Chạy kiểm tra: pytest
