<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { teacherApi } from '@/api/teacher'
import LoadingState from '@/components/LoadingState.vue'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'

const router = useRouter()
const toast = useToast()

const quizzes = ref([])
const total = ref(0)
const page = ref(1)
const per_page = ref(12)
const loading = ref(false)
const error = ref(null)
const search = ref('')
const tagFilter = ref('')
const tags = ref([])

const loadTags = ref([])

async function load() {
  loading.value = true
  error.value = null
  try {
    const res = await teacherApi.listLibrary({
      search: search.value.trim(),
      tag: tagFilter.value.trim(),
      page: page.value,
      per_page: per_page.value,
    })
    quizzes.value = res.data.quizzes || []
    total.value = res.data.total || 0
    page.value = res.data.page || 1
    per_page.value = res.data.per_page || 12
    // gather tags from results
    const tset = new Set()
    for (const q of quizzes.value) {
      if (q.tags) {
        q.tags.split(',').forEach(t => {
          const tt = t.trim()
          if (tt) tset.add(tt)
        })
      }
    }
    loadTags.value = Array.from(tset).sort()
  } catch (e) {
    const msg = e.response && e.response.data && e.response.data.error
      ? e.response.data.error
      : 'Không tải được thư viện.'
    error.value = msg
    toast.error(msg, 'Lỗi tải thư viện')
  } finally {
    loading.value = false
  }
}

function debounce(fn, delay) {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}

const debouncedSearch = debounce(() => {
  page.value = 1
  load()
}, 300)

watch(search, () => { debouncedSearch() })
watch(tagFilter, () => { page.value = 1; load() })

function goPage(p) {
  if (p < 1 || p > Math.ceil(total.value / per_page.value)) return
  page.value = p
  load()
}

function selectTag(t) {
  tagFilter.value = t
  page.value = 1
  load()
}

function clearTag() {
  tagFilter.value = ''
  load()
}

onMounted(() => { load() })
</script>

<template>
  <div class="q-page-wrap q-teacher-page">
    <div class="q-page-header">
      <h2 class="q-page-title">Thư viện bộ đề</h2>
      <p class="q-page-sub">Khám phá và sao chép bộ đề công khai từ các giáo viên khác.</p>
    </div>

    <div v-if="loading" style="display:flex;justify-content:center;padding:40px 0;">
      <LoadingState message="Đang tải thư viện..." />
    </div>

    <div v-else-if="error" style="display:flex;justify-content:center;padding:40px 0;">
      <ErrorState :message="error" :retry="load" back-label="Về bộ đề của tôi" back-route="teacher" />
    </div>

    <div v-else>
      <div class="q-library-header">
        <input
          class="q-field-control"
          v-model="search"
          placeholder="Tìm kiếm bộ đề..."
          @input="() => {}"
        />
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <span v-if="tagFilter" class="q-tag-chip">{{ tagFilter }} <span style="cursor:pointer;color:var(--q-brand);" @click="clearTag">×</span></span>
          <span v-for="t in loadTags" :key="t" class="q-tag-chip" :class="{ 'q-tag-chip--active': tagFilter === t }" @click="selectTag(t)">
            {{ t }}
          </span>
        </div>
      </div>

      <div v-if="quizzes.length === 0" style="display:flex;justify-content:center;padding:40px 0;">
        <EmptyState :message="search.trim() || tagFilter.trim() ? 'Không tìm thấy bộ đề nào phù hợp.' : 'Thư viện trống.'" />
      </div>

      <div v-else class="q-library-grid">
        <div
          v-for="q in quizzes"
          :key="q.id"
          class="q-library-card"
          @click="router.push({ name: 'teacher-library-quiz', params: { id: q.id } })"
        >
          <h3>{{ q.title }}</h3>
          <p>{{ q.description || '(không có mô tả)' }}</p>
          <div class="q-library-meta">
            <span>Tác giả: {{ q.owner || '—' }}</span>
            <span>•</span>
            <span>{{ q.question_count || 0 }} câu hỏi</span>
          </div>
          <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;">
            <span v-for="t in (q.tags || '').split(',').map(x => x.trim()).filter(x => x)" :key="t" class="q-tag-chip">{{ t }}</span>
          </div>
        </div>
      </div>

      <div v-if="total > 0" class="q-pagination">
        <button :disabled="page === 1" @click="goPage(page - 1)">Trang trước</button>
        <span style="padding:0 10px;">Trang {{ page }} / {{ Math.ceil(total / per_page) }}</span>
        <button :disabled="page >= Math.ceil(total / per_page)" @click="goPage(page + 1)">Trang sau</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.q-tag-chip--active {
  background: var(--q-brand);
  color: #fff;
}
</style>