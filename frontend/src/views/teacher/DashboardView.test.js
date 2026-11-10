import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import DashboardView from '@/views/teacher/DashboardView.vue'

vi.mock('@/api/teacher', () => ({
  teacherApi: {
    listQuizzes: vi.fn(),
  },
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    currentRoute: { value: { path: '/', query: {}, params: {} } },
  }),
  useRoute: () => ({ path: '/', query: {}, params: {} }),
}))

describe('DashboardView', () => {
  let teacherApi

  beforeEach(async () => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.token = 'test-token'
    auth.user = { id: 1, role: 'teacher' }

    const mod = await import('@/api/teacher')
    teacherApi = mod.teacherApi
    teacherApi.listQuizzes.mockReset()
  })

  it('API trả lỗi → hiện ErrorState có dấu, không ném lỗi chưa bắt', async () => {
    teacherApi.listQuizzes.mockRejectedValueOnce({
      response: { data: { error: 'Không tải được danh sách.' } },
    })

    const wrapper = mount(DashboardView)
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    expect(wrapper.html()).toContain('Có lỗi xảy ra')
    expect(wrapper.html()).toContain('Thử lại')
    expect(wrapper.find('.q-error-message').text()).toContain('Không tải được danh sách.')
    wrapper.unmount()
  })

  it('API thành công → không hiện ErrorState', async () => {
    teacherApi.listQuizzes.mockResolvedValueOnce({
      data: [{ id: 1, title: 'Test Quiz', access_code: 'ABC123', question_count: 5, attempt_count: 0, is_open: true, is_public: true }],
    })

    const wrapper = mount(DashboardView)
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    expect(wrapper.html()).not.toContain('Có lỗi xảy ra')
    expect(wrapper.html()).toContain('Test Quiz')
    wrapper.unmount()
  })
})