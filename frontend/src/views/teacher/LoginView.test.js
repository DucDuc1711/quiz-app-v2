import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/teacher/LoginView.vue'

const mockRouterPush = vi.fn()
const mockRouterReplace = vi.fn()

vi.mock('@/api/axios', () => ({
  default: {
    post: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockRouterPush,
    replace: mockRouterReplace,
    currentRoute: { value: { path: '/', query: {}, params: {} } },
  }),
  useRoute: () => ({ path: '/', query: {}, params: {} }),
}))

describe('LoginView', () => {
  let api

  beforeEach(async () => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.token = null
    auth.user = null
    mockRouterPush.mockReset()
    mockRouterReplace.mockReset()

    const mod = await import('@/api/axios')
    api = mod.default
    api.post.mockReset()
  })

  it('đăng nhập thành công → chuyển /teacher, không ném lỗi', async () => {
    api.post.mockResolvedValueOnce({
      data: { access_token: 'tok123', user: { id: 1, role: 'teacher' } },
    })

    const wrapper = mount(LoginView)
    await wrapper.find('input[placeholder="tên đăng nhập hoặc email"]').setValue('giaovien')
    await wrapper.find('input[aria-label="Mật khẩu"]').setValue('matkhau123')
    await wrapper.find('form').trigger('submit.prevent')
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    expect(mockRouterPush).toHaveBeenCalledWith('/teacher')
    expect(wrapper.vm.loading).toBe(false)
    wrapper.unmount()
  })

  it('đăng nhập thất bại → hiện lỗi đỏ, nút không kẹt "Đang xử lý..."', async () => {
    api.post.mockRejectedValueOnce({
      response: { data: { error: 'Sai tài khoản hoặc mật khẩu.' } },
    })

    const wrapper = mount(LoginView)
    await wrapper.find('input[placeholder="tên đăng nhập hoặc email"]').setValue('giaovien')
    await wrapper.find('input[aria-label="Mật khẩu"]').setValue('sai123')
    await wrapper.find('form').trigger('submit.prevent')
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    expect(wrapper.html()).toContain('Sai tài khoản hoặc mật khẩu.')
    expect(wrapper.vm.loading).toBe(false)
    expect(wrapper.find('button[type="submit"]').text()).toBe('Đăng nhập')
    wrapper.unmount()
  })
})