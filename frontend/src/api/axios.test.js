import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('axios', () => {
  let requestInterceptor
  let responseInterceptor

  const mockAxiosInstance = {
    interceptors: {
      request: { use: vi.fn((fn) => { requestInterceptor = fn }) },
      response: { use: vi.fn((fulfilled, rejected) => { responseInterceptor = rejected }) },
    },
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
  }

  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
    },
    __mockAxiosInstance: mockAxiosInstance,
    __getRequestInterceptor: () => requestInterceptor,
    __getResponseInterceptor: () => responseInterceptor,
  }
})

describe('axios interceptor', () => {
  let store
  let requestInterceptor
  let responseInterceptor

  beforeEach(async () => {
    setActivePinia(createPinia())
    const { useAuthStore } = await import('@/stores/auth')
    store = useAuthStore()

    vi.clearAllMocks()

    // Import axios to trigger the interceptor setup
    await import('@/api/axios')

    // Get the interceptors from the mock
    const axiosMock = await import('axios')
    requestInterceptor = axiosMock.__getRequestInterceptor()
    responseInterceptor = axiosMock.__getResponseInterceptor()
  })

  it('should add Authorization header for teacher routes', () => {
    store.token = 'test-token'
    const config = { url: '/api/teacher/quizzes', headers: {} }
    const result = requestInterceptor(config)
    expect(result.headers.Authorization).toBe('Bearer test-token')
  })

  it('should NOT add Authorization header for auth login', () => {
    store.token = 'test-token'
    const config = { url: '/api/auth/login', headers: {} }
    const result = requestInterceptor(config)
    expect(result.headers.Authorization).toBeUndefined()
  })

  it('should NOT add Authorization header for play routes', () => {
    store.token = 'test-token'
    const config = { url: '/api/play/join', headers: {} }
    const result = requestInterceptor(config)
    expect(result.headers.Authorization).toBeUndefined()
  })

  it('should handle 401 on non-login endpoints by clearing auth', async () => {
    store.token = 'test-token'
    const error = {
      response: { status: 401 },
      config: { url: '/api/teacher/quizzes' },
    }
    store.clearAuth = vi.fn()
    window.dispatchEvent = vi.fn()

    await expect(responseInterceptor(error)).rejects.toEqual(error)
    expect(store.clearAuth).toHaveBeenCalled()
    expect(window.dispatchEvent).toHaveBeenCalled()
  })

  it('should NOT clear auth on 401 for login endpoints', async () => {
    const error = {
      response: { status: 401 },
      config: { url: '/api/auth/login' },
    }
    store.clearAuth = vi.fn()

    await expect(responseInterceptor(error)).rejects.toEqual(error)
    expect(store.clearAuth).not.toHaveBeenCalled()
  })
})