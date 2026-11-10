<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { teacherApi } from '@/api/teacher'
import LoadingState from '@/components/LoadingState.vue'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'

const router = useRouter()
const route = useRoute()
const { success, error } = useToast()

const quiz = ref(null)
const loading = ref(false)
const loadError = ref(null)
const cloning = ref(false)

async function load() {
  loading.value = true
  loadError.value = null
  try {
    const res = await teacherApi.getLibraryQuiz(route.params.id)
    quiz.value = res.data
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không tải được chi tiết bộ đề.'
    loadError.value = msg
    toast.error(msg, 'Lỗi tải chi tiết')
  } finally {
    loading.value = false
  }
}

function truncated(content, len = 80) {
  if (!content) return ''
  return content.length > len ? content.slice(0, len) + '…' : content
}

async function onClone() {
  cloning.value = true
  try {
    const res = await teacherApi.cloneQuiz(route.params.id)
    const id = res.data.quiz.id
    success('Đã sao chép bộ đề.', 'Thành công')
    router.push({ name: 'teacher-quiz', params: { id } })
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không sao chép được bộ đề.'
    toast.error(msg, 'Sao chép thất bại')
  } finally {
    cloning.value = false
  }
}

onMounted(() => { load() })
</script>

<template>
  <div class="q-page-wrap q-teacher-page">
    <div class="q-page-header">
      <button class="q-btn q-btn-outline" @click="router.push({ name: 'teacher-library' })">← Về thư viện</button>
      <h2 class="q-page-title">{{ quiz?.title || 'Chi tiết bộ đề' }}</h2>
      <p class="q-page-sub">Xem toàn bộ câu hỏi và đáp án của bộ đề công khai.</p>
    </div>

    <div v-if="loading" style="display:flex;justify-content:center;padding:40px 0;">
      <LoadingState message="Đang tải chi tiết..." />
    </div>

    <div v-else-if="loadError" style="display:flex;justify-content:center;padding:40px 0;">
      <ErrorState :message="loadError" :retry="load" back-label="Về thư viện" back-route="teacher-library" />
    </div>

    <div v-else-if="quiz" class="q-library-detail">
      <div class="q-panel" style="margin-bottom:20px;">
        <h3 style="font-size:1.1rem;margin-bottom:8px;">{{ quiz.title }}</h3>
        <p v-if="quiz.description" style="color:var(--q-text-soft);margin-bottom:12px;">{{ quiz.description }}</p>
        <div class="q-library-meta" style="margin-bottom:8px;">
          <span>Tác giả: {{ quiz.owner || '—' }}</span>
          <span style="margin-left:12px;">Mã: <b>{{ quiz.access_code }}</b></span>
          <span style="margin-left:12px;">{{ quiz.questions?.length || 0 }} câu hỏi</span>
          <span v-if="quiz.tags" style="margin-left:12px;">Thẻ: {{ quiz.tags }}</span>
        </div>
      </div>

      <div class="q-detail-questions">
        <h3 style="font-size:1rem;margin-bottom:12px;">Câu hỏi</h3>
        <div v-for="(q, idx) in quiz.questions" :key="q.order_num || idx" class="q-detail-question">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
            <span style="font-weight:700;color:var(--q-brand);">Câu {{ q.order_num || (idx + 1) }}</span>
            <span style="font-size:0.8rem;color:var(--q-text-soft);">{{ q.type }}</span>
          </div>
          <p style="margin-bottom:8px;">{{ q.content }}</p>
          <div class="q-detail-choices">
            <div
              v-for="(c, cidx) in q.choices"
              :key="c.order_num || cidx"
              class="q-detail-choice"
              :class="{ 'q-detail-choice--correct': c.is_correct }"
            >
              <span class="q-detail-choice-icon">{{ c.is_correct ? '✓' : '○' }}</span>
              <span>{{ c.content }}</span>
            </div>
          </div>
        </div>
      </div>

      <div style="margin-top:24px;display:flex;gap:10px;justify-content:flex-end;">
        <button class="q-btn q-btn-primary" :disabled="cloning" @click="onClone">
          {{ cloning ? 'Đang sao chép...' : 'Dùng bộ đề này' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped></style>