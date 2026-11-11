import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import App from './App.vue'

vi.mock('@/api/axios', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { user: { id: 1, role: 'teacher', username: 'giaovien' } } }),
    interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
  },
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', name: 'home', component: { template: 'div' } },
    { path: '/teacher', name: 'teacher', component: { template: 'div' } },
    { path: '/teacher/library', name: 'teacher-library', component: { template: 'div' } },
  ],
})

describe('App navbar', () => {
  beforeEach(async () => {
    router.push('/')
    await router.isReady()
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.token = 'test-token'
    auth.user = { id: 1, role: 'teacher', username: 'giaovien' }
  })

  it('trên "/" khi đã đăng nhập giáo viên: hiển thị "Bộ đề của tôi", "Thư viện", tên giáo viên, Đăng xuất', async () => {
    const wrapper = mount(App, {
      global: {
        plugins: [router],
      },
      attachTo: document.body,
    })
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    const html = wrapper.html()
    expect(html).toContain('Bộ đề của tôi')
    expect(html).toContain('Thư viện')
    expect(html).toContain('Giáo viên (giaovien)')
    expect(html).toContain('Đăng xuất')
    // Không còn chỉ "Trang chủ" và Đăng xuất mà thiếu liên kết giáo viên
    wrapper.unmount()
  })
})