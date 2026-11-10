// -*- coding: utf-8 -*-
// E2E tests cho Quiz App v2 — Chạy trên trình duyệt thật (Chromium)
// KHÔNG chạm DB thật: backend dùng e2e.db (cổng 5100), frontend cổng 5273
import { test, expect } from '@playwright/test'

const VIETNAMESE_UNSIGNED_PATTERNS = [
  /\bco\s+loi\b/i,
  /\bthu\s+lai\b/i,
  /\bkhong\b/i,
  /\bdang\s+nhap\b/i,
  /\bdang\s+ky\b/i,
  /\bmat\s+khau\b/i,
  /\btai\s+khoan\b/i,
  /\bda\s+ton\s+tai\b/i,
  /\bchinh\s+xac\b/i,
  /\bten\s+dang\b/i,
  /\bbo\s+de\b/i,
  /\bgiao\s+vien\b/i,
  /\btrang\s+chu\b/i,
  /\bhoac\b/i,
]

function assertNoUnsignedVietnamese(text, label) {
  for (const p of VIETNAMESE_UNSIGNED_PATTERNS) {
    if (p.test(text)) {
      throw new Error(`${label}: tìm thấy chuỗi tiếng Việt không dấu "${text.match(p)[0]}" trong: "${text.slice(0, 80)}"`)
    }
  }
}

test.describe('Quiz App E2E', () => {
  test.beforeEach(({ page }) => {
    const consoleErrors = []
    const pageErrors = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text())
    })
    page.on('pageerror', (err) => pageErrors.push(err.message))
    page._consoleErrors = consoleErrors
    page._pageErrors = pageErrors
  })

  test.afterEach(async ({ page }) => {
    const allErrors = [...(page._consoleErrors || []), ...(page._pageErrors || [])]
    if (allErrors.length > 0) console.error('LỖI TRÌNH DUYỆT:', allErrors)
    expect(allErrors.length).toBe(0)
  })

  // --- Test b: Đăng ký giáo viên mới ---
  test('đăng ký giáo viên mới, chuyển /teacher, F5 vẫn đăng nhập', async ({ page }) => {
    await page.goto('/teacher/register')
    await page.fill('input[autocomplete="username"]', 'GvE2E')
    await page.fill('input[autocomplete="email"]', 'GVE2E@GMAIL.COM')
    await page.fill('input[autocomplete="new-password"]', 'MatKhau123')
    await page.fill('input[autocomplete="new-password"]:nth-of-type(2)', 'MatKhau123')
    await page.click('button:has-text("Đăng ký")')
    await expect(page).toHaveURL('**/teacher')
    await expect(page.locator('nav')).toContainText('GvE2E')
    await expect(page.locator('main')).toContainText('Chưa có bộ đề nào')
    await page.reload()
    await expect(page).toHaveURL('**/teacher')
    await expect(page.locator('nav')).toContainText('GvE2E')
  })

  // --- Test c: Vào /teacher/library ---
  test('Vào /teacher/library tải được, không lỗi', async ({ page }) => {
    await page.goto('/teacher/register')
    await page.fill('input[autocomplete="username"]', 'GvLib')
    await page.fill('input[autocomplete="email"]', 'gvl@example.com')
    await page.fill('input[autocomplete="new-password"]', 'MatKhau123')
    await page.fill('input[autocomplete="new-password"]:nth-of-type(2)', 'MatKhau123')
    await page.click('button:has-text("Đăng ký")')
    await expect(page).toHaveURL('**/teacher')
    await page.click('a:has-text("Thư viện")')
    await expect(page).toHaveURL('**/teacher/library')
    await expect(page.locator('main')).not.toContainText('Có lỗi xảy ra')
  })

  // --- Test d: Đăng xuất, đăng nhập sai, đăng nhập đúng ---
  test('đăng xuất, đăng nhập sai báo lỗi, nút bấm lại được; đăng nhập đúng vào /teacher', async ({ page }) => {
    await page.goto('/teacher/register')
    await page.fill('input[autocomplete="username"]', 'GvLogin')
    await page.fill('input[autocomplete="email"]', 'gvlogin@example.com')
    await page.fill('input[autocomplete="new-password"]', 'MatKhau123')
    await page.fill('input[autocomplete="new-password"]:nth-of-type(2)', 'MatKhau123')
    await page.click('button:has-text("Đăng ký")')
    await expect(page).toHaveURL('**/teacher')
    await page.click('button:has-text("Đăng xuất"), a:has-text("Đăng xuất")')
    await expect(page).toHaveURL('**/')
    await page.click('a:has-text("Đăng nhập giáo viên")')
    await expect(page).toHaveURL('**/teacher/login')
    await page.fill('input[autocomplete="username"]', 'gvlogin')
    await page.fill('input[autocomplete="current-password"]', 'MatKhauSai123')
    await page.click('button:has-text("Đăng nhập")')
    await expect(page.locator('.q-form-error, .q-error')).toContainText('Tài khoản hoặc mật khẩu không chính xác')
    const loginBtn = page.locator('button:has-text("Đăng nhập")')
    await expect(loginBtn).not.toBeDisabled()
    await expect(loginBtn).not.toContainText('Đang xử lý')
    await page.fill('input[autocomplete="current-password"]', 'MatKhau123')
    await page.click('button:has-text("Đăng nhập")')
    await expect(page).toHaveURL('**/teacher')
    await page.click('button:has-text("Đăng xuất"), a:has-text("Đăng xuất")')
    await page.click('a:has-text("Đăng nhập giáo viên")')
    await page.fill('input[autocomplete="username"]', 'GVLOGIN@EXAMPLE.COM')
    await page.fill('input[autocomplete="current-password"]', 'MatKhau123')
    await page.click('button:has-text("Đăng nhập")')
    await expect(page).toHaveURL('**/teacher')
  })

  // --- Test e: Nút Hiện/Ẩn mật khẩu cùng hàng với ô nhập ---
  test('nút Hiện/Ẩn mật khẩu cùng hàng với ô nhập', async ({ page }) => {
    await page.goto('/teacher/login')
    const input = page.locator('input[autocomplete="current-password"]')
    const toggleBtn = page.locator('button.q-password-toggle')
    await expect(input).toBeVisible()
    await expect(toggleBtn).toBeVisible()
    const inputBox = await input.boundingBox()
    const btnBox = await toggleBtn.boundingBox()
    expect(Math.abs(inputBox.y - btnBox.y)).toBeLessThan(10)
  })

  // --- Test f: Tạo bộ đề qua giao diện ---
  test('tạo bộ đề qua giao diện, thêm câu qua API, bật is_open', async ({ page, request }) => {
    await page.goto('/teacher/register')
    await page.fill('input[autocomplete="username"]', 'GvCreate')
    await page.fill('input[autocomplete="email"]', 'gvcreate@example.com')
    await page.fill('input[autocomplete="new-password"]', 'MatKhau123')
    await page.fill('input[autocomplete="new-password"]:nth-of-type(2)', 'MatKhau123')
    await page.click('button:has-text("Đăng ký")')
    await expect(page).toHaveURL('**/teacher')
    const token = await page.evaluate(() => localStorage.getItem('quiz_teacher_token'))
    await page.click('button:has-text("Tạo bộ đề mới")')
    await page.fill('input[placeholder="Tiêu đề bộ đề"]', 'Bộ đề E2E')
    await page.click('button:has-text("Tạo")')
    await expect(page).toHaveURL(/\/teacher\/quizzes\/[^\/]+/)
    const quizId = page.url().split('/').pop()
    const apiRes = await request.post(`/api/teacher/quizzes/${quizId}/questions`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        type: 'single',
        content: 'Câu hỏi E2E?',
        choices: [
          { content: 'A', is_correct: true },
          { content: 'B', is_correct: false },
        ],
      },
    })
    expect(apiRes.status()).toBe(201)
    const openBtn = page.locator('button:has-text("Mở nhận bài"), button:has-text("Đóng nhận bài")')
    if ((await openBtn.count()) > 0) await openBtn.click()
  })

  // --- Test g: Học sinh làm bài, vào kết quả, làm lại cùng thiết bị ---
  test('học sinh làm bài, vào kết quả, làm lại cùng thiết bị', async ({ page, request }) => {
    await page.goto('/teacher/register')
    await page.fill('input[autocomplete="username"]', 'GvPlay')
    await page.fill('input[autocomplete="email"]', 'gvplay@example.com')
    await page.fill('input[autocomplete="new-password"]', 'MatKhau123')
    await page.fill('input[autocomplete="new-password"]:nth-of-type(2)', 'MatKhau123')
    await page.click('button:has-text("Đăng ký")')
    await expect(page).toHaveURL('**/teacher')
    const token = await page.evaluate(() => localStorage.getItem('quiz_teacher_token'))
    const createRes = await request.post('/api/teacher/quizzes', {
      headers: { Authorization: `Bearer ${token}` },
      data: { title: 'Quiz E2E Play', question_time: 30, is_public: true },
    })
    const quizId = (await createRes.json()).quiz.id
    await request.post(`/api/teacher/quizzes/${quizId}/questions`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        type: 'single',
        content: 'Câu duy nhất?',
        choices: [
          { content: 'Đúng', is_correct: true },
          { content: 'Sai', is_correct: false },
        ],
      },
    })
    await request.patch(`/api/teacher/quizzes/${quizId}/publish`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { is_open: true },
    })
    const quizRes = await request.get(`/api/teacher/quizzes/${quizId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const accessCode = (await quizRes.json()).quiz.access_code
    const studentPage = await page.context().newPage()
    await studentPage.goto('/')
    await studentPage.fill('input[maxlength="6"]', accessCode)
    await studentPage.fill('input[placeholder="Tên của bạn"]', 'Học Sinh E2E')
    await studentPage.click('button:has-text("Tham gia bộ đề")')
    await studentPage.waitForURL(/\/play\//)
    const attemptToken = studentPage.url().split('/').pop()
    await studentPage.click('.q-option-card, .q-options >> nth=0')
    await studentPage.click('button:has-text("Chốt!")')
    await studentPage.waitForURL(/\/result\//)
    await expect(studentPage.locator('.q-score-big')).toBeVisible()
    await studentPage.goto('/')
    await studentPage.fill('input[maxlength="6"]', accessCode)
    await studentPage.fill('input[placeholder="Tên của bạn"]', 'Học Sinh E2E')
    await studentPage.click('button:has-text("Tham gia bộ đề")')
    await studentPage.waitForURL(/\/play\//)
    await studentPage.click('.q-option-card, .q-options >> nth=0')
    await studentPage.click('button:has-text("Chốt!")')
    await studentPage.waitForURL(/\/result\//)
    await expect(studentPage.locator('.q-score-big')).toBeVisible()
    await studentPage.close()
  })

  // --- Test h: Giáo viên vào trang Kết quả thấy 2 lượt làm ---
  test('giáo viên vào trang Kết quả thấy 2 lượt làm', async ({ page, request }) => {
    await page.goto('/teacher/register')
    await page.fill('input[autocomplete="username"]', 'GvResults')
    await page.fill('input[autocomplete="email"]', 'gvresults@example.com')
    await page.fill('input[autocomplete="new-password"]', 'MatKhau123')
    await page.fill('input[autocomplete="new-password"]:nth-of-type(2)', 'MatKhau123')
    await page.click('button:has-text("Đăng ký")')
    await expect(page).toHaveURL('**/teacher')
    const token = await page.evaluate(() => localStorage.getItem('quiz_teacher_token'))
    const createRes = await request.post('/api/teacher/quizzes', {
      headers: { Authorization: `Bearer ${token}` },
      data: { title: 'Quiz E2E Results', question_time: 30, is_public: true },
    })
    const quizId = (await createRes.json()).quiz.id
    await request.post(`/api/teacher/quizzes/${quizId}/questions`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        type: 'single',
        content: 'Câu cho kết quả?',
        choices: [
          { content: 'Đúng', is_correct: true },
          { content: 'Sai', is_correct: false },
        ],
      },
    })
    await request.patch(`/api/teacher/quizzes/${quizId}/publish`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { is_open: true },
    })
    const quizRes = await request.get(`/api/teacher/quizzes/${quizId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const accessCode = (await quizRes.json()).quiz.access_code
    for (let i = 0; i < 2; i++) {
      const sp = await page.context().newPage()
      await sp.goto('/')
      await sp.fill('input[maxlength="6"]', accessCode)
      await sp.fill('input[placeholder="Tên của bạn"]', `Học Sinh ${i + 1}`)
      await sp.click('button:has-text("Tham gia bộ đề")')
      await sp.waitForURL(/\/play\//)
      await sp.click('.q-option-card, .q-options >> nth=0')
      await sp.click('button:has-text("Chốt!")')
      await sp.waitForURL(/\/result\//)
      await sp.close()
    }
    await page.click('a:has-text("Thư viện")')
    await page.click(`a[href*="/teacher/quizzes/${quizId}/results"]`)
    await expect(page).toHaveURL(/\/teacher\/quizzes\/[^\/]+\/results/)
    await expect(page.locator('table')).toContainText('Học Sinh 1')
    await expect(page.locator('table')).toContainText('Học Sinh 2')
  })

  // --- Test i: Quét chữ không dấu ---
  const PAGES_TO_SCAN = [
    '/',
    '/teacher/login',
    '/teacher/register',
    '/teacher',
    '/teacher/library',
  ]

  for (const path of PAGES_TO_SCAN) {
    test(`quét chữ không dấu: ${path}`, async ({ page }) => {
      await page.goto('/teacher/register')
      await page.fill('input[autocomplete="username"]', 'GvScanX')
      await page.fill('input[autocomplete="email"]', 'gvscanx@example.com')
      await page.fill('input[autocomplete="new-password"]', 'MatKhau123')
      await page.fill('input[autocomplete="new-password"]:nth-of-type(2)', 'MatKhau123')
      await page.click('button:has-text("Đăng ký")')
      await expect(page).toHaveURL('**/teacher')
      await page.goto(path)
      await page.waitForTimeout(2000)
      const bodyText = await page.locator('body').innerText()
      assertNoUnsignedVietnamese(bodyText, `Trang ${path}`)
    })
  }

  test('quét chữ không dấu: /teacher/quizzes/:id và /teacher/quizzes/:id/results', async ({ page, request }) => {
    await page.goto('/teacher/register')
    await page.fill('input[autocomplete="username"]', 'GvScanY')
    await page.fill('input[autocomplete="email"]', 'gvcscany@example.com')
    await page.fill('input[autocomplete="new-password"]', 'MatKhau123')
    await page.fill('input[autocomplete="new-password"]:nth-of-type(2)', 'MatKhau123')
    await page.click('button:has-text("Đăng ký")')
    await expect(page).toHaveURL('**/teacher')
    const token = await page.evaluate(() => localStorage.getItem('quiz_teacher_token'))
    const createRes = await request.post('/api/teacher/quizzes', {
      headers: { Authorization: `Bearer ${token}` },
      data: { title: 'Quiz Scan', question_time: 30, is_public: true },
    })
    const quizId = (await createRes.json()).quiz.id
    await request.post(`/api/teacher/quizzes/${quizId}/questions`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        type: 'single',
        content: 'Câu scan?',
        choices: [
          { content: 'A', is_correct: true },
          { content: 'B', is_correct: false },
        ],
      },
    })
    await page.goto(`/teacher/quizzes/${quizId}`)
    const detailText = await page.locator('body').innerText()
    assertNoUnsignedVietnamese(detailText, 'Trang chi tiết quiz')
    await page.click(`a[href*="/teacher/quizzes/${quizId}/results"]`)
    await page.waitForURL(/\/teacher\/quizzes\/[^\/]+\/results/)
    const resultsText = await page.locator('body').innerText()
    assertNoUnsignedVietnamese(resultsText, 'Trang kết quả quiz')
  })
})