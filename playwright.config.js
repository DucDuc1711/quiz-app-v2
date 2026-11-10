// -*- coding: utf-8 -*-
// Cấu hình Playwright E2E cho Quiz App v2
// KHÔNG bao giờ chạm DB thật: backend dùng e2e.db (trong .gitignore, xóa sau chạy)
import { defineConfig, devices } from '@playwright/test'

const BACKEND_PORT = 5100
const FRONTEND_PORT = 5273
const E2E_DB = 'backend/instance/e2e.db'

// Assert: backend KHÔNG được dùng quiz.db (DB thật)
if (process.env.DATABASE_URL && process.env.DATABASE_URL.includes('quiz.db')) {
  throw new Error('E2E KHÔNG được sử dụng quiz.db! Hãy đặt DATABASE_URL trỏ e2e.db.')
}

export default defineConfig({
  testDir: './frontend/tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: 'html',

  webServer: [
    {
      // Backend: Flask trên cổng 5100, DATABASE_URL trỏ e2e.db
      // Chạy flask db upgrade trước để tạo bảng, sau đó mới flask run
      command: `cd /d "backend" && set DATABASE_URL=sqlite:///instance/e2e.db && set FLASK_APP=run.py && .venv\\Scripts\\python.exe -m flask db upgrade && .venv\\Scripts\\python.exe -m flask run --host=127.0.0.1 --port=${BACKEND_PORT}`,
      port: BACKEND_PORT,
      timeout: 120 * 1000,
      reuseExistingServer: !process.env.CI,
    },
    {
      // Frontend: Vite dev server trên cổng 5273, VITE_API_TARGET trỏ backend cổng 5100
      command: `cd /d "frontend" && set VITE_API_TARGET=http://127.0.0.1:${BACKEND_PORT} && npx vite --port ${FRONTEND_PORT}`,
      port: FRONTEND_PORT,
      timeout: 120 * 1000,
      reuseExistingServer: !process.env.CI,
    },
  ],

  use: {
    baseURL: `http://127.0.0.1:${FRONTEND_PORT}`,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
