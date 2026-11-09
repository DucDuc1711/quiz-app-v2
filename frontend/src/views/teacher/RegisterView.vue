<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import AuthCard from '@/components/AuthCard.vue'

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
    let token = null
    let user = null
    try {
      const api = (await import('@/api/axios')).default
      const res = await api.post('/auth/register', {
        username: username.value.trim().toLowerCase(),
        email: email.value.trim().toLowerCase(),
        password: password.value,
      })
      token = res.data.access_token
      user = res.data.user
    } catch (e) {
      const msg = e.response && e.response.data && e.response.data.error
        ? e.response.data.error
        : 'Đăng ký không thành công. Vui lòng thử lại.'
      fieldErrors.value = { _form: msg }
      toast.error(msg, 'Đăng ký không thành công')
      loading.value = false
      return
    }

    // Bước sau (setAuth, toast, chuyển trang) nằm ngoài try gọi API,
    // nên lỗi ở đây không bị báo là "đăng ký thất bại".
    try {
      auth.setAuth(token, user)
      toast.success('Đăng ký thành công.', 'Chào mừng')
      router.push('/teacher')
    } finally {
      loading.value = false
    }
  }
</script>

<template>
  <AuthCard
    title="Đăng ký giáo viên"
    subtitle="Tạo tài khoản giáo viên để quản lý bộ đề thi."
    :error="fieldErrors._form || null"
    submitLabel="Đăng ký"
    :loading="loading"
    toggleBefore="Đã có tài khoản?"
    toggleText="Đăng nhập tại đây"
    @toggle="router.push({ name: 'teacher-login' })"
    @submit="onRegister"
  >
    <template #form>
      <div class="q-form-group">
        <label class="q-form-label">Tên đăng nhập</label>
        <input
          class="q-form-control"
          v-model="username"
          placeholder="tên_đăng_nhập (4–30 ký tự)"
          autocomplete="username"
          autocapitalize="off"
          autocorrect="off"
          spellcheck="false"
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
          autocomplete="email"
          autocapitalize="off"
          autocorrect="off"
          spellcheck="false"
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
            autocomplete="new-password"
            autocapitalize="off"
            autocorrect="off"
            spellcheck="false"
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
            autocomplete="new-password"
            autocapitalize="off"
            autocorrect="off"
            spellcheck="false"
            :class="{ 'q-form-error': fieldErrors.confirmPassword }"
          />
          <button type="button" class="q-password-toggle" @click="showConfirm = !showConfirm">
            {{ showConfirm ? 'Ẩn' : 'Hiện' }}
          </button>
        </div>
        <div v-if="fieldErrors.confirmPassword" class="q-form-error">{{ fieldErrors.confirmPassword }}</div>
      </div>

      <div v-if="fieldErrors._form" class="q-form-error q-form-error--block">{{ fieldErrors._form }}</div>
    </template>
  </AuthCard>
</template>
