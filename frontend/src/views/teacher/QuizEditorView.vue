<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { teacherApi } from '@/api/teacher'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import LoadingState from '@/components/LoadingState.vue'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'
import AccessCodeBlock from './AccessCodeBlock.vue'
import QuizSettings from './QuizSettings.vue'
import QuestionList from './QuestionList.vue'
import QuestionForm from './QuestionForm.vue'
import ImportBlock from './ImportBlock.vue'

const route = useRoute()
const router = useRouter()
const { toast } = useToast()

const quiz = ref(null)
const loading = ref(false)
const error = ref(null)
const activeTab = ref('settings')
const showQuestionForm = ref(false)
const editingQuestion = ref(null)
const unsavedChanges = ref(false)
const deleteQuizDialog = ref(false)
const deleteAttemptsDialog = ref(false)

async function load() {
  loading.value = true
  error.value = null
  try {
    const res = await teacherApi.getQuiz(route.params.id)
    quiz.value = res.data
    unsavedChanges.value = false
  } catch (e) {
    if (e.response && e.response.status === 404) {
      router.replace('/teacher')
      return
    }
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không tải được bộ đề.'
    error.value = msg
    toast.error(msg, 'Lỗi tải')
  } finally {
    loading.value = false
  }
}

function isLocked() {
  return quiz.value && quiz.value.attempt_count > 0
}

const deleteQuizMessage = computed(() => {
  if (!quiz.value) return ''
  return 'Bạn chắc chắn muốn xóa bộ đề "' + quiz.value.title + '"? ' + quiz.value.attempt_count + ' lượt làm sẽ mất và không khôi phục được.'
})

const deleteAttemptsMessage = computed(() => {
  if (!quiz.value) return ''
  return 'Bạn chắc chắn muốn xóa tất cả ' + quiz.value.attempt_count + ' lượt làm của bộ đề này? Thao tác không khôi phục được. Sau khi xóa, bạn sẽ có thể chỉnh sửa câu hỏi.'
})

async function onSettingsSaved(payload) {
  if (payload.is_open !== undefined || payload.is_public !== undefined) {
    await load()
  }
}

async function onQuestionSaved() {
  showQuestionForm.value = false
  editingQuestion.value = null
  await load()
}

async function onQuestionDeleted(qId) {
  await load()
}

async function onImported() {
  await load()
}

async function onCodeChanged(newCode) {
  quiz.value.access_code = newCode
  toast.success('Mã tham gia đã cập nhật: ' + newCode, 'Mã mới')
}

async function deleteQuiz() {
  deleteQuizDialog.value = false
  try {
    await teacherApi.deleteQuiz(quiz.value.id)
    toast.success('Đã xóa bộ đề.', 'Xóa thành công')
    router.push({ name: 'teacher' })
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không xóa được bộ đề.'
    toast.error(msg, 'Xóa thất bại')
  }
}

async function deleteAllAttempts() {
  deleteAttemptsDialog.value = false
  try {
    await teacherApi.deleteQuizAttempts(quiz.value.id)
    toast.success('Đã xóa toàn bộ kết quả làm bài. Bạn có thể chỉnh sửa câu hỏi lại.', 'Xóa kết quả')
    await load()
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không xóa được kết quả.'
    toast.error(msg, 'Xóa thất bại')
  }
}

function warnUnsaved(e) {
  if (unsavedChanges.value) {
    e.preventDefault()
    e.returnValue = ''
  }
}

onMounted(() => {
  load()
  window.addEventListener('beforeunload', warnUnsaved)
})
onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', warnUnsaved)
})
</script>

<template>
  <div class="q-page-wrap q-teacher-page">
    <div v-if="loading" style="display:flex;justify-content:center;padding:40px 0;">
      <LoadingState message="Đang tải bộ đề..." />
    </div>

    <div v-else-if="error" style="display:flex;justify-content:center;padding:40px 0;">
      <ErrorState :message="error" :retry="load" back-label="Về danh sách" back-route="teacher" />
    </div>

    <div v-else-if="quiz" class="q-teacher-page">
      <div class="q-page-header" style="margin-bottom:20px;">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
          <div>
            <h2 class="q-page-title">{{ quiz.title }}</h2>
            <p class="q-page-sub">Mã tham gia: <b>{{ quiz.access_code }}</b> · {{ quiz.question_count }} câu hỏi</p>
          </div>
          <div style="display:flex;gap:8px;">
            <button class="q-btn q-btn-outline" @click="router.push({ name: 'teacher-quiz-results', params: { id: quiz.id } })">Kết quả</button>
            <button class="q-btn q-btn-outline" @click="() => deleteQuizDialog = true">Xóa bộ đề</button>
          </div>
        </div>
      </div>

      <!-- Access code block -->
      <AccessCodeBlock
        :code="quiz.access_code"
        :quiz-id="quiz.id"
        @code-changed="onCodeChanged"
      />

      <!-- Warning when attempts exist -->
      <div v-if="isLocked()" class="q-warn-banner">
        <strong>Cảnh báo:</strong> Bộ đề này đã có <b>{{ quiz.attempt_count }}</b> lượt làm bài,
        không thể thêm, sửa, xóa hay đổi thứ tự câu hỏi.
        <button class="q-btn q-btn-outline" style="margin-left:16px;font-size:0.85rem;" @click="() => deleteAttemptsDialog = true">
          Xóa kết quả để chỉnh sửa
        </button>
      </div>

      <div v-if="!isLocked()">
        <div class="q-editor-tabs">
          <button class="q-editor-tab" :class="{'q-editor-tab--active': activeTab === 'settings'}" @click="activeTab = 'settings'">Cài đặt</button>
          <button class="q-editor-tab" :class="{'q-editor-tab--active': activeTab === 'questions'}" @click="activeTab = 'questions'">Câu hỏi</button>
          <button class="q-editor-tab" :class="{'q-editor-tab--active': activeTab === 'import'}" @click="activeTab = 'import'">Nhập Excel/CSV</button>
        </div>

        <div class="q-editor-panel" :class="{'q-editor-panel--active': activeTab === 'settings'}">
          <QuizSettings :quiz="quiz" @saved="onSettingsSaved" />
        </div>

        <div class="q-editor-panel" :class="{'q-editor-panel--active': activeTab === 'questions'}">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <h3 style="font-size:1rem;margin:0;">Danh sách câu hỏi</h3>
            <button class="q-btn q-btn-primary" @click="() => { editingQuestion.value = null; showQuestionForm.value = true }">+ Thêm câu hỏi</button>
          </div>
          <QuestionList
            :questions="quiz.questions || []"
            :quiz-id="quiz.id"
            :locked="false"
            @edit="q => { editingQuestion.value = q; showQuestionForm.value = true }"
            @delete="onQuestionDeleted"
            @reorder="ids => { unsavedChanges.value = true }"
          />
        </div>

        <div class="q-editor-panel" :class="{'q-editor-panel--active': activeTab === 'import'}">
          <ImportBlock :quiz-id="quiz.id" @imported="onImported" />
        </div>
      </div>

      <div v-else style="padding:24px;">
        <h3 style="font-size:1rem;margin-bottom:12px;">Câu hỏi (khóa do đã có lượt làm)</h3>
        <QuestionList
          :questions="quiz.questions || []"
          :quiz-id="quiz.id"
          :locked="true"
        />
      </div>

      <!-- Question form modal -->
      <QuestionForm
        :quiz-id="quiz.id"
        :question="editingQuestion"
        v-model:visible="showQuestionForm"
        @save="onQuestionSaved"
        @cancel="() => { showQuestionForm.value = false; editingQuestion.value = null }"
      />

      <ConfirmDialog
        v-model:visible="deleteQuizDialog"
        title="Xóa bộ đề"
        :message="deleteQuizMessage"
        confirmLabel="Xóa"
        cancelLabel="Hủy"
        confirmVariant="danger"
        @confirm="deleteQuiz"
      />

      <ConfirmDialog
        v-model:visible="deleteAttemptsDialog"
        title="Xóa toàn bộ kết quả làm bài"
        :message="deleteAttemptsMessage"
        confirmLabel="Xóa tất cả"
        cancelLabel="Hủy"
        confirmVariant="danger"
        @confirm="deleteAllAttempts"
      />
    </div>
  </div>
</template>

<style scoped></style>