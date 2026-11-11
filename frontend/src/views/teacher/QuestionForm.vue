<script setup>
import { ref, computed, watch } from 'vue'
import { useToast } from '@/composables/useToast'
import { teacherApi } from '@/api/teacher'

const props = defineProps(['quizId', 'question', 'visible'])
const emit = defineEmits(['save', 'cancel', 'image-added'])

const toast = useToast()

const isEdit = computed(() => !!props.question)

const type = ref(isEdit.value ? props.question.type : 'single')
const content = ref(isEdit.value ? props.question.content : '')
const timeLimit = ref(isEdit.value && props.question.time_limit ? String(props.question.time_limit) : '')
const imageUrl = ref(isEdit.value ? props.question.image_url : '')
const imagePreview = ref(isEdit.value ? props.question.image_url : '')
const imageFile = ref(null)
const imageError = ref(null)

const choices = ref(isEdit.value
  ? props.question.choices.map(c => ({ content: c.content || '', is_correct: !!c.is_correct, _id: c.id }))
  : [{ content: '', is_correct: false }, { content: '', is_correct: false }])

const fieldErrors = ref({})
const loading = ref(false)

function choiceContent(i) { return choices.value[i] ? choices.value[i].content : '' }

function correctCount() {
  return choices.value.filter(c => c.is_correct).length
}

function isTrueFalse() { return type.value === 'true_false' }

watch(type, (val) => {
  if (val === 'true_false') {
    choices.value = [
      { content: 'Đúng', is_correct: false, _tf: true },
      { content: 'Sai', is_correct: false, _tf: true },
    ]
  } else if (choices.value.length < 2) {
    choices.value.push({ content: '', is_correct: false })
  }
})

function addChoice() {
  if (choices.value.length >= 6) { toast.error('Tối đa 6 đáp án.', 'Giới hạn đáp án'); return }
  choices.value.push({ content: '', is_correct: false })
}

function removeChoice(idx) {
  if (isTrueFalse()) { toast.error('Không xóa đáp án câu Đúng/Sai.', 'Không thể xóa'); return }
  if (choices.value.length <= 2) { toast.error('Ít nhất 2 đáp án.', 'Giới hạn đáp án'); return }
  choices.value.splice(idx, 1)
  if (correctCount() === 0 && choices.value.length > 0) choices.value[0].is_correct = true
}

function toggleCorrect(idx) {
  if (isTrueFalse()) {
    choices.value.forEach((c, i) => { c.is_correct = (i === idx) })
  } else if (type.value === 'single') {
    choices.value.forEach((c, i) => { c.is_correct = (i === idx) })
  } else {
    choices.value[idx].is_correct = !choices.value[idx].is_correct
  }
}

function validate() {
  fieldErrors.value = {}
  let ok = true

  if (!content.value || content.value.length < 1 || content.value.length > 1000) {
    fieldErrors.value.content = 'Nội dung câu hỏi từ 1-1000 ký tự.'
    ok = false
  }

  if (type.value === 'true_false') {
    if (choices.value.length !== 2) { fieldErrors.value.choices = 'Câu Đúng/Sai phải có 2 đáp án.'; ok = false }
    const contents = new Set(choices.value.map(c => c.content))
    if (!contents.has('Đúng') || !contents.has('Sai')) { fieldErrors.value.choices = 'Đáp án Đúng/Sai phải là "Đúng" và "Sai".'; ok = false }
    if (correctCount() !== 1) { fieldErrors.value.choices = 'Câu Đúng/Sai phải chọn đúng 1 đáp án.'; ok = false }
  } else {
    if (choices.value.length < 2 || choices.value.length > 6) {
      fieldErrors.value.choices = 'Số lượng đáp án phải từ 2-6.'
      ok = false
    }
    for (let i = 0; i < choices.value.length; i++) {
      const c = choices.value[i].content || ''
      if (c.length < 1 || c.length > 300) {
        fieldErrors.value['choice_' + i] = 'Nội dung đáp án từ 1-300 ký tự.'
        ok = false
      }
    }
    if (type.value === 'single' && correctCount() !== 1) {
      fieldErrors.value.choices = 'Câu 1 đáp án phải chọn đúng 1 đáp án.'
      ok = false
    }
    if (type.value === 'multiple' && correctCount() < 1) {
      fieldErrors.value.choices = 'Câu nhiều đáp án phải chọn ít nhất 1 đáp án đúng.'
      ok = false
    }
  }

  const tl = Number(timeLimit.value)
  if (timeLimit.value !== '' && (!tl || tl < 5 || tl > 600)) {
    fieldErrors.value.time_limit = 'Thời gian câu từ 5-600 giây.'
    ok = false
  }

  if (imageError.value) {
    fieldErrors.value.image = imageError.value
    ok = false
  }

  return ok
}
async function onSave() {
  if (!validate()) return

  let finalImageUrl = imageUrl.value
  if (imageFile.value) {
    try {
      const res = await teacherApi.uploadImage(imageFile.value)
      finalImageUrl = res.data.url
      emit('image-added', finalImageUrl)
    } catch (e) {
      const msg = e.response && e.response.data && e.response.data.error
        ? e.response.data.error
        : 'Không tải lên ảnh.'
      toast.error(msg, 'Tải ảnh thất bại')
      return
    }
  }

  const payload = {
    type: type.value,
    content: content.value,
    image_url: finalImageUrl || null,
    time_limit: timeLimit.value ? Number(timeLimit.value) : null,
    choices: choices.value.map((c, i) => ({
      content: c.content,
      is_correct: c.is_correct,
      order_num: i,
    })),
  }

  loading.value = true
  try {
    if (isEdit.value) {
      await teacherApi.updateQuestion(props.question.id, payload)
      toast.success('Đã cập nhật câu hỏi.', 'Cập nhật')
    } else {
      await teacherApi.addQuestion(props.quizId, payload)
      toast.success('Đã thêm câu hỏi.', 'Thêm mới')
    }
    emit('save')
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không lưu được câu hỏi.'
    toast.error(msg, 'Lưu thất bại')
  } finally {
    loading.value = false
  }
}

function handleImageChange(e) {
  const file = e.target.files[0]
  if (!file) return
  const allowed = ['image/png', 'image/jpeg', 'image/webp', 'image/gif']
  if (!allowed.includes(file.type)) {
    imageError.value = 'Chỉ nhận ảnh png, jpg, webp, gif.'
    imageFile.value = null
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    imageError.value = 'File quá lớn. Giới hạn 2 MB.'
    imageFile.value = null
    return
  }
  imageError.value = null
  imageFile.value = file
  imagePreview.value = URL.createObjectURL(file)
}

function removeImage() {
  imageFile.value = null
  imagePreview.value = imageUrl.value || null
}
</script>

<template>
  <div v-if="props.visible" class="q-dialog-overlay" @click="emit('cancel')"></div>
  <div v-if="props.visible" class="q-dialog" role="dialog" aria-modal="true" aria-label="Câu hỏi">
    <div class="q-dialog-card">
      <div class="q-dialog-title">{{ isEdit ? 'Sửa câu hỏi' : 'Thêm câu hỏi' }}</div>

      <div class="q-field">
        <label class="q-field-label">Loại câu hỏi</label>
        <div style="display:flex;gap:10px;">
          <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
            <input type="radio" name="qtype" value="single" v-model="type" /> 1 đáp án
          </label>
          <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
            <input type="radio" name="qtype" value="multiple" v-model="type" /> Nhiều đáp án
          </label>
          <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
            <input type="radio" name="qtype" value="true_false" v-model="type" /> Đúng / Sai
          </label>
        </div>
        <div v-if="fieldErrors.type" class="q-form-error">{{ fieldErrors.type }}</div>
      </div>

      <div class="q-field">
        <label class="q-field-label">Nội dung câu hỏi <span style="font-size:0.8em;">({{ content.value.length }}/1000)</span></label>
        <textarea class="q-field-control" v-model="content" rows="3" :class="{'q-form-error': fieldErrors.content}"></textarea>
        <div v-if="fieldErrors.content" class="q-form-error">{{ fieldErrors.content }}</div>
      </div>

      <div class="q-field">
        <label class="q-field-label">Thời gian câu (giây, trống = mặc định bộ đề)</label>
        <input class="q-field-control" type="number" v-model="timeLimit" min="5" max="600" :class="{'q-form-error': fieldErrors.time_limit}" />
        <div v-if="fieldErrors.time_limit" class="q-form-error">{{ fieldErrors.time_limit }}</div>
      </div>

      <div class="q-field" style="margin-top:12px;">
        <label class="q-field-label">Ảnh câu hỏi</label>
        <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" @change="handleImageChange" />
        <div v-if="imageError" class="q-form-error" style="margin-top:6px;">{{ imageError }}</div>
        <div v-if="imagePreview" style="margin-top:10px;">
          <img :src="imagePreview" style="max-width:200px;max-height:200px;border:1px solid var(--q-border);border-radius:var(--q-radius-md);" />
          <button class="q-btn q-btn-outline" style="font-size:0.85rem;margin-top:6px;" @click="removeImage">Gỡ ảnh</button>
        </div>
      </div>

      <div style="margin-top:12px;">
        <label class="q-field-label">Đáp án</label>
        <div v-for="(c, i) in choices" :key="i" style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <div style="flex:1;">
            <input class="q-field-control" v-model="choices[i].content" placeholder="Nội dung đáp án" :disabled="isTrueFalse()" />
          </div>
          <div style="width:24px;">
            <input type="checkbox" v-if="type === 'multiple'" v-model="choices[i].is_correct" />
            <input type="radio" v-else-if="type === 'single'" name="correct" :value="i" v-model="choices[i].is_correct" :disabled="isTrueFalse()" />
            <span v-if="isTrueFalse()" style="font-weight:800;">{{ i === 0 ? 'Đúng' : 'Sai' }}</span>
          </div>
          <button v-if="!isTrueFalse()" class="q-btn q-btn-outline" style="font-size:0.8rem;padding:0 6px;" @click="removeChoice(i)">×</button>
          <div v-if="fieldErrors['choice_' + i]" class="q-form-error" style="margin-top:2px;">{{ fieldErrors['choice_' + i] }}</div>
        </div>
        <button class="q-btn q-btn-outline" style="font-size:0.85rem;" @click="addChoice" :disabled="choices.length >= 6 || isTrueFalse()">Thêm đáp án</button>
        <div v-if="fieldErrors.choices" class="q-form-error" style="margin-top:6px;">{{ fieldErrors.choices }}</div>
        <div v-if="isTrueFalse()" style="font-size:0.85rem;color:var(--q-text-soft);margin-top:6px;">
          Đáp án cố định: Đúng / Sai. Chọn 1 đáp án đúng.
        </div>
      </div>

      <div class="q-dialog-actions" style="margin-top:18px;">
        <button class="q-btn q-btn-outline" @click="emit('cancel')">Hủy</button>
        <button class="q-btn q-btn-primary" :disabled="loading" @click="onSave">
          {{ loading ? 'Đang lưu...' : (isEdit ? 'Cập nhật' : 'Thêm') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.q-dialog-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 3000;
  display: flex; align-items: center; justify-content: center;
}
.q-dialog {
  width: 90%; max-width: 700px; z-index: 3001;
}
.q-dialog-card {
  background: var(--q-card); border: 1px solid var(--q-border);
  border-radius: var(--q-radius-xl); box-shadow: var(--q-shadow);
  padding: 28px 32px; color: var(--q-text);
  max-height: 85vh; overflow-y: auto;
}
.q-dialog-title { font-size: 1.15rem; font-weight: 700; margin-bottom: 20px; }
.q-field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.q-field-label { font-size: 0.9rem; font-weight: 600; color: var(--q-text-soft); }
.q-field-control {
  min-height: var(--q-touch-min); padding: 0 14px;
  border: 1px solid var(--q-border); border-radius: var(--q-radius-md);
  font-size: 1rem; width: 100%;
}
.q-field-control.q-form-error { border-color: var(--q-danger); }
.q-form-error { font-size: 0.82rem; color: var(--q-danger); margin-top: 2px; }
.q-dialog-actions { display: flex; gap: 10px; justify-content: flex-end; }
</style>
