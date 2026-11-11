import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import DashboardView from '@/views/teacher/DashboardView.vue'

vi.mock('@/api/teacher', () => ({
  teacherApi: {
    listQuizzes: vi.fn(),
    createQuiz: vi.fn(),
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
    teacherApi.createQuiz.mockReset()
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

  it('modal tạo: nhấn Tạo gọi API với tiêu đề đã nhập', async () => {
    teacherApi.listQuizzes.mockResolvedValueOnce({ data: [] })
    teacherApi.createQuiz.mockResolvedValueOnce({ data: { quiz: { id: 9 } } })

    const wrapper = mount(DashboardView, {
      attachTo: document.body,
    })
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    // Mở modal: nút "Tạo bộ đề mới"
    const createBtn = wrapper.findAll('button').find((b) => b.text() === 'Tạo bộ đề mới')
    await createBtn.trigger('click')
    await wrapper.vm.$nextTick()

    // Nhập tiêu đề vào ô
    const input = wrapper.find('.q-dialog input.q-field-control')
    await input.setValue('Bộ đề kiểm tra')
    await wrapper.vm.$nextTick()

    // Nhấn nút Tạo
    await wrapper.find('.q-dialog .q-btn-primary').trigger('click')
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    expect(teacherApi.createQuiz).toHaveBeenCalledWith({ title: 'Bộ đề kiểm tra' })
    wrapper.unmount()
  })

  it('modal tạo: bấm vào ô nhập KHÔNG đóng hộp (overlay chỉ dùng @click.self)', async () => {
    teacherApi.listQuizzes.mockResolvedValueOnce({ data: [] })

    const wrapper = mount(DashboardView, {
      attachTo: document.body,
    })
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    await wrapper.findAll('button').find((b) => b.text() === 'Tạo bộ đề mới').trigger('click')
    await wrapper.vm.$nextTick()

    const overlay = wrapper.find('.q-dialog-overlay')
    const input = wrapper.find('.q-dialog input.q-field-control')
    // Nhấn vào chính ô nhập (trong nội dung hộp, không phải lớp nền)
    await input.trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.q-dialog').exists()).toBe(true)
    wrapper.unmount()
  })

  it('modal tạo: bấm lớp nền (@click.self) thì đóng hộp', async () => {
    teacherApi.listQuizzes.mockResolvedValueOnce({ data: [] })

    const wrapper = mount(DashboardView, {
      attachTo: document.body,
    })
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    await wrapper.findAll('button').find((b) => b.text() === 'Tạo bộ đề mới').trigger('click')
    await wrapper.vm.$nextTick()

    const overlay = wrapper.find('.q-dialog-overlay')
    await overlay.trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.q-dialog').exists()).toBe(false)
    wrapper.unmount()
  })
})