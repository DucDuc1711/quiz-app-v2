import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/student/HomeView.vue'
import PlayView from '@/views/student/PlayView.vue'
import ResultView from '@/views/student/ResultView.vue'
import NotFoundView from '@/views/NotFoundView.vue'
import ComingSoonView from '@/views/ComingSoonView.vue'
import { useAuthStore } from '@/stores/auth'
import TeacherLoginView from '@/views/teacher/LoginView.vue'
import TeacherRegisterView from '@/views/teacher/RegisterView.vue'
import TeacherDashboardView from '@/views/teacher/DashboardView.vue'
import TeacherQuizEditorView from '@/views/teacher/QuizEditorView.vue'
import TeacherQuizResultsView from '@/views/teacher/ResultsView.vue'
import TeacherLibraryListView from '@/views/teacher/LibraryListView.vue'
import TeacherLibraryDetailView from '@/views/teacher/LibraryDetailView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/join/:code', name: 'join-code', component: HomeView, props: true },
  { path: '/play/:token', name: 'play', component: PlayView },
  { path: '/result/:token', name: 'result', component: ResultView },
  { path: '/teacher/login', name: 'teacher-login', component: TeacherLoginView },
  { path: '/teacher/register', name: 'teacher-register', component: TeacherRegisterView },
  { path: '/teacher', name: 'teacher', component: TeacherDashboardView },
  { path: '/teacher/quizzes/:id', name: 'teacher-quiz', component: TeacherQuizEditorView, props: true },
  { path: '/teacher/quizzes/:id/results', name: 'teacher-quiz-results', component: TeacherQuizResultsView, props: true },
  { path: '/teacher/library', name: 'teacher-library', component: TeacherLibraryListView },
  { path: '/teacher/library/:id', name: 'teacher-library-quiz', component: TeacherLibraryDetailView, props: true },
  { path: '/admin/login', name: 'admin-login', component: ComingSoonView, props: { label: 'Đăng nhập admin' } },
  { path: '/admin', name: 'admin', component: ComingSoonView, props: { label: 'Trang chủ admin' } },
  { path: '/admin/teachers', name: 'admin-teachers', component: ComingSoonView, props: { label: 'Quản lý giáo viên' } },
  { path: '/admin/quizzes', name: 'admin-quizzes', component: ComingSoonView, props: { label: 'Quản lý bộ đề' } },
  { path: '/admin/attempts', name: 'admin-attempts', component: ComingSoonView, props: { label: 'Quản lý kết quả' } },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
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

export default router