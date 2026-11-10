// Helpers dùng chung cho các test Vitest (không dùng vi.mock vì nó bị hoisted)

import { setActivePinia, createPinia } from 'pinia'

export function setupPinia() {
  setActivePinia(createPinia())
}

// Tạo localStorage mock và gán vào window
export function mockLocalStorage() {
  const store = {}
  const localStorageMock = {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => { store[key] = String(value) },
    removeItem: (key) => { delete store[key] },
    clear: () => { Object.keys(store).forEach((k) => { delete store[k] }) },
  }
  Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
    writable: true,
  })
  return localStorageMock
}

// Tạo mock router đơn giản cho useRouter/useRoute
export function mockRouter() {
  const push = () => {}
  const replace = () => {}
  const currentRoute = { value: { path: '/', query: {}, params: {} } }
  return { push, replace, currentRoute }
}