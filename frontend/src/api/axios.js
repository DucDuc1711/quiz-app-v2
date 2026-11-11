import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const api = axios.create({
  baseURL: '/api',
})

function isUnauthenticatedEndpoint(url) {
  if (!url) return false
  const cleanUrl = url.toLowerCase()
  return (
    cleanUrl === '/auth/login' ||
    cleanUrl === '/api/auth/login' ||
    cleanUrl === '/auth/register' ||
    cleanUrl === '/api/auth/register' ||
    cleanUrl.startsWith('/play/') ||
    cleanUrl.startsWith('/api/play/')
  )
}

api.interceptors.request.use((config) => {
  const store = useAuthStore()
  const url = config.url ? String(config.url) : ''
  
  if (store.token && !isUnauthenticatedEndpoint(url)) {
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

    if (status === 401 && !isUnauthenticatedEndpoint(url) && store.token) {
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