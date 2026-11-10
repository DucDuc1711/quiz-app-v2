<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import AuthCard from '@/components/AuthCard.vue'
import PasswordField from '@/components/PasswordField.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const { success, error } = useToast()

const redirect = computed(() => route.query.redirect || '/teacher')

const username = ref('')
const password = ref('')
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
  let token = null
  let user = null
  try {
    const api = (await import('@/api/axios')).default
    const res = await api.post('/auth/login', {
      username_or_email: u.toLowerCase(),
      password: p,
    })
    token = res.data.access_token
    user = res.data.user
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Đăng nhập không thành công. Vui lòng thử lại.'
    fieldErrors.value = { _form: msg }
    error(msg, 'Đăng nhập không thành công')
    loading.value = false
    return
  }

  // Bước sau (setAuth, toast, chuyển trang) nằm ngoài try gọi API,
  // nên lỗi ở đây không bị báo là "đăng nhập thất bại".
  try {
    if (user && user.role === 'admin') {
      error('Tài khoản admin vui lòng đăng nhập tại /admin/login', 'Không thể đăng nhập')
      loading.value = false
      return
    }
    auth.setAuth(token, user)
    try {
      success('Đăng nhập thành công.', 'Chào mừng')
    } catch (_) {}
    router.push(redirect.value)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthCard
    title="Đăng nhập giáo viên"
    subtitle="Vui lòng nhập thông tin để vào trang quản lý bộ đề."
    :error="fieldErrors._form || null"
    submitLabel="Đăng nhập"
    :loading="loading"
    toggleBefore="Chưa có tài khoản?"
    toggleText="Đăng ký tài khoản mới"
    @toggle="router.push({ name: 'teacher-register' })"
    @submit="onLogin"
  >
    <template #form>
      <div class="q-form-group">
        <label class="q-form-label">Tên đăng nhập hoặc email</label>
        <input
          class="q-form-control"
          v-model="username"
          placeholder="tên đăng nhập hoặc email"
          autocomplete="username"
          autocapitalize="off"
          autocorrect="off"
          spellcheck="false"
          :class="{ 'q-form-error': fieldErrors.username }"
        />
        <div v-if="fieldErrors.username" class="q-form-error">{{ fieldErrors.username }}</div>
      </div>

      <div class="q-form-group">
        <label class="q-form-label">Mật khẩu</label>
        <PasswordField
          v-model="password"
          aria-label="Mật khẩu"
          autocomplete="current-password"
          placeholder="••••••••"
          :error="!!fieldErrors.password"
        />
        <div v-if="fieldErrors.password" class="q-form-error">{{ fieldErrors.password }}</div>
      </div>
    </template>
  </AuthCard>
</template>

