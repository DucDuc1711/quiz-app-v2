<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const { toast } = useToast()

const redirect = computed(() => route.query.redirect || '/teacher')

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const fieldErrors = ref({})

function clearErrors() {
  fieldErrors.value = {}
}

async function onLogin() {
  clearErrors()
  const u = username.value.trim()
  const p = password.value
  let valid = true

  if (!u) {
    fieldErrors.value = { ...fieldErrors.value, username: 'Vui lòng nhập tên đăng nhập hoặc email.' }
    valid = false
  }
  if (!p) {
    fieldErrors.value = { ...fieldErrors.value, password: 'Vui lòng nhập mật khẩu.' }
    valid = false
  }
  if (!valid) return

  loading.value = true
  try {
    const api = (await import('@/api/axios')).default
    const res = await api.post('/auth/login', { username_or_email: u, password: p })
    const data = res.data
    if (data.user && data.user.role === 'admin') {
      toast.error('Tai khoan admin vui long dang nhap tai /admin/login', 'Khong the dang nhap')
      loading.value = false
      return
    }
    auth.setAuth(data.access_token, data.user)
    toast.success('Dang nhap thanh cong.', 'Chao mung')
    router.push(redirect.value)
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Đăng nhập thất bại. Vui lòng thử lại.'
    fieldErrors.value = { _form: msg }
    toast.error(msg, 'Đăng nhập thất bại')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="q-page-wrap q-teacher-page">
    <div class="q-page-card q-panel q-pad">
      <div class="q-page-header">
        <span class="q-mark">Q</span>uiz App
      </div>
      <h2 class="q-page-title">Đăng nhập giáo viên</h2>
      <p class="q-page-sub">Vui lòng nhập thông tin để vào trang quản lý bộ đề.</p>

      <form @submit.prevent="onLogin" class="q-form">
        <div class="q-form-group">
          <label class="q-form-label">Ten dang nhap hoac email</label>
          <input
            class="q-form-control"
            v-model="username"
            placeholder="ten_dang_nhap hoac email"
            :class="{ 'q-form-error': fieldErrors.username }"
          />
          <div v-if="fieldErrors.username" class="q-form-error">{{ fieldErrors.username }}</div>
        </div>

        <div class="q-form-group">
          <label class="q-form-label">Mat khau</label>
          <div class="q-password-wrap">
            <input
              class="q-form-control"
              :type="showPassword ? 'text' : 'password'"
              v-model="password"
              placeholder="••••••••"
              :class="{ 'q-form-error': fieldErrors.password }"
            />
            <button type="button" class="q-password-toggle" @click="showPassword = !showPassword">
              {{ showPassword ? 'An' : 'Hien' }}
            </button>
          </div>
          <div v-if="fieldErrors.password" class="q-form-error">{{ fieldErrors.password }}</div>
        </div>

        <div v-if="fieldErrors._form" class="q-form-error q-form-error--block">{{ fieldErrors._form }}</div>

        <button
          type="submit"
          class="q-btn q-btn-primary q-btn-full"
          :disabled="loading"
        >
          {{ loading ? 'Đăng nhập...' : 'Đăng nhập' }}
        </button>
      </form>

      <p class="q-page-footer">
        Chưa có tài khoản?
        <a class="q-link" @click="router.push({ name: 'teacher-register' })">Đăng ký tài mới</a>
      </p>
    </div>
  </div>
</template>

<style scoped>
.q-teacher-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - var(--q-header-height));
  padding: 24px;
}
.q-page-card {
  width: 100%;
  max-width: 400px;
}
.q-page-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--q-brand);
  margin-bottom: 24px;
}
.q-mark {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: var(--q-brand);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
}
.q-page-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: var(--q-text);
}
.q-page-sub {
  font-size: 0.95rem;
  color: var(--q-text-soft);
  margin: 0 0 24px 0;
}
.q-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.q-form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.q-form-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--q-text-soft);
}
.q-form-control {
  min-height: var(--q-touch-min);
  padding: 0 14px;
  border: 1px solid var(--q-border);
  border-radius: var(--q-radius-md);
  font-size: 1rem;
  width: 100%;
}
.q-form-control.q-form-error {
  border-color: var(--q-danger);
}
.q-password-wrap {
  display: flex;
  gap: 8px;
}
.q-password-toggle {
  min-height: var(--q-touch-min);
  padding: 0 14px;
  border: 1px solid var(--q-border);
  border-radius: var(--q-radius-md);
  background: var(--q-card);
  color: var(--q-text-soft);
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;
}
.q-password-toggle:hover {
  border-color: var(--q-brand);
}
.q-form-error {
  font-size: 0.82rem;
  color: var(--q-danger);
  margin-top: 2px;
}
.q-form-error--block {
  margin-top: 8px;
  padding: 8px 12px;
  background: var(--q-danger-bg);
  border: 1px solid var(--q-danger);
  border-radius: var(--q-radius-md);
  color: var(--q-danger-text);
}
.q-btn-full {
  width: 100%;
}
.q-page-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 0.95rem;
  color: var(--q-text-soft);
}
.q-link {
  color: var(--q-brand);
  font-weight: 600;
}
</style>