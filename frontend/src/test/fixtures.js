// Fixture dữ liệu mẫu cho Vitest smoke test (hình dạng JSON thật theo backend/app/routes).
// Không cần kết nối backend thật.

export function makeQuiz(overrides = {}) {
  return {
    id: 1,
    owner_id: 1,
    title: 'Bộ đề mẫu',
    description: 'Mô tả bộ đề mẫu.',
    access_code: 'ABC123',
    question_time: 30,
    is_open: true,
    is_public: true,
    tags: 'toán, trial',
    question_count: 2,
    attempt_count: 0,
    ...overrides,
  };
}

export function makeQuestion(overrides = {}) {
  return {
    id: 1,
    quiz_id: 1,
    type: 'single',
    content: 'Câu hỏi mẫu?',
    time_limit: 30,
    image_url: null,
    order_num: 1,
    choices: [
      { id: 1, content: 'A', is_correct: true, order_num: 1 },
      { id: 2, content: 'B', is_correct: false, order_num: 2 },
    ],
    ...overrides,
  };
}

export function makeQuizWithQuestions(overrides = {}) {
  return {
    ...makeQuiz(overrides),
    questions: [makeQuestion()],
  };
}

export function makeStats(overrides = {}) {
  return {
    total_attempts: 0,
    finished_attempts: 0,
    average_score: 0,
    questions: [],
    ...overrides,
  };
}

export function makeAttempt(overrides = {}) {
  return {
    id: 1,
    quiz_id: 1,
    student_name: 'Học sinh mẫu',
    score: 8,
    correct_answers: 4,
    total_questions: 5,
    time_spent: 120,
    tab_switch_count: 0,
    status: 'submitted',
    finished_at: new Date().toISOString(),
    ...overrides,
  };
}

export function makeAuthResponse(overrides = {}) {
  return {
    message: 'Đăng nhập thành công.',
    access_token: 'fake-access-token',
    user: { id: 1, username: 'gvtest', email: 'gvtest@example.com', role: 'teacher' },
    ...overrides,
  };
}

export function makeMeResponse(overrides = {}) {
  return {
    message: 'Lấy thông tin người dùng thành công.',
    user: { id: 1, username: 'gvtest', email: 'gvtest@example.com', role: 'teacher', is_active: true },
    ...overrides,
  };
}

export function makePlayJoinResponse(overrides = {}) {
  return {
    message: 'Tham gia bộ đề thành công.',
    attempt_token: 'attempt-token-123',
    quiz: { id: 1, title: 'Bộ đề mẫu', total_questions: 2, question_time: 30 },
    ...overrides,
  };
}

export function makePlayStateResponse(overrides = {}) {
  return {
    status: 'active',
    phase: 'question',
    index: 0,
    total: 2,
    time_limit: 30,
    seconds_left: 30,
    is_last: false,
    question: makeQuestion(),
    ...overrides,
  };
}

export function makePlayResultResponse(overrides = {}) {
  return {
    student_name: 'Học sinh mẫu',
    score: 8,
    correct_answers: 4,
    total_questions: 5,
    time_spent: 120,
    rank: 1,
    show_ranking: true,
    ...overrides,
  };
}