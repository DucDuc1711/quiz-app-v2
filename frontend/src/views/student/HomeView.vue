<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import QRCode from 'qrcode'
import { playApi } from '@/api/play'
import { useDeviceId } from '@/composables/useDeviceId'

const route = useRoute()
const router = useRouter()
const { deviceId } = useDeviceId()

const code = ref((route.params.code || '').toUpperCase())
const name = ref('')

onMounted(() => {
  if (code.value && !quiz.value && !error.value) onLookup()
})
const loading = ref(false)
const error = ref(null)
const quiz = ref(null)
const qrDataUrl = ref(null)

watch(code, (val) => {
  code.value = val.toUpperCase()
})

function apiErrorMessage(e, fallback) {
  if (e.response && e.response.data && e.response.data.error) return e.response.data.error
  if (e.response && e.response.status === 404) return 'Khong tim thay bo de voi ma nay.'
  if (e.response && e.response.status === 403) return 'Bo de dong hoac chua vao thoi gian lam bai.'
  if (e.response && e.response.status === 409) return 'Thiet bi nay da lam bo de nay.'
  return fallback
}

async function onLookup() {
  const c = code.value.trim()
  if (!c) {
    error.value = 'Vui long nhap ma bo de.'
    return
  }
  loading.value = true
  error.value = null
  quiz.value = null
  qrDataUrl.value = null
  try {
    const res = await playApi.lookup(c)
    quiz.value = res.data.quiz
    try {
      qrDataUrl.value = await QRCode.toDataURL(window.location.origin + '/join/' + c)
    } catch (_) {}
  } catch (e) {
    quiz.value = null
    error.value = apiErrorMessage(e, 'Khong tra cuu duoc ma bo de. Vui long thu lai.')
  } finally {
    loading.value = false
  }
}

async function onJoin() {
  const c = code.value.trim()
  if (!c) {
    error.value = 'Vui long nhap ma bo de.'
    return
  }
  if (!name.value.trim()) {
    error.value = 'Ten hoc sinh khong duoc bo trong.'
    return
  }
  loading.value = true
  error.value = null
  try {
    const res = await playApi.join({ code: c, name: name.value.trim(), device_id: deviceId })
    localStorage.setItem('quiz_attempt_token', res.data.attempt_token)
    router.push({ name: 'play', params: { token: res.data.attempt_token } })
  } catch (e) {
    error.value = apiErrorMessage(e, 'Tham gia bo de that bai. Vui long thu lai.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="q-home-wrap">
    <div class="q-container q-home-grid">
      <div class="q-home-left">
        <div class="q-brand-big"><span class="q-mark">Q</span>uiz App</div>
        <p class="q-lead">Thi trac nghiem vui nhon cho hoc sinh. Nhap ma bo de va ten cua ban de bat dau.</p>
        <div class="q-illustration">
          <svg viewBox="0 0 200 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="hero-title">
            <title id="hero-title">Minh hoa thi trac nghiem</title>
            <rect x="30" y="40" width="140" height="70" rx="14" fill="#F1F5F9" stroke="#E2E8F0" stroke-width="2" />
            <circle cx="78" cy="75" r="16" fill="#6C5CE7" />
            <path d="M72 70 L78 78 L86 68" stroke="#FFFFFF" stroke-width="3" fill="none" />
            <rect x="110" y="58" width="24" height="34" rx="5" fill="#EA580C" />
            <path d="M132 56 Q150 48 162 60" fill="none" stroke="#DB2777" stroke-width="3" />
            <circle cx="150" cy="76" r="6" fill="#DB2777" />
            <circle cx="112" cy="44" r="5" fill="#F97316" />
            <circle cx="166" cy="50" r="5" fill="#0891B2" />
            <circle cx="126" cy="102" r="5" fill="#2563EB" />
          </svg>
        </div>
        <p class="q-ill-caption">Chuan bi sang cay? Hay nhap ma va vao cuoi chuyen trinh!</p>
      </div>
      <div class="q-home-right q-panel q-pad">
        <h3 class="q-form-title">Tham gia bo de</h3>
        <div class="q-form-group">
          <label class="q-form-label">Ma bo de</label>
          <input class="q-form-control" v-model="code" maxlength="6" placeholder="VD: ABC123" />
        </div>
        <div class="q-form-group">
          <label class="q-form-label">Ten hoc sinh</label>
          <input class="q-form-control" v-model="name" maxlength="40" placeholder="Ten cua ban" />
        </div>
        <button class="q-btn q-btn-primary q-btn-full mt-2" @click="onLookup" :disabled="loading">Kiem tra ma</button>
        <button class="q-btn q-btn-outline q-btn-full mt-3" @click="onJoin" :disabled="loading || !quiz">Tham gia bo de</button>
        <div v-if="error" class="q-error">{{ error }}</div>
        <div v-if="quiz" class="q-quiz-info">
          <p><strong>{{ quiz.title }}</strong></p>
          <p>{{ quiz.total_questions }} cau hoi &#8226; {{ quiz.question_time }} giay moi cau</p>
        </div>
        <div v-if="qrDataUrl" class="q-qr">
          <img class="q-qr-img" :src="qrDataUrl" alt="QR tham gia bo de" />
          <p class="q-text-soft">Quet de tham gia tu dien thoai</p>
        </div>
      </div>
    </div>
  </div>
</template>