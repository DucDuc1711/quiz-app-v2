<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { teacherApi } from '@/api/teacher'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import LoadingState from '@/components/LoadingState.vue'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'

const router = useRouter()
const toast = useToast()

const props = defineProps(['id'])

const loading = ref(false)
const loadError = ref(null)
const stats = ref(null)
const attempts = ref([])
const wrongStats = ref([])
const deleteDialog = ref(false)
let deleteTarget = ref(null)
const sortKey = ref(null)
const sortDir = ref('asc')
const searchName = ref('')

const isValidId = computed(() => {
  const n = Number(props.id)
  return Number.isInteger(n) && n > 0
})

async function load() {
  if (!isValidId.value) {
    loadError.value = 'Đường dẫn không hợp lệ.'
    loading.value = false
    return
  }
  loading.value = true
  loadError.value = null
  try {
    const [sRes, aRes] = await Promise.all([
      teacherApi.getStats(props.id),
      teacherApi.listAttempts(props.id),
    ])
    stats.value = sRes.data
    attempts.value = aRes.data
    wrongStats.value = (stats.value.questions || []).map((q, i) => ({ ...q, index: i + 1 }))
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không tải được kết quả.'
    loadError.value = msg
  } finally {
    loading.value = false
  }
}

onMounted(load)

function truncated(content, len = 60) {
  if (!content) return ''
  return content.length > len ? content.slice(0, len) + '…' : content
}

function formatTime(seconds) {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return (m > 0 ? m + 'p ' : '') + s + 's'
}

function sortAttempts(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}

const sortedAttempts = computed(() => {
  const arr = [...attempts.value].filter(a => {
    if (!searchName.value.trim()) return true
    return a.student_name.toLowerCase().includes(searchName.value.trim().toLowerCase())
  })
  if (!sortKey.value) return arr
  return arr.sort((a, b) => {
    let av = a[sortKey.value], bv = b[sortKey.value]
    if (av == null) av = ''
    if (bv == null) bv = ''
    if (sortDir.value === 'asc') return av > bv ? 1 : av < bv ? -1 : 0
    return av < bv ? 1 : av > bv ? -1 : 0
  })
})

function sortLabel(key) {
  if (sortKey.value !== key) return '⇕'
  return sortDir.value === 'asc' ? '↑' : '↓'
}

async function confirmDeleteAttempt() {
  const id = deleteTarget
  if (!id) return
  deleteDialog.value = false
  try {
    await teacherApi.deleteAttempt(id)
    toast.success('Đã xóa lượt làm.', 'Xóa thành công')
    await load()
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không xóa được lượt làm.'
    toast.error(msg, 'Xóa thất bại')
  } finally {
    deleteTarget = null
  }
}

async function exportResults(fmt) {
  try {
    const res = await teacherApi.exportResults(props.id, fmt)
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = `ket_qua_${props.id}.${fmt}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    toast.success('Đã xuất file ' + fmt.toUpperCase() + '.', 'Xuất thành công')
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không xuất được file.'
    toast.error(msg, 'Xuất thất bại')
  }
}

onMounted(() => { load() })
</script>

<template>
  <div class="q-page-wrap q-teacher-page">
    <div class="q-page-header">
      <h2 class="q-page-title">Kết quả làm bài</h2>
      <p class="q-page-sub">Thống kê và đánh giá lượt làm của học sinh.</p>
    </div>

    <div v-if="loading" style="display:flex;justify-content:center;padding:40px 0;">
      <LoadingState message="Đang tải kết quả..." />
    </div>

    <div v-else-if="loadError" style="display:flex;justify-content:center;padding:40px 0;">
      <ErrorState :message="loadError" :retry="load" back-label="Về trình soạn" back-route="teacher-quiz" />
    </div>

    <div v-else>
      <div class="q-attempts-header">
        <div class="q-stat-grid">
          <div class="q-stat-card">
            <div class="q-stat-value">{{ stats?.total_attempts || 0 }}</div>
            <div class="q-stat-label">Lượt làm</div>
          </div>
          <div class="q-stat-card">
            <div class="q-stat-value">{{ (stats?.average_score || 0).toFixed(1) }}</div>
            <div class="q-stat-label">Điểm trung bình</div>
          </div>
          <div class="q-stat-card">
            <div class="q-stat-value">{{ stats?.max_score || 0 }}</div>
            <div class="q-stat-label">Điểm cao nhất</div>
          </div>
          <div class="q-stat-card">
            <div class="q-stat-value">{{ stats?.min_score || 0 }}</div>
            <div class="q-stat-label">Điểm thấp nhất</div>
          </div>
        </div>

        <div style="display:flex;gap:10px;">
          <button class="q-btn q-btn-outline" @click="exportResults('xlsx')">Xuất Excel (.xlsx)</button>
          <button class="q-btn q-btn-outline" @click="exportResults('csv')">Xuất CSV (.csv)</button>
          <button class="q-btn q-btn-outline" @click="router.push({ name: 'teacher-quiz', params: { id } })">Về trình soạn</button>
        </div>
      </div>

      <div v-if="wrongStats && wrongStats.length" class="q-panel" style="margin-top:20px;">
        <h3 style="font-size:1rem;margin-bottom:12px;">Tỉ lệ sai từng câu</h3>
        <div v-for="q in wrongStats" :key="q.index" class="q-wrong-row" :class="{ 'q-wrong-high': q.wrong_rate >= 0.5 }">
          <span class="q-wrong-index">#{{ q.index }}</span>
          <span class="q-wrong-content">{{ truncated(q.content, 50) }}</span>
          <div class="q-wrong-bar"><div class="q-wrong-fill" :style="{ width: Math.round((q.wrong_rate || 0) * 100) + '%' }"></div></div>
          <span class="q-wrong-pct">{{ Math.round((q.wrong_rate || 0) * 100) }}% sai</span>
        </div>
      </div>

      <div v-if="attempts.length === 0" style="margin-top:24px;display:flex;justify-content:center;">
        <EmptyState message="Chưa có ai làm bài này." hint="Học sinh sẽ nhập mã bộ đề để tham gia làm bài." />
      </div>

      <div v-if="attempts.length" style="margin-top:24px;">
        <div class="q-library-header">
          <input class="q-field-control" v-model="searchName" placeholder="Tìm theo tên học sinh..." />
        </div>
        <div class="q-table-wrap">
          <table class="q-attempt-table">
            <thead>
              <tr>
                <th class="q-sortable" @click="sortAttempts('student_name')">Họ tên {{ sortLabel('student_name') }}</th>
                <th class="q-sortable" @click="sortAttempts('score')">Điểm {{ sortLabel('score') }}</th>
                <th class="q-sortable" @click="sortAttempts('correct_answers')">Đúng {{ sortLabel('correct_answers') }}</th>
                <th class="q-sortable" @click="sortAttempts('total_questions')">Tổng câu {{ sortLabel('total_questions') }}</th>
                <th class="q-sortable" @click="sortAttempts('time_spent')">Thời gian {{ sortLabel('time_spent') }}</th>
                <th class="q-sortable" @click="sortAttempts('tab_switch_count')">Rời tab {{ sortLabel('tab_switch_count') }}</th>
                <th>Trạng thái</th>
                <th>Nộp lúc</th>
                <th style="width:110px;">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in sortedAttempts" :key="a.id">
                <td>{{ a.student_name }}</td>
                <td>{{ a.score }}</td>
                <td>{{ a.correct_answers }}</td>
                <td>{{ a.total_questions }}</td>
                <td>{{ formatTime(a.time_spent) }}</td>
                <td>{{ a.tab_switch_count }}</td>
                <td>{{ a.status === 'submitted' ? 'Đã nộp' : 'Đang làm' }}</td>
                <td>{{ a.finished_at ? new Date(a.finished_at).toLocaleString('vi-VN') : '—' }}</td>
                <td>
                  <button class="q-btn q-btn-outline" style="font-size:0.85rem;padding:0 8px;" @click="deleteTarget = a.id">Xóa</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <ConfirmDialog
        v-model:visible="deleteDialog"
        title="Xóa lượt làm"
        message="Bạn chắc chắn muốn xóa lượt làm này? Thao tác không khôi phục được."
        confirmLabel="Xóa"
        cancelLabel="Hủy"
        confirmVariant="danger"
        @confirm="confirmDeleteAttempt"
      />
    </div>
  </div>
</template>

<style scoped>
.q-stat-card {
  background: var(--q-card);
  border: 1px solid var(--q-border);
  border-radius: var(--q-radius-lg);
  padding: 16px;
  text-align: center;
}
.q-stat-value { font-size: 2rem; font-weight: 800; color: var(--q-brand); }
.q-stat-label { font-size: 0.85rem; color: var(--q-text-soft); margin-top: 4px; }
</style>