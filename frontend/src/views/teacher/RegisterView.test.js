import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import RegisterView from '@/views/teacher/RegisterView.vue'

const mockRouterPush = vi.fn()

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
    replace: vi.fn(),
    currentRoute: { value: { path: '/', query: {}, params: {} } },
  }),
  useRoute: () => ({ path: '/', query: {}, params: {} }),
}))

describe('RegisterView', () => {
  let api

  beforeEach(async () => {
    setActivePinia(createPinia())
    mockRouterPush.mockReset()

    const mod = await import('@/api/axios')
    api = mod.default
    api.post.mockReset()
  })

  it('đăng ký thành công → chuyển /teacher, không ném lỗi', async () => {
    api.post.mockResolvedValueOnce({
      data: { access_token: 'tok123', user: { id: 1, role: 'teacher' } },
    })

    const wrapper = mount(RegisterView)
    await wrapper.find('input[placeholder="tên_đăng_nhập (4–30 ký tự)"]').setValue('giaovien')
    await wrapper.find('input[placeholder="ten@example.com"]').setValue('gv@example.com')
    await wrapper.find('input[placeholder="•••••••• (tối thiểu 8 ký tự)"]').setValue('matkhau123')
    await wrapper.find('input[placeholder="••••••••"]').setValue('matkhau123')
    await wrapper.find('form').trigger('submit.prevent')
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    expect(mockRouterPush).toHaveBeenCalledWith('/teacher')
    expect(wrapper.vm.loading).toBe(false)
    wrapper.unmount()
  })

  it('đăng ký thất bại → hiện lỗi đỏ, nút không kẹt "Đang xử lý..."', async () => {
    api.post.mockRejectedValueOnce({
      response: { data: { error: 'Tên đăng nhập đã tồn tại.' } },
    })

    const wrapper = mount(RegisterView)
    await wrapper.find('input[placeholder="tên_đăng_nhập (4–30 ký tự)"]').setValue('giaovien')
    await wrapper.find('input[placeholder="ten@example.com"]').setValue('gv@example.com')
    await wrapper.find('input[placeholder="•••••••• (tối thiểu 8 ký tự)"]').setValue('matkhau123')
    await wrapper.find('input[placeholder="••••••••"]').setValue('matkhau123')
    await wrapper.find('form').trigger('submit.prevent')
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    expect(wrapper.html()).toContain('Tên đăng nhập đã tồn tại.')
    expect(wrapper.vm.loading).toBe(false)
    expect(wrapper.find('button[type="submit"]').text()).toBe('Đăng ký')
    wrapper.unmount()
  })
})