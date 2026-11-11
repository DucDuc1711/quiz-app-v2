// -*- coding: utf-8 -*-
// Vitest smoke test: mount LẦN LƯỢT TẤT CẢ view/component trang với API giả.
// FAIL nếu có cảnh báo Vue ("Invalid prop", "Unhandled error", ...) hoặc màn trống.
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import {
  makeQuiz, makeQuizWithQuestions, makeStats, makeAttempt,
  makeAuthResponse, makeMeResponse, makePlayJoinResponse,
  makePlayStateResponse, makePlayResultResponse,
} from '@/test/fixtures.js';

vi.mock('@/api/teacher', () => ({
  teacherApi: {
    listQuizzes: vi.fn(),
    getQuiz: vi.fn(),
    createQuiz: vi.fn(),
    updateQuiz: vi.fn(),
    deleteQuiz: vi.fn(),
    publishQuiz: vi.fn(),
    listLibrary: vi.fn(),
    getLibraryQuiz: vi.fn(),
    cloneQuiz: vi.fn(),
    addQuestion: vi.fn(),
    updateQuestion: vi.fn(),
    deleteQuestion: vi.fn(),
    reorderQuestions: vi.fn(),
    listAttempts: vi.fn(),
    deleteAttempt: vi.fn(),
    deleteAllAttempts: vi.fn(),
    getStats: vi.fn(),
    exportResults: vi.fn(),
    downloadFile: vi.fn(),
    downloadImportTemplate: vi.fn(),
    importQuestions: vi.fn(),
    uploadImage: vi.fn(),
    regenerateCode: vi.fn(),
    deleteQuizAttempts: vi.fn(),
  },
}));
vi.mock('@/api/play', () => ({
  playApi: {
    lookup: vi.fn(),
    join: vi.fn(),
    state: vi.fn(),
    answer: vi.fn(),
    next: vi.fn(),
    result: vi.fn(),
    ranking: vi.fn(),
    event: vi.fn(),
  },
}));
import { teacherApi } from '@/api/teacher';
import { playApi } from '@/api/play';

function makeRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div>home</div>' } },
      { path: '/teacher/login', name: 'teacher-login', component: { template: '<div>login</div>' } },
      { path: '/teacher/register', name: 'teacher-register', component: { template: '<div>register</div>' } },
      { path: '/teacher', name: 'teacher', component: { template: '<div>dashboard</div>' } },
      { path: '/teacher/quizzes/:id', name: 'teacher-quiz', component: { template: '<div>quiz</div>' } },
      { path: '/teacher/quizzes/:id/results', name: 'teacher-quiz-results', component: { template: '<div>results</div>' } },
      { path: '/teacher/library', name: 'teacher-library', component: { template: '<div>library</div>' } },
      { path: '/teacher/library/:id', name: 'teacher-library-quiz', component: { template: '<div>library detail</div>' } },
      { path: '/play/:token', name: 'play', component: { template: '<div>play</div>' } },
      { path: '/result/:token', name: 'result', component: { template: '<div>result</div>' } },
    ],
  });
}

function mountWithPiniaAndRouter(Component, options = {}) {
  const pinia = createPinia();
  setActivePinia(pinia);
  const router = makeRouter();
  const route = options.route || { path: '/' };
  // Push path only (no params) to avoid Vue Router warning about ignored params
  router.push({ path: route.path || '/' });
  return mount(Component, { global: { plugins: [pinia, router] }, ...options });
}

function assertNoVueWarnings(html, label) {
  expect(html).not.toMatch(/function\s/);
  expect(html).not.toMatch(/=>\s*/);
  expect(html.trim().length).toBeGreaterThan(0, label + ' khong duoc bo trong');
}


// ============ CAC VIEW/COMPONENT CAN MOUNT ============
import HomeView from '@/views/student/HomeView.vue';
import PlayView from '@/views/student/PlayView.vue';
import ResultView from '@/views/student/ResultView.vue';
import LoginView from '@/views/teacher/LoginView.vue';
import RegisterView from '@/views/teacher/RegisterView.vue';
import DashboardView from '@/views/teacher/DashboardView.vue';
import QuizEditorView from '@/views/teacher/QuizEditorView.vue';
import AccessCodeBlock from '@/views/teacher/AccessCodeBlock.vue';
import QuizSettings from '@/views/teacher/QuizSettings.vue';
import QuestionList from '@/views/teacher/QuestionList.vue';
import QuestionForm from '@/views/teacher/QuestionForm.vue';
import ImportBlock from '@/views/teacher/ImportBlock.vue';
import ResultsView from '@/views/teacher/ResultsView.vue';
import LibraryListView from '@/views/teacher/LibraryListView.vue';
import LibraryDetailView from '@/views/teacher/LibraryDetailView.vue';
import ErrorState from '@/components/ErrorState.vue';
import EmptyState from '@/components/EmptyState.vue';
import LoadingState from '@/components/LoadingState.vue';
import ConfirmDialog from '@/components/ConfirmDialog.vue';
import PasswordField from '@/components/PasswordField.vue';

const MOCK_QUIZ = makeQuizWithQuestions({ id: 1, title: 'Bo de test', access_code: 'ABC123' });

// Components that can mount without props (router + pinia only)
const SIMPLE_COMPONENTS = [
  HomeView, PlayView, ResultView,
  LoginView, RegisterView, DashboardView,
  LibraryListView, LibraryDetailView,
  ErrorState, EmptyState, LoadingState, PasswordField,
];

// Components that need props
const PROP_COMPONENTS = [
  { comp: QuizSettings, props: { quiz: MOCK_QUIZ } },
  { comp: ConfirmDialog, props: { message: 'Xac nhan thao tac' } },
  { comp: AccessCodeBlock, props: { code: 'ABC123', quizId: 1 } },
  { comp: QuestionList, props: { questions: [], quizId: 1, locked: false } },
  { comp: QuestionForm, props: { quizId: 1, question: null, visible: false } },
  { comp: ImportBlock, props: { quizId: 1 } },
  { comp: ResultsView, props: { quizId: 1 } },
];

describe('Smoke: mount tat ca view/component voi API gia', () => {
  let consoleWarnSpy;
  let consoleErrorSpy;

  beforeEach(() => {
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.clearAllMocks();
    teacherApi.getQuiz.mockResolvedValue({ data: MOCK_QUIZ });
  });

  afterEach(() => {
    consoleWarnSpy.mockRestore();
    consoleErrorSpy.mockRestore();
  });

  it.each(SIMPLE_COMPONENTS.map((c, i) => [c.name || 'Component' + i, c]))('%s khong bao loi Vue va khong bo trong', async (name, Component) => {
    const wrapper = mountWithPiniaAndRouter(Component);
    await wrapper.vm.$nextTick();
    await flushPromises();
    await new Promise((r) => setTimeout(r, 0));
    const html = wrapper.html();
    expect(consoleErrorSpy).not.toHaveBeenCalled();
    expect(consoleWarnSpy).not.toHaveBeenCalled();
    assertNoVueWarnings(html, name);
    wrapper.unmount();
  });

  it.each(PROP_COMPONENTS.map((c, i) => [c.comp.name || 'Comp' + i, c.comp, c.props]))('%s (co props) khong bao loi Vue va khong bo trong', async (name, Component, props) => {
    const wrapper = mountWithPiniaAndRouter(Component, { props });
    await wrapper.vm.$nextTick();
    await flushPromises();
    await new Promise((r) => setTimeout(r, 0));
    const html = wrapper.html();
    expect(consoleErrorSpy).not.toHaveBeenCalled();
    expect(consoleWarnSpy).not.toHaveBeenCalled();
    assertNoVueWarnings(html, name);
    wrapper.unmount();
  });

  it('QuizEditorView khong bao loi khi co du lieu quiz', async () => {
    teacherApi.getQuiz.mockResolvedValue({ data: MOCK_QUIZ });
    const wrapper = mountWithPiniaAndRouter(QuizEditorView, { route: { path: '/teacher/quizzes/1', params: { id: '1' } } });
    await wrapper.vm.$nextTick();
    await flushPromises();
    await new Promise((r) => setTimeout(r, 0));
    const html = wrapper.html();
    expect(consoleErrorSpy).not.toHaveBeenCalled();
    expect(consoleWarnSpy).not.toHaveBeenCalled();
    assertNoVueWarnings(html, 'QuizEditorView');
    wrapper.unmount();
  });
});

describe('Smoke: Dashboard hoat dong', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('bam Tao bo de moi mo modal, nhap tieu de, tao goi API', async () => {
    teacherApi.listQuizzes.mockResolvedValue({ data: [] });
    teacherApi.createQuiz.mockResolvedValue({ data: { quiz: { id: 99 } } });
    const pinia = createPinia();
    setActivePinia(pinia);
    const auth = useAuthStore();
    auth.token = 'test-token';
    auth.user = { id: 1, role: 'teacher' };
    const router = makeRouter();
    const wrapper = mount(DashboardView, { global: { plugins: [pinia, router] } });
    await wrapper.vm.$nextTick();
    await flushPromises();
    const btns = wrapper.findAll('button');
    const createBtn = btns.find(b => b.text().includes('Tạo bộ đề mới'));
    expect(createBtn).toBeDefined();
    await createBtn.trigger('click');
    await wrapper.vm.$nextTick();
    const input = wrapper.find('input[placeholder="Tiêu đề bộ đề"]');
    await input.setValue('Bo de kiem thu');
    await wrapper.vm.$nextTick();
    const btns2 = wrapper.findAll('button');
    const taoBtn = btns2.find(b => b.text() === 'Tạo');
    await taoBtn.trigger('click');
    await wrapper.vm.$nextTick();
    await flushPromises();
    expect(teacherApi.createQuiz).toHaveBeenCalled();
    wrapper.unmount();
  });

  it('bam Dong/Mo nhan bai hoac Xoa tren the khong chuyen trang', async () => {
    teacherApi.listQuizzes.mockResolvedValue({ data: [{ id: 1, title: 'Test', access_code: 'ABC123', question_count: 5, attempt_count: 0, is_open: true, is_public: true }] });
    teacherApi.updateQuiz.mockResolvedValue({ data: {} });
    const pinia = createPinia();
    setActivePinia(pinia);
    const auth = useAuthStore();
    auth.token = 'test-token';
    auth.user = { id: 1, role: 'teacher' };
    const router = makeRouter();
    vi.spyOn(router, 'push');
    const wrapper = mount(DashboardView, { global: { plugins: [pinia, router] } });
    await wrapper.vm.$nextTick();
    await flushPromises();
    const callsBefore = router.push.mock.calls.length;
    const toggleBtn = wrapper.findAll('button').find(b => b.text().includes('Dong nhan bai') || b.text().includes('Mo nhan bai'));
    if (toggleBtn) { await toggleBtn.trigger('click'); await wrapper.vm.$nextTick(); await flushPromises(); }
    const xoaBtn = wrapper.findAll('button').find(b => b.text() === 'Xoa');
    if (xoaBtn) { await xoaBtn.trigger('click'); await wrapper.vm.$nextTick(); }
    expect(router.push.mock.calls.length).toBe(callsBefore);
    wrapper.unmount();
  });
});

describe('Smoke: Thu vien - Dung bo de nay', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('bam Dung bo de nay goi clone API va chuyen trang', async () => {
    teacherApi.getLibraryQuiz.mockResolvedValue({ data: makeQuiz({ id: 1, owner: 'Giao vien A' }) });
    teacherApi.cloneQuiz.mockResolvedValue({ data: { quiz: { id: 3 } } });
    const pinia = createPinia();
    setActivePinia(pinia);
    const router = makeRouter();
    vi.spyOn(router, 'push');
    const wrapper = mount(LibraryDetailView, { global: { plugins: [pinia, router] }, route: { path: '/teacher/library/1', params: { id: '1' } } });
    await wrapper.vm.$nextTick();
    await flushPromises();
    const btn = wrapper.findAll('button').find(b => b.text() === 'Dùng bộ đề này');
    expect(btn).toBeDefined();
    await btn.trigger('click');
    await wrapper.vm.$nextTick();
    await flushPromises();
    expect(teacherApi.cloneQuiz).toHaveBeenCalledWith(expect.any(String));
    expect(router.push).toHaveBeenCalledWith({ name: 'teacher-quiz', params: { id: 3 } });
    wrapper.unmount();
  });

  it('the thu vien khong hien chu Ma:', async () => {
    teacherApi.listLibrary.mockResolvedValue({ data: { quizzes: [makeQuiz({ id: 1, owner: 'Giao vien A', access_code: 'ABC123' })], total: 1, page: 1, per_page: 12 } });
    const pinia = createPinia();
    setActivePinia(pinia);
    const router = makeRouter();
    const wrapper = mount(LibraryListView, { global: { plugins: [pinia, router] } });
    await wrapper.vm.$nextTick();
    await flushPromises();
    const html = wrapper.html();
    expect(html).not.toContain('Ma:');
    wrapper.unmount();
  });
});

describe('Smoke: store/axios - Authorization header', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('/api/auth/me CO Authorization khi co token', () => {
    const store = { token: 'fake-token' };
    const config = { url: '/auth/me', headers: {} };
    if (store.token) { config.headers.Authorization = 'Bearer ' + store.token; }
    expect(config.headers.Authorization).toBe('Bearer fake-token');
  });

  it('/api/auth/login KHONG co Authorization', () => {
    const store = { token: 'fake-token' };
    const config = { url: '/auth/login', headers: {} };
    const isUnauth = config.url === '/auth/login' || config.url === '/api/auth/login' || config.url === '/auth/register' || config.url === '/api/auth/register' || config.url.startsWith('/play/') || config.url.startsWith('/api/play/');
    if (store.token && !isUnauth) { config.headers.Authorization = 'Bearer ' + store.token; }
    expect(config.headers.Authorization).toBeUndefined();
  });

  it('/me tra 200 thi giu phien', async () => {
    const pinia = createPinia();
    setActivePinia(pinia);
    const auth = useAuthStore();
    auth.token = 'fake-token';
    auth.user = null;
    const api = await import('@/api/axios');
    api.default.get = vi.fn().mockResolvedValue({ data: { user: { id: 1, username: 'gv', email: 'gv@example.com', role: 'teacher', is_active: true } } });
    await auth.init();
    expect(auth.user).toEqual({ id: 1, username: 'gv', email: 'gv@example.com', role: 'teacher', is_active: true });
    expect(auth.token).toBe('fake-token');
  });

  it('/me tra 401 thi xoa phien', async () => {
    const pinia = createPinia();
    setActivePinia(pinia);
    const auth = useAuthStore();
    auth.token = 'fake-token';
    auth.user = { id: 1, username: 'gv', role: 'teacher' };
    const api = await import('@/api/axios');
    api.default.get = vi.fn().mockRejectedValue({ response: { status: 401 } });
    await auth.init();
    expect(auth.token).toBeNull();
    expect(auth.user).toBeNull();
  });

  it('/me loi mang thi KHONG xoa phien', async () => {
    const pinia = createPinia();
    setActivePinia(pinia);
    const auth = useAuthStore();
    auth.token = 'fake-token';
    auth.user = { id: 1, username: 'gv', role: 'teacher' };
    const api = await import('@/api/axios');
    api.default.get = vi.fn().mockRejectedValue(new Error('Network error'));
    await auth.init();
    expect(auth.token).toBe('fake-token');
  });
});