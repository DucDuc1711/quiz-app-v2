import { defineStore } from 'pinia'

const TOKEN_KEY = 'quiz_teacher_token'
const USER_KEY = 'quiz_teacher_user'

function getStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch (_) {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || null,
    user: getStoredUser(),
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    isTeacher: (state) => state.user && state.user.role === 'teacher',
    isAdmin: (state) => state.user && state.user.role === 'admin',
  },
  actions: {
    async init() {
      try {
        const raw = localStorage.getItem(USER_KEY)
        this.user = raw ? JSON.parse(raw) : null
      } catch (_) {
        this.user = null
      }
      if (this.token) {
        try {
          const api = (await import('@/api/axios')).default
          const res = await api.get('/auth/me')
          if (res.data && res.data.user) {
            this.user = res.data.user
            localStorage.setItem(USER_KEY, JSON.stringify(this.user))
          }
        } catch (_) {
          this.clearAuth()
        }
      }
    },
    setAuth(token, user) {
      this.token = token
      this.user = user
      localStorage.setItem(TOKEN_KEY, token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    },
    clearAuth() {
      this.token = null
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
  },
})