<script setup>
import { ref } from 'vue'
import { useToast } from '@/composables/useToast'
import { teacherApi } from '@/api/teacher'

const props = defineProps(['quizId'])
const emit = defineEmits(['imported'])

const { success, error } = useToast()

const file = ref(null)
const loading = ref(false)
const result = ref(null)

function handleFileChange(e) {
  file.value = e.target.files[0] || null
}

async function downloadTemplate() {
  try {
    await teacherApi.downloadImportTemplate()
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không tải được file mẫu.'
    toast.error(msg, 'Tải thất bại')
  }
}

async function onImport() {
  if (!file.value) { toast.error('Vui lòng chọn file.', 'Chọn file'); return }
  const ext = file.value.name.split('.').pop().toLowerCase()
  if (ext !== 'xlsx' && ext !== 'csv') { toast.error('Chỉ nhận file .xlsx hoặc .csv.', 'Sai định dạng'); return }
  loading.value = true
  result.value = null
  try {
    const res = await teacherApi.importQuestions(props.quizId, file.value)
    result.value = res.data
    success('Nhập ' + res.data.imported + ' câu hỏi. ' + (res.data.errors && res.data.errors.length ? res.data.errors.length + ' dòng lỗi.' : 'Không có lỗi.'), 'Nhập thành công')
    emit('imported')
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không nhập được file.'
    toast.error(msg, 'Nhập thất bại')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="q-panel" style="padding:20px;margin-top:20px;">
    <h3 style="font-size:1rem;margin-bottom:12px;">Nhập câu hỏi từ Excel/CSV</h3>
    <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
      <button class="q-btn q-btn-outline" :disabled="loading" @click="downloadTemplate">Tải file mẫu</button>
      <input type="file" accept=".xlsx,.csv" @change="handleFileChange" style="display:none;" ref="fileInput" />
      <button class="q-btn q-btn-outline" :disabled="loading || !file.value" @click="() => { const el = $refs.fileInput; if(el) el.click() }">Chọn file</button>
      <span v-if="file.value" style="font-size:0.85rem;color:var(--q-text-soft);">{{ file.value.name }}</span>
      <button class="q-btn q-btn-primary" :disabled="loading || !file.value" @click="onImport">
        {{ loading ? 'Đang nhập...' : 'Nhập câu hỏi' }}
      </button>
    </div>
    <div class="q-import-note" style="margin-top:10px;">
      <span>Định dạng cột:</span>
      <span style="font-family:monospace;font-size:0.85rem;color:var(--q-brand);">Câu hỏi | Loại | Đáp án A…F | Đáp án đúng | Thời gian</span>
    </div>

    <div v-if="result" style="margin-top:16px;padding:14px;background:var(--q-muted);border-radius:var(--q-radius-md);">
      <div style="font-weight:700;margin-bottom:6px;">Kết quả nhập</div>
      <div style="font-size:0.9rem;">
        <span>Đã nhập: <b>{{ result.imported }}</b> câu hỏi</span>
        <span v-if="result.errors && result.errors.length" style="color:var(--q-danger);margin-left:12px;">Lỗi: <b>{{ result.errors.length }}</b> dòng</span>
      </div>
      <div v-if="result.errors && result.errors.length" style="margin-top:8px;max-height:200px;overflow-y:auto;font-size:0.85rem;">
        <div v-for="(err, i) in result.errors" :key="i" style="margin-bottom:4px;">{{ err }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped></style>