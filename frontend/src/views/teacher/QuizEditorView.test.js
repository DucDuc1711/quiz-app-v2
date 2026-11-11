import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import QuizEditorView from '@/views/teacher/QuizEditorView.vue'

vi.mock('@/api/teacher', () => ({
  teacherApi: {
    getQuiz: vi.fn(),
  },
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
  useRoute: () => ({ path: '/teacher/quizzes/1', query: {}, params: { id: '1' } }),
}))

describe('QuizEditorView', () => {
  let teacherApi

  beforeEach(async () => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.token = 'test-token'
    auth.user = { id: 1, role: 'teacher' }

    const mod = await import('@/api/teacher')
    teacherApi = mod.teacherApi
    teacherApi.getQuiz.mockReset()
  })

  it('attempt_count > 0: hiện cảnh báo khóa và nút Thêm câu hỏi bị disabled', async () => {
    teacherApi.getQuiz.mockResolvedValue({
      data: {
        id: 1,
        title: 'Bộ đề mẫu',
        access_code: 'ABC123',
        attempt_count: 2,
        question_count: 3,
        questions: [
          { id: 1, type: 'single', content: 'Câu 1?', choices: [], order_num: 1 },
        ],
      },
    })

    const wrapper = mount(QuizEditorView)
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    // Mở tab Câu hỏi (nút Thêm câu hỏi chỉ render ở tab này)
    const tabQ = wrapper.findAll('button.q-editor-tab').find((b) => b.text() === 'Câu hỏi')
    await tabQ.trigger('click')
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    expect(wrapper.text()).toContain('Cảnh báo')
    expect(wrapper.text()).toContain('2 lượt làm bài')
    expect(wrapper.text()).toContain('Xóa kết quả để chỉnh sửa')

    // Nút Thêm câu hỏi bị disabled khi khóa
    const addBtn = wrapper.findAll('button.q-btn-primary').find((b) => b.text().includes('Thêm câu hỏi'))
    expect(addBtn.exists()).toBe(true)
    expect(addBtn.attributes('disabled')).toBeDefined()

    // Dòng số câu hỏi ở thẻ danh sách (khóa): hiện "3 câu hỏi" qua question_count
    expect(wrapper.text()).toContain('3 câu hỏi')
    wrapper.unmount()
  })

  it('attempt_count = 0: không hiện cảnh báo, nút Thêm câu hỏi bật', async () => {
    teacherApi.getQuiz.mockResolvedValue({
      data: {
        id: 1,
        title: 'Bộ đề mới',
        access_code: 'XYZ999',
        attempt_count: 0,
        question_count: 0,
        questions: [],
      },
    })

    const wrapper = mount(QuizEditorView)
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    expect(wrapper.text()).not.toContain('Cảnh báo')
    const addBtn = wrapper.find('button.q-btn-primary')
    expect(addBtn.attributes('disabled')).toBeUndefined()
    wrapper.unmount()
  })
})