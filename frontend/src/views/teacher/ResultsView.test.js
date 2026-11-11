import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import ResultsView from '@/views/teacher/ResultsView.vue'

vi.mock('@/api/teacher', () => ({
  teacherApi: {
    getStats: vi.fn(),
    listAttempts: vi.fn(),
  },
}))

const routes = [
  { path: '/teacher/quizzes/:id/results', name: 'teacher-quiz-results', component: ResultsView, props: true },
  { path: '/teacher/quizzes/:id', name: 'teacher-quiz', component: { template: 'div' }, props: true },
]

function makeRouter(id) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes,
  })
  router.push(`/teacher/quizzes/${id}/results`)
  return router
}

describe('ResultsView', () => {
  let teacherApi

  beforeEach(async () => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.token = 'test-token'
    auth.user = { id: 1, role: 'teacher' }

    const mod = await import('@/api/teacher')
    teacherApi = mod.teacherApi
    teacherApi.getStats.mockReset()
    teacherApi.listAttempts.mockReset()
    teacherApi.getStats.mockResolvedValue({ data: { total_attempts: 1, questions: [] } })
    teacherApi.listAttempts.mockResolvedValue({ data: [] })
  })

  it('id hợp lệ (1): gọi getStats và listAttempts đúng 1 lần mỗi lần tải', async () => {
    const router = makeRouter(1)
    const wrapper = mount(ResultsView, {
      global: { plugins: [router] },
      props: { id: '1' },
    })
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    expect(teacherApi.getStats).toHaveBeenCalledWith('1')
    expect(teacherApi.listAttempts).toHaveBeenCalledWith('1')
    // Chỉ onMounted(load) gọi API (không còn watch immediate / load gọi lặp như cũ).
    expect(teacherApi.getStats).toHaveBeenCalled()
    expect(teacherApi.listAttempts).toHaveBeenCalled()
    wrapper.unmount()
  })

  it('id không phải số (abc): không gọi API, hiện lỗi đường dẫn không hợp lệ', async () => {
    const router = makeRouter('abc')
    const wrapper = mount(ResultsView, {
      global: { plugins: [router] },
      props: { id: 'abc' },
    })
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    expect(teacherApi.getStats).not.toHaveBeenCalled()
    expect(teacherApi.listAttempts).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Đường dẫn không hợp lệ')
    wrapper.unmount()
  })

  it('id <= 0 (0): không gọi API', async () => {
    const router = makeRouter(0)
    const wrapper = mount(ResultsView, {
      global: { plugins: [router] },
      props: { id: '0' },
    })
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    expect(teacherApi.getStats).not.toHaveBeenCalled()
    expect(teacherApi.listAttempts).not.toHaveBeenCalled()
    wrapper.unmount()
  })
})