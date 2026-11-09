<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const auth = useAuthStore()
const { toast } = useToast()

const USERNAME_RE = /^[a-zA-Z0-9_.]{4,30}$/
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirm = ref(false)
const loading = ref(false)
const fieldErrors = ref({})

function clearErrors() {
  fieldErrors.value = {}
}

function validate() {
  clearErrors()
  const u = username.value.trim()
  const e = email.value.trim().toLowerCase()
  const p = password.value
  const cp = confirmPassword.value
  let valid = true

  if (!u) {
    fieldErrors.value = { ...fieldErrors.value, username: 'Tên đăng nhập bắt buộc.' }
    valid = false
  } else if (!USERNAME_RE.test(u)) {
    fieldErrors.value = { ...fieldErrors.value, username: 'Tên đăng nhập 4–30 ký tự, chỉ chữ, số, dấu gạch dưới và dấu chấm.' }
    valid = false
  }

  if (!e) {
    fieldErrors.value = { ...fieldErrors.value, email: 'Email bắt buộc.' }
    valid = false
  } else if (!EMAIL_RE.test(e)) {
    fieldErrors.value = { ...fieldErrors.value, email: 'Email không hợp lệ.' }
    valid = false
  }

  if (!p) {
    fieldErrors.value = { ...fieldErrors.value, password: 'Mật khẩu bắt buộc.' }
    valid = false
  } else if (p.length < 8) {
    fieldErrors.value = { ...fieldErrors.value, password: 'Mật khẩu tối thiểu 8 ký tự.' }
    valid = false
  }

  if (!cp) {
    fieldErrors.value = { ...fieldErrors.value, confirmPassword: 'Vui lòng nhập lại mật khẩu.' }
    valid = false
  } else if (cp !== p) {
    fieldErrors.value = { ...fieldErrors.value, confirmPassword: 'Mật khẩu nhập lại không khớp.' }
    valid = false
  }

  return valid
}

async function onRegister() {
    if (!validate()) return

    loading.value = true
    try {
      const api = (await import('@/api/axios')).default
      const res = await api.post('/auth/register', {
        username: username.value.trim(),
        email: email.value.trim().toLowerCase(),
        password: password.value,
      })
      const data = res.data
      auth.setAuth(data.access_token, data.user)
      toast.success('Đăng ký thành công.', 'Chào mừng')
      router.push('/teacher')
    } catch (e) {
      const msg = e.response && e.response.data && e.response.data.error
        ? e.response.data.error
        : 'Đăng ký thất bại. Vui lòng thử lại.'
      fieldErrors.value = { _form: msg }
      toast.error(msg, 'Đăng ký thất bại')
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
      <h2 class="q-page-title">Đăng ký giáo viên</h2>
      <p class="q-page-sub">Tạo tài khoản giáo viên để quản lý bộ đề thi.</p>

      <form @submit.prevent="onRegister" class="q-form">
        <div class="q-form-group">
          <label class="q-form-label">Tên đăng nhập</label>
          <input
            class="q-form-control"
            v-model="username"
            placeholder="tên_đăng_nhập (4–30 ký tự)"
            :class="{ 'q-form-error': fieldErrors.username }"
          />
          <div v-if="fieldErrors.username" class="q-form-error">{{ fieldErrors.username }}</div>
        </div>

        <div class="q-form-group">
          <label class="q-form-label">Email</label>
          <input
            class="q-form-control"
            v-model="email"
            type="email"
            placeholder="ten@example.com"
            :class="{ 'q-form-error': fieldErrors.email }"
          />
          <div v-if="fieldErrors.email" class="q-form-error">{{ fieldErrors.email }}</div>
        </div>

        <div class="q-form-group">
          <label class="q-form-label">Mật khẩu</label>
          <div class="q-password-wrap">
            <input
              class="q-form-control"
              :type="showPassword ? 'text' : 'password'"
              v-model="password"
              placeholder="•••••••• (tối thiểu 8 ký tự)"
              :class="{ 'q-form-error': fieldErrors.password }"
            />
            <button type="button" class="q-password-toggle" @click="showPassword = !showPassword">
              {{ showPassword ? 'Ẩn' : 'Hiện' }}
            </button>
          </div>
          <div v-if="fieldErrors.password" class="q-form-error">{{ fieldErrors.password }}</div>
        </div>

        <div class="q-form-group">
          <label class="q-form-label">Nhập lại mật khẩu</label>
          <div class="q-password-wrap">
            <input
              class="q-form-control"
              :type="showConfirm ? 'text' : 'password'"
              v-model="confirmPassword"
              placeholder="••••••••"
              :class="{ 'q-form-error': fieldErrors.confirmPassword }"
            />
            <button type="button" class="q-password-toggle" @click="showConfirm = !showConfirm">
              {{ showConfirm ? 'Ẩn' : 'Hiện' }}
            </button>
          </div>
          <div v-if="fieldErrors.confirmPassword" class="q-form-error">{{ fieldErrors.confirmPassword }}</div>
        </div>

        <div v-if="fieldErrors._form" class="q-form-error q-form-error--block">{{ fieldErrors._form }}</div>

        <button
          type="submit"
          class="q-btn q-btn-primary q-btn-full"
          :disabled="loading"
        >
          {{ loading ? 'Đăng ký...' : 'Đăng ký' }}
        </button>
      </form>

      <p class="q-page-footer">
        Đã có tài khoản?
        <a class="q-link" @click="router.push({ name: 'teacher-login' })">Đăng nhập tại đây</a>
      </p>
    </div>
  </div>
</template>
