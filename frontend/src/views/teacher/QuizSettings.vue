<script setup>
import { ref, computed, watch } from 'vue'
import { useToast } from '@/composables/useToast'
import { teacherApi } from '@/api/teacher'

const props = defineProps(['quiz'])
const emit = defineEmits(['saved', 'code-changed'])

const toast = useToast()

const form = ref({
  title: props.quiz.title || '',
  description: props.quiz.description || '',
  tags: props.quiz.tags || '',
  question_time: props.quiz.question_time || 30,
  shuffle_questions: !!props.quiz.shuffle_questions,
  shuffle_choices: !!props.quiz.shuffle_choices,
  show_ranking: !!props.quiz.show_ranking,
  is_public: !!props.quiz.is_public,
  is_open: !!props.quiz.is_open,
  open_at: props.quiz.open_at ? formatDateTimeLocal(props.quiz.open_at) : '',
  close_at: props.quiz.close_at ? formatDateTimeLocal(props.quiz.close_at) : '',
})

const saving = ref(false)
const unsaved = ref(false)

function formatDateTimeLocal(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) +
    'T' + pad(d.getHours()) + ':' + pad(d.getMinutes())
}

watch(() => form.value, () => {
  unsaved.value = true
}, { deep: true })

async function onSave() {
  saving.value = true
  try {
    const payload = {
      title: form.value.title.trim(),
      description: form.value.description.trim(),
      question_time: Number(form.value.question_time),
      shuffle_questions: form.value.shuffle_questions,
      shuffle_choices: form.value.shuffle_choices,
      show_ranking: form.value.show_ranking,
      is_public: form.value.is_public,
      is_open: form.value.is_open,
      tags: form.value.tags.trim(),
      open_at: form.value.open_at || null,
      close_at: form.value.close_at || null,
    }
    await teacherApi.updateQuiz(props.quiz.id, payload)
    unsaved.value = false
    toast.success('Đã lưu cài đặt bộ đề.', 'Lưu thành công')
    emit('saved', payload)
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không lưu được cài đặt.'
    toast.error(msg, 'Lưu thất bại')
  } finally {
    saving.value = false
  }
}

function clearDateTime(field) {
  form.value[field] = ''
}

function validateDates() {
  if (form.value.open_at && form.value.close_at && form.value.close_at <= form.value.open_at) {
    toast.error('Thời gian đóng phải sau thời gian mở.', 'Lỗi ngày giờ')
    return false
  }
  return true
}

const originalCode = computed(() => props.quiz.access_code)
</script>

<template>
  <div class="q-panel" style="padding:24px;">
    <h3 style="font-size:1.1rem;margin-bottom:16px;">Cài đặt bộ đề</h3>

    <div class="q-settings-grid">
      <div class="q-field">
        <label class="q-field-label">Tiêu đề</label>
        <input class="q-field-control" v-model="form.title" />
      </div>
      <div class="q-field">
        <label class="q-field-label">Mô tả</label>
        <textarea class="q-field-control" v-model="form.description" rows="2"></textarea>
      </div>
      <div class="q-field">
        <label class="q-field-label">Thẻ (cách nhau dấu phẩy)</label>
        <input class="q-field-control" v-model="form.tags" placeholder="toán, tieng-anh, trial" />
        <div class="q-field-help">Ví dụ: môn học, cấp độ, chủ đề.</div>
      </div>
      <div class="q-field">
        <label class="q-field-label">Thời gian mỗi câu (giây)</label>
        <input class="q-field-control" type="number" v-model.number="form.question_time" min="5" max="600" />
        <div class="q-field-help">5–600 giây.</div>
      </div>
    </div>

    <div style="margin-top:16px;border-top:1px solid var(--q-border);padding-top:16px;">
      <div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center;">
        <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
          <input type="checkbox" v-model="form.shuffle_questions" /> Xáo trộn câu hỏi
        </label>
        <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
          <input type="checkbox" v-model="form.shuffle_choices" /> Xáo trộn đáp án
        </label>
        <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
          <input type="checkbox" v-model="form.show_ranking" /> Hiện bảng xếp hạng
        </label>
        <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
          <input type="checkbox" v-model="form.is_public" /> Công khai
        </label>
      </div>
    </div>

    <div style="margin-top:16px;border-top:1px solid var(--q-border);padding-top:16px;">
      <div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center;">
        <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
          <input type="checkbox" v-model="form.is_open" /> Đang mở nhận bài
        </label>
        <div style="margin-left:auto;">
          <button class="q-btn q-btn-outline" @click="clearDateTime('open_at')" v-if="form.open_at">Xóa giờ mở</button>
          <button class="q-btn q-btn-outline" @click="clearDateTime('close_at')" v-if="form.close_at">Xóa giờ đóng</button>
        </div>
      </div>
      <div class="q-field" style="margin-top:10px;display:flex;gap:12px;align-items:center;">
        <label class="q-field-label" style="width:110px;">Lúc mở</label>
        <input class="q-field-control" type="datetime-local" v-model="form.open_at" style="flex:1;" />
      </div>
      <div class="q-field" style="margin-top:8px;display:flex;gap:12px;align-items:center;">
        <label class="q-field-label" style="width:110px;">Lúc đóng</label>
        <input class="q-field-control" type="datetime-local" v-model="form.close_at" style="flex:1;" />
      </div>
    </div>

    <div style="margin-top:20px;display:flex;gap:10px;justify-content:flex-end;">
      <button class="q-btn q-btn-primary" :disabled="saving || !unsaved" @click="onSave">
        {{ saving ? 'Đang lưu...' : 'Lưu cài đặt' }}
      </button>
    </div>
  </div>
</template>

<style scoped></style>