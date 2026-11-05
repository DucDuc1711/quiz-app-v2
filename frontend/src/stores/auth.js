import { defineStore } from 'pinia'

const TOKEN_KEY = 'quiz_token'
const USER_KEY = 'quiz_user'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || null,
    user: null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    isTeacher: (state) => state.user && state.user.role === 'teacher',
    isAdmin: (state) => state.user && state.user.role === 'admin',
  },
  actions: {
    init() {
      try {
        this.user = JSON.parse(localStorage.getItem(USER_KEY) || 'null')
      } catch (_) {
        this.user = null
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