<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import { teacherApi } from '@/api/teacher'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import LoadingState from '@/components/LoadingState.vue'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'

const router = useRouter()
const auth = useAuthStore()
const toast = useToast()

const quizzes = ref([])
const loading = ref(false)
const loadError = ref(null)
const search = ref('')
const showCreateModal = ref(false)
const newTitle = ref('')
const deleteDialog = ref(false)
const deleteTarget = ref(null)
const saving = ref(false)
const toggleOpen = ref(null)

const deleteMessage = computed(() => {
  const q = deleteTarget.value
  if (!q) return ''
  return 'Bạn chắc chắn muốn xóa "' + q.title + '"? ' + (q.attempt_count || 0) + ' lượt làm sẽ mất và không khôi phục được.'
})

const emptyHint = computed(() => {
  if (search.value.trim()) return ''
  return 'Nhấn "Tạo bộ đề mới" để bắt đầu.'
})

function filtered() {
  const s = search.value.trim().toLowerCase()
  if (!s) return quizzes.value
  return quizzes.value.filter(q => q.title.toLowerCase().includes(s))
}

async function load() {
  loading.value = true
  loadError.value = null
  try {
    const res = await teacherApi.listQuizzes()
    quizzes.value = res.data
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không tải được danh sách bộ đề.'
    loadError.value = msg
    toast.error(msg, 'Lỗi tải danh sách')
  } finally {
    loading.value = false
  }
}

async function onCreate() {
  const t = newTitle.value.trim()
  if (!t) { toast.error('Vui lòng nhập tiêu đề bộ đề.', 'Tiêu đề bắt buộc'); return }
  saving.value = true
  try {
    const res = await teacherApi.createQuiz({ title: t })
    const id = res.data.quiz.id
    showCreateModal.value = false
    newTitle.value = ''
    toast.success('Đã tạo bộ đề.', 'Thành công')
    router.push({ name: 'teacher-quiz', params: { id } })
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không tạo được bộ đề.'
    toast.error(msg, 'Tạo thất bại')
  } finally {
    saving.value = false
  }
}

function openDelete(quiz) {
  deleteTarget.value = quiz
  deleteDialog.value = true
}

async function confirmDelete() {
  const q = deleteTarget.value
  if (!q) return
  deleteDialog.value = false
  try {
    await teacherApi.deleteQuiz(q.id)
    toast.success('Đã xóa bộ đề "' + q.title + '".', 'Xóa thành công')
    await load()
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không xóa được bộ đề.'
    toast.error(msg, 'Xóa thất bại')
  } finally {
    deleteTarget.value = null
  }
}

async function toggleQuizOpen(quiz) {
  toggleOpen.value = quiz.id
  try {
    await teacherApi.updateQuiz(quiz.id, { is_open: !quiz.is_open })
    quiz.is_open = !quiz.is_open
    toast.success(quiz.is_open ? 'Đã mở nhận bài.' : 'Đã đóng nhận bài.', 'Cập nhật trạng thái')
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không thay đổi trạng thái.'
    toast.error(msg, 'Thất bại')
    await load()
  } finally {
    toggleOpen.value = null
  }
}

onMounted(() => { load() })
</script>

<template>
  <div class="q-page-wrap q-teacher-page">
    <div class="q-page-header">
      <h2 class="q-page-title">Bộ đề của tôi</h2>
      <p class="q-page-sub">Quản lý bộ đề thi, tra cứu và soạn câu hỏi.</p>
    </div>

    <div v-if="loading" style="display:flex;justify-content:center;padding:40px 0;">
      <LoadingState message="Đang tải bộ đề..." />
    </div>

    <div v-else-if="loadError" style="display:flex;justify-content:center;padding:40px 0;">
      <ErrorState :message="loadError" :retry="load" back-label="Trang chủ" back-route="/" />
    </div>

    <div v-else>
      <div class="q-attempts-header">
        <div class="q-library-header">
          <input
            class="q-field-control"
            v-model="search"
            placeholder="Tìm theo tiêu đề bộ đề..."
          />
          <button class="q-btn q-btn-primary" @click="showCreateModal = true">Tạo bộ đề mới</button>
        </div>
      </div>

      <div v-if="filtered().length === 0" style="display:flex;justify-content:center;padding:40px 0;flex-direction:column;align-items:center;">
        <EmptyState
          :message="search.trim() ? 'Không tìm thấy bộ đề nào phù hợp.' : 'Chưa có bộ đề nào.'"
          :hint="emptyHint"
        />
        <button class="q-btn q-btn-primary" @click="showCreateModal = true" style="margin-top:24px;">Tạo bộ đề mới</button>
      </div>

      <div v-else class="q-quiz-grid">
        <div v-for="q in filtered()" :key="q.id" class="q-quiz-card">
          <div class="q-quiz-meta">
            <span>{{ q.question_count }} câu hỏi</span>
            <span>•</span>
            <span>{{ q.attempt_count }} lượt làm</span>
          </div>
          <h3>{{ q.title }}</h3>
          <div class="q-code-badge">{{ q.access_code }}</div>
          <div class="q-quiz-meta" style="margin-top:auto;">
            <span>{{ q.is_open ? 'Đang mở' : 'Đóng' }} &#8226; {{ q.is_public ? 'Công khai' : 'Riêng tư' }}</span>
          </div>
          <div class="q-quiz-actions">
            <button class="q-btn q-btn-outline" @click.stop="router.push({ name: 'teacher-quiz', params: { id: q.id } })">Soạn</button>
            <button class="q-btn q-btn-outline" @click.stop="router.push({ name: 'teacher-quiz-results', params: { id: q.id } })">Kết quả</button>
            <button class="q-btn q-btn-outline" @click.stop="toggleQuizOpen(q)" :disabled="toggleOpen === q.id">
              {{ toggleOpen === q.id ? '...' : (q.is_open ? 'Đóng nhận bài' : 'Mở nhận bài') }}
            </button>
            <button class="q-btn q-btn-outline" @click.stop="openDelete(q)">Xóa</button>
          </div>
        </div>
      </div>

      <ConfirmDialog
        v-model:visible="deleteDialog"
        title="Xóa bộ đề"
        :message="deleteMessage"
        confirmLabel="Xóa"
        cancelLabel="Hủy"
        confirmVariant="danger"
        @confirm="confirmDelete"
      />
    </div>

    <div v-if="showCreateModal" class="q-dialog-overlay" @click="showCreateModal = false"></div>
    <div v-if="showCreateModal" class="q-dialog" role="dialog" aria-modal="true" aria-label="Tạo bộ đề mới">
      <div class="q-dialog-card">
        <div class="q-dialog-title">Tạo bộ đề mới</div>
        <div class="q-dialog-message">Nhập tiêu đề bộ đề (bắt buộc).</div>
        <div class="q-dialog-actions" style="margin-top:0;">
          <input
            class="q-field-control"
            v-model="newTitle"
            placeholder="Tiêu đề bộ đề"
            @keydown.enter="onCreate"
          />
          <button class="q-btn q-btn-primary" :disabled="saving || !newTitle.trim()" @click="onCreate">
            {{ saving ? 'Đang tạo...' : 'Tạo' }}
          </button>
          <button class="q-btn q-btn-outline" @click="showCreateModal = false">Hủy</button>
        </div>
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
  width: 90%; max-width: 480px; z-index: 3001;
}
.q-dialog-card {
  background: var(--q-card); border: 1px solid var(--q-border);
  border-radius: var(--q-radius-xl); box-shadow: var(--q-shadow);
  padding: 28px 32px; color: var(--q-text);
}
.q-dialog-title { font-size: 1.15rem; font-weight: 700; margin-bottom: 12px; }
.q-dialog-message { font-size: 0.98rem; line-height: 1.6; color: var(--q-text-soft); margin-bottom: 24px; }
.q-dialog-actions { display: flex; gap: 10px; justify-content: flex-end; align-items: center; flex-wrap: wrap; }
</style>