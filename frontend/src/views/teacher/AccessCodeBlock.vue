<script setup>
import { ref, computed, onMounted } from 'vue'
import QRCode from 'qrcode'
import { useToast } from '@/composables/useToast'
import { teacherApi } from '@/api/teacher'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const props = defineProps(['code', 'quizId'])
const emit = defineEmits(['code-changed'])

const { success, error } = useToast()

const showFullscreen = ref(false)
const regenDialog = ref(false)
const copying = ref(false)
const qrUrl = ref(null)

onMounted(async () => {
  try {
    qrUrl.value = await QRCode.toDataURL(window.location.origin + '/join/' + props.code)
  } catch (_) {}
})

async function copyText(text, label) {
  copying.value = true
  try {
    await navigator.clipboard.writeText(text)
    success('Đã sao chép ' + label + '.', 'Sao chép')
  } catch (e) {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    try {
      document.execCommand('copy')
      success('Đã sao chép ' + label + '.', 'Sao chép')
    } catch (_) {
      error('Không thể sao chép. Vui lòng sao chép thủ công.', 'Sao chép')
    }
    document.body.removeChild(ta)
  } finally {
    copying.value = false
  }
}

function copyLink() {
  const link = window.location.origin + '/join/' + props.code
  copyText(link, 'link tham gia')
}

function openRegenerateDialog() {
  regenDialog.value = true
}

async function regenerateCode() {
  regenDialog.value = false
  try {
    const res = await teacherApi.regenerateCode(props.quizId)
    const newCode = res.data.access_code
    emit('code-changed', newCode)
    success('Đã sinh mã mới: ' + newCode, 'Mã mới')
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không sinh được mã mới.'
    error(msg, 'Sinh mã thất bại')
  }
}

const joinLink = computed(() => window.location.origin + '/join/' + props.code)
</script>
<template>
  <div class="q-access-block">
    <div class="q-code-big">{{ code }}</div>
    <div class="q-copy-link">{{ joinLink }}</div>
    <div style="margin-top:16px;display:flex;gap:8px;justify-content:center;flex-wrap:wrap;">
      <button class="q-btn q-btn-outline" :disabled="copying" @click="copyText(code, 'mã')">Sao chép mã</button>
      <button class="q-btn q-btn-outline" :disabled="copying" @click="copyLink">Sao chép link</button>
      <button class="q-btn q-btn-primary" @click="openRegenerateDialog">Sinh mã mới</button>
      <button class="q-btn q-btn-outline" @click="showFullscreen = true">Chiếu lên bảng</button>
    </div>

    <!-- Fullscreen board view -->
    <div v-if="showFullscreen" class="q-dialog-overlay" @click="showFullscreen = false"></div>
    <div v-if="showFullscreen" class="q-board-full" role="dialog" aria-modal="true" aria-label="Chiếu mã lên bảng">
      <div class="q-board-card">
        <button class="q-board-close" @click="showFullscreen = false" aria-label="Đóng">✕</button>
        <h2 class="q-board-title">Mã tham gia</h2>
        <div class="q-board-code">{{ code }}</div>
        <div class="q-board-hint">Học sinh vào <span style="font-weight:700;">{{ joinLink }}</span> để làm bài</div>
        <img class="q-board-qr" :src="qrUrl" alt="QR mã tham gia" />
        <div class="q-board-close-hint">Nhấn Esc hoặc nhấp bên ngoài để đóng</div>
      </div>
    </div>

    <ConfirmDialog
      v-model:visible="regenDialog"
      title="Sinh mã mới"
      :message="'Mã hiện tại (' + code + ') sẽ ngừng dùng được. Các học sinh đang có mã cũ sẽ không thể truy cập nữa. Bạn chắc chắn muốn sinh mã mới?'"
      confirmLabel="Sinh mã mới"
      cancelLabel="Hủy"
      confirmVariant="danger"
      @confirm="regenerateCode"
    />
  </div>
</template>

<style scoped>
.q-board-full {
  position: fixed; inset: 0; background: #ffffff; z-index: 4000;
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.q-board-card {
  background: #ffffff; border: 4px solid var(--q-brand);
  border-radius: var(--q-radius-xl); padding: 40px;
  text-align: center; max-width: 560px; width: 100%;
  box-shadow: var(--q-shadow);
}
.q-board-close {
  position: absolute; top: 16px; right: 16px;
  background: none; border: none; font-size: 2rem;
  color: var(--q-text-soft); cursor: pointer;
}
.q-board-close:hover { color: var(--q-text); }
.q-board-title {
  font-size: 1.5rem; font-weight: 800; color: var(--q-text);
  margin: 0 0 24px 0;
}
.q-board-code {
  font-size: 4.5rem; font-weight: 900; color: var(--q-brand);
  letter-spacing: 6px; margin: 0 0 16px 0;
  background: var(--q-muted); padding: 24px; border-radius: var(--q-radius-lg);
  display: inline-block;
}
.q-board-hint {
  font-size: 1rem; color: var(--q-text-soft);
  margin-bottom: 24px;
}
.q-board-qr {
  width: 220px; height: 220px;
  margin: 0 auto 24px auto;
}
.q-board-close-hint {
  font-size: 0.85rem; color: var(--q-text-soft);
}

@media (max-width: 480px) {
  .q-board-code { font-size: 2.5rem; padding: 16px; }
  .q-board-qr { width: 160px; height: 160px; }
  .q-board-card { padding: 24px; }
}
</style>