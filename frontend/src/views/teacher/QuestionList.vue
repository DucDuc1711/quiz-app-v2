<script setup>
import { ref, computed } from 'vue'
import { useToast } from '@/composables/useToast'
import { teacherApi } from '@/api/teacher'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const props = defineProps(['questions', 'quizId', 'locked'])
const emit = defineEmits(['edit', 'delete', 'reorder'])

const { toast } = useToast()
const deleteDialog = ref(false)
const deleteTarget = ref(null)
const deleteMessage = computed(() => 'B\u1eb7n ch\u00e1c ch\u1ea5n mu\u01b0\u1ed1n x\u00f3a c\u00e2u h\u1ecfi: "' + (deleteTarget.value?.content || '').slice(0, 60) + '...?')

function typeLabel(t) {
  const m = { single: '1 đáp án', multiple: 'Nhiều đáp án', true_false: 'Đúng/Sai' }
  return m[t] || t
}

async function move(dir, idx) {
  if (props.locked) return
  const ids = props.questions.map(q => q.id)
  if (dir === -1 && idx === 0) return
  if (dir === 1 && idx === ids.length - 1) return
  const tmp = ids[idx]
  ids[idx] = ids[idx + dir]
  ids[idx + dir] = tmp
  try {
    await teacherApi.reorderQuestions(props.quizId, ids)
    emit('reorder', ids)
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không đổi thứ tự câu hỏi.'
    toast.error(msg, 'Thất bại')
  }
}

function openDelete(q) {
  deleteTarget.value = q
  deleteDialog.value = true
}

async function confirmDelete() {
  const q = deleteTarget.value
  if (!q) return
  deleteDialog.value = false
  try {
    await teacherApi.deleteQuestion(q.id)
    toast.success('Đã xóa câu hỏi.', 'Xóa thành công')
    emit('delete', q.id)
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không xóa được câu hỏi.'
    toast.error(msg, 'Xóa thất bại')
  } finally {
    deleteTarget.value = null
  }
}
</script>

<template>
  <div>
    <div v-for="(q, idx) in questions" :key="q.id" class="q-question-item">
      <div class="q-question-info">
        <div class="q-question-number">Câu {{ idx + 1 }}</div>
        <div class="q-question-content">{{ q.content }}</div>
        <div class="q-question-meta">
          <span>{{ typeLabel(q.type) }}</span>
          <span v-if="q.time_limit">• {{ q.time_limit }}s/câu</span>
          <span v-if="q.image_url">• có ảnh</span>
        </div>
      </div>
      <div class="q-question-actions">
        <button class="q-btn q-btn-outline" :disabled="props.locked" @click="emit('edit', q)">Sửa</button>
        <button class="q-btn q-btn-outline" :disabled="props.locked" @click="openDelete(q)">Xóa</button>
        <button
          class="q-btn q-btn-outline"
          :disabled="props.locked || idx === 0"
          @click="move(-1, idx)"
        >Lên</button>
        <button
          class="q-btn q-btn-outline"
          :disabled="props.locked || idx === questions.length - 1"
          @click="move(1, idx)"
        >Xuống</button>
      </div>
    </div>

    <ConfirmDialog
      v-model:visible="deleteDialog"
      title="Xóa câu hỏi"
      :message="deleteMessage"
      confirmLabel="Xóa"
      cancelLabel="Hủy"
      confirmVariant="danger"
      @confirm="confirmDelete"
    />
  </div>
</template>

<style scoped></style>