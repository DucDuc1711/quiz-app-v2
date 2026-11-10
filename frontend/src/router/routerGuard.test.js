import { createRouter, createWebHistory } from 'vue-router'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { setupPinia } from '@/test/helpers'

const MockComponent = { template: '<div/>' }

function createTestRouter() {
  const routes = [
    { path: '/teacher/login', name: 'teacher-login', component: MockComponent },
    { path: '/teacher/register', name: 'teacher-register', component: MockComponent },
    { path: '/teacher', name: 'teacher', component: MockComponent },
    { path: '/admin/login', name: 'admin-login', component: MockComponent },
  ]
  const router = createRouter({
    history: createWebHistory(),
    routes,
  })
  router.beforeEach((to, from, next) => {
    const auth = useAuthStore()
    const isTeacherRoute = to.path.startsWith('/teacher')
    const isLoginOrRegister = to.name === 'teacher-login' || to.name === 'teacher-register'

    if (isTeacherRoute) {
      if (auth.isAuthenticated) {
        if (auth.isAdmin) {
          next({ name: 'admin-login' })
          return
        }
        if (isLoginOrRegister) {
          next({ name: 'teacher' })
          return
        }
        next()
        return
      }
      if (isLoginOrRegister) {
        next()
        return
      }
      next({ name: 'teacher-login', query: { redirect: to.fullPath } })
      return
    }

    next()
  })
  return router
}

describe('router guard', () => {
  it('chưa đăng nhập vào /teacher → chuyển /teacher/login?redirect=/teacher', async () => {
    setupPinia()
    const auth = useAuthStore()
    auth.token = null
    auth.user = null

    const router = createTestRouter()
    await router.push('/teacher')
    expect(router.currentRoute.value.path).toBe('/teacher/login')
    expect(router.currentRoute.value.query.redirect).toBe('/teacher')
  })

  it('đã đăng nhập vào /teacher/login → chuyển /teacher', async () => {
    setupPinia()
    const auth = useAuthStore()
    auth.token = 'token'
    auth.user = { id: 1, role: 'teacher' }

    const router = createTestRouter()
    await router.push('/teacher/login')
    expect(router.currentRoute.value.name).toBe('teacher')
  })

  it('đã đăng nhập vào /teacher/register → chuyển /teacher', async () => {
    setupPinia()
    const auth = useAuthStore()
    auth.token = 'token'
    auth.user = { id: 1, role: 'teacher' }

    const router = createTestRouter()
    await router.push('/teacher/register')
    expect(router.currentRoute.value.name).toBe('teacher')
  })

  it('tài khoản admin vào khu giáo viên bị chặn /admin/login', async () => {
    setupPinia()
    const auth = useAuthStore()
    auth.token = 'token'
    auth.user = { id: 1, role: 'admin' }

    const router = createTestRouter()
    await router.push('/teacher')
    expect(router.currentRoute.value.name).toBe('admin-login')
  })

  it('đã đăng nhập teacher vào /teacher → vào được', async () => {
    setupPinia()
    const auth = useAuthStore()
    auth.token = 'token'
    auth.user = { id: 1, role: 'teacher' }

    const router = createTestRouter()
    await router.push('/teacher')
    expect(router.currentRoute.value.name).toBe('teacher')
  })
})