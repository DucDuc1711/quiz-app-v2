import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/student/HomeView.vue'
import PlayView from '@/views/student/PlayView.vue'
import ResultView from '@/views/student/ResultView.vue'
import NotFoundView from '@/views/NotFoundView.vue'
import ComingSoonView from '@/views/ComingSoonView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/join/:code', name: 'join-code', component: HomeView, props: true },
  { path: '/play/:token', name: 'play', component: PlayView },
  { path: '/result/:token', name: 'result', component: ResultView },
  { path: '/teacher/login', name: 'teacher-login', component: ComingSoonView, props: { label: 'Đăng nhập giáo viên' } },
  { path: '/teacher/register', name: 'teacher-register', component: ComingSoonView, props: { label: 'Đăng ký giáo viên' } },
  { path: '/teacher', name: 'teacher', component: ComingSoonView, props: { label: 'Trang chủ giáo viên' } },
  { path: '/teacher/quizzes/:id', name: 'teacher-quiz', component: ComingSoonView, props: { label: 'Soạn bộ đề' } },
  { path: '/teacher/quizzes/:id/results', name: 'teacher-quiz-results', component: ComingSoonView, props: { label: 'Kết quả bộ đề' } },
  { path: '/teacher/library', name: 'teacher-library', component: ComingSoonView, props: { label: 'Thư viện bộ đề' } },
  { path: '/teacher/library/:id', name: 'teacher-library-quiz', component: ComingSoonView, props: { label: 'Chi tiết thư viện' } },
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

export default router