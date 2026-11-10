import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const store = useAuthStore()
  const url = config.url ? String(config.url) : ''
  const isAuthEndpoint = url.startsWith('/auth/') || url.startsWith('/api/auth/')
  const isPlayEndpoint = url.startsWith('/play/') || url.startsWith('/api/play/')
  
  if (store.token && !isAuthEndpoint && !isPlayEndpoint) {
    config.headers.Authorization = `Bearer ${store.token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const store = useAuthStore()
    const status = error.response && error.response.status
    const url = error.config && error.config.url ? String(error.config.url) : ''
    const isLoginEndpoint = url.endsWith('/auth/login') || url.endsWith('/auth/admin/login')

    if (status === 401 && !isLoginEndpoint && store.token) {
      const role = store.user && store.user.role
      store.clearAuth()
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('auth-logout', { detail: { role } }))
      }
    }
    return Promise.reject(error)
  }
)

export default api