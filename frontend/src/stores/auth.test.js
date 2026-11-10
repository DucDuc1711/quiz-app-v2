// Mock localStorage before any imports
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
})

// Mock axios
vi.mock('@/api/axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}))

import { setActivePinia, createPinia } from 'pinia'

describe('useAuthStore', () => {
  let useAuthStore

  beforeEach(async () => {
    setActivePinia(createPinia())
    localStorageMock.getItem.mockReset()
    localStorageMock.setItem.mockReset()
    localStorageMock.removeItem.mockReset()
    localStorageMock.clear.mockReset()
    
    // Reset modules to re-import store with fresh localStorage mock
    vi.resetModules()
    const authModule = await import('@/stores/auth')
    useAuthStore = authModule.useAuthStore
  })

  it('should initialize with token from localStorage', () => {
    localStorageMock.getItem.mockImplementation(key => {
      if (key === 'quiz_teacher_token') return 'stored-token'
      if (key === 'quiz_teacher_user') return JSON.stringify({ id: 1, username: 'test' })
      return null
    })
    const store = useAuthStore()
    expect(store.token).toBe('stored-token')
    expect(store.user).toEqual({ id: 1, username: 'test' })
  })

  it('should initialize with null when no localStorage data', () => {
    localStorageMock.getItem.mockReturnValue(null)
    const store = useAuthStore()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
  })

  it('should set auth and store in localStorage', () => {
    const store = useAuthStore()
    store.setAuth('new-token', { id: 2, username: 'test2' })
    expect(store.token).toBe('new-token')
    expect(store.user).toEqual({ id: 2, username: 'test2' })
    expect(localStorageMock.setItem).toHaveBeenCalledWith('quiz_teacher_token', 'new-token')
    expect(localStorageMock.setItem).toHaveBeenCalledWith('quiz_teacher_user', JSON.stringify({ id: 2, username: 'test2' }))
  })

  it('should clear auth and remove from localStorage', () => {
    const store = useAuthStore()
    store.setAuth('token', { id: 1 })
    store.clearAuth()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('quiz_teacher_token')
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('quiz_teacher_user')
  })

  it('should have correct getters', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    store.setAuth('token', { id: 1, role: 'teacher' })
    expect(store.isAuthenticated).toBe(true)
    expect(store.isTeacher).toBe(true)
    expect(store.isAdmin).toBe(false)
    store.clearAuth()
    store.setAuth('token', { id: 2, role: 'admin' })
    expect(store.isTeacher).toBe(false)
    expect(store.isAdmin).toBe(true)
  })
})