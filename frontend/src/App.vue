<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import { onMounted, onUnmounted, computed } from 'vue'
import ToastHost from '@/components/ToastHost.vue'

const router = useRouter()
const auth = useAuthStore()
const toast = useToast()
auth.init()

const isTeacherZone = computed(() => router.currentRoute.value.path.startsWith('/teacher'))

const userLabel = computed(() => {
  if (!auth.user) return null
  return auth.isAdmin ? 'Admin (' + auth.user.username + ')' : 'Giáo viên (' + auth.user.username + ')'
})

onMounted(() => {
  window.addEventListener('auth-logout', onAuthLogout)
})
onUnmounted(() => {
  window.removeEventListener('auth-logout', onAuthLogout)
})

function onAuthLogout(e) {
  const role = e.detail && e.detail.role
  toast.error('Phiên đăng nhập đã hết hạn.', 'Phiên hết hạn')
  const to = role === 'admin'
    ? '/admin/login'
    : role === 'teacher'
      ? { name: 'teacher-login', query: { redirect: router.currentRoute.value.path || '/' } }
      : '/'
  router.push(to)
}

function logout() {
  auth.clearAuth()
  router.push('/')
}
</script>

<template>
  <div class="q-app">
    <ToastHost />
    <header class="q-header">
      <div class="q-container q-inner">
        <div class="q-brand" @click="router.push('/')"><span class="q-mark">Q</span>uiz App</div>
        <nav class="q-nav-links">
          <a class="q-btn q-btn-outline" :class="{ 'q-btn-primary': $route.path === '/' }" @click="router.push('/')">Trang chủ</a>
          <a v-if="isTeacherZone && auth.isAuthenticated" class="q-btn q-btn-outline" @click="router.push({ name: 'teacher' })">Bộ đề của tôi</a>
          <a v-if="isTeacherZone && auth.isAuthenticated" class="q-btn q-btn-outline" @click="router.push({ name: 'teacher-library' })">Thư viện</a>
          <span v-if="auth.isAuthenticated" class="q-text-soft">{{ userLabel }}</span>
          <a v-if="auth.isAuthenticated" class="q-btn q-btn-danger" @click="logout">Đăng xuất</a>
          <a v-if="!auth.isAuthenticated" class="q-btn q-btn-outline" @click="router.push('/teacher/login')">Đăng nhập giáo viên</a>
          <a v-if="!auth.isAuthenticated" class="q-btn q-btn-outline" @click="router.push('/admin/login')">Đăng nhập admin</a>
        </nav>
      </div>
    </header>
    <main class="q-main q-container">
      <router-view v-slot="{ Component }">
        <transition name="q-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <footer class="q-footer">
      Quiz App &#8212; demo thi trắc nghiệm &middot; chạy local trên máy tính
    </footer>
  </div>
</template>
