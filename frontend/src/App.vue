<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { onMounted, onUnmounted, computed } from 'vue'

const router = useRouter()
const auth = useAuthStore()
auth.init()

const userLabel = computed(() => {
  if (!auth.user) return null
  return auth.isAdmin ? 'Admin (' + auth.user.username + ')' : 'Giao vien (' + auth.user.username + ')'
})

onMounted(() => {
  window.addEventListener('auth-logout', onAuthLogout)
})
onUnmounted(() => {
  window.removeEventListener('auth-logout', onAuthLogout)
})

function onAuthLogout(e) {
  const role = e.detail && e.detail.role
  const to = role === 'admin' ? '/admin/login' : role === 'teacher' ? '/teacher/login' : '/'
  router.push(to)
}

function logout() {
  auth.clearAuth()
  router.push('/')
}
</script>

<template>
  <div class="q-app">
    <header class="q-header">
      <div class="q-container q-inner">
        <div class="q-brand" @click="router.push('/')"><span class="q-mark">Q</span>uiz App</div>
        <nav class="q-nav-links">
          <a class="q-btn q-btn-outline" :class="{ 'q-btn-primary': $route.path === '/' }" @click="router.push('/')">Trang chu</a>
          <span v-if="auth.isAuthenticated" class="q-text-soft">{{ userLabel }}</span>
          <a v-if="auth.isAuthenticated" class="q-btn q-btn-danger" @click="logout">Dang xuat</a>
          <a v-if="!auth.isAuthenticated" class="q-btn q-btn-outline" @click="router.push('/teacher/login')">Dang nhap giao vien</a>
          <a v-if="!auth.isAuthenticated" class="q-btn q-btn-outline" @click="router.push('/admin/login')">Dang nhap admin</a>
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
      Quiz App &#8212; demo thi trac nghiem &middot; chay local tren may tinh
    </footer>
  </div>
</template>
