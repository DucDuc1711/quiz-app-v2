<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { playApi } from '@/api/play'
import confetti from 'canvas-confetti'

const route = useRoute()
const router = useRouter()

const result = ref(null)
const ranking = ref([])
const loading = ref(true)
const err = ref(null)

const prefersReduced = typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches

function runConfetti() {
  if (prefersReduced) return
  const duration = 2 * 1000
  const end = Date.now() + duration
  const colors = ['#6C5CE7', '#8B5CF6', '#2563EB', '#EA580C', '#DB2777']
  ;(function frame() {
    confetti({ particleCount: 6, angle: 60, spread: 55, origin: { x: 0 }, colors })
    confetti({ particleCount: 6, angle: 120, spread: 55, origin: { x: 1 }, colors })
    if (Date.now() < end) requestAnimationFrame(frame)
  })()
}

async function loadResult() {
  loading.value = true
  err.value = null
  try {
    const res = await playApi.result(route.params.token)
    result.value = res.data
    if (res.data.rank && res.data.rank <= 3) runConfetti()
    if (res.data.show_ranking) {
      const r = await playApi.ranking(route.params.token)
      ranking.value = r.data.ranking || []
    }
  } catch (e) {
    if (e.response && e.response.status === 409) {
      router.replace({ name: 'play', params: { token: route.params.token } })
      return
    }
    err.value = e.response && e.response.data && e.response.data.error ? e.response.data.error : 'Không lấy được kết quả.'
  } finally {
    loading.value = false
  }
}

onMounted(loadResult)
</script>

<template>
  <div class="q-result-wrap">
    <div v-if="loading" class="q-state">
      <div class="q-spinner"></div>
      <div class="q-state-title">Đang tải kết quả...</div>
    </div>
    <div v-else-if="err" class="q-state">
      <div class="q-state-title">Có lỗi xảy ra</div>
      <div class="q-text-soft">{{ err }}</div>
      <button class="q-btn q-btn-primary mt-3" @click="loadResult">Thử lại</button>
    </div>
    <div v-else class="q-result-card">
      <div class="q-result-grid">
        <div class="q-result-left">
          <div class="q-result-badge">Kết quả của {{ result.student_name }}</div>
          <div class="q-score-big">{{ result.score }} / 10</div>
          <div class="q-score-meta">
            <span><strong>{{ result.correct_answers }}</strong> / {{ result.total_questions }} câu đúng</span>
            <span>&#8226; Thời gian: {{ result.time_spent }}s</span>
            <span>&#8226; Hạng: <strong>{{ result.rank }}</strong></span>
          </div>
          <button class="q-btn q-btn-primary q-btn-full mt-4" @click="router.push('/')">Làm bộ đề khác</button>
        </div>
        <div class="q-result-right">
          <h3 class="q-result-title">Bảng xếp hạng</h3>
          <div v-if="!result.show_ranking" class="q-empty">Bảng xếp hạng được ẩn cho bộ đề này.</div>
          <div v-else class="q-table-wrap">
            <table class="q-rank-table">
              <thead>
                <tr><th>Hang</th><th>Ten hoc sinh</th><th>Diem</th><th>Dung</th><th>Thoi gian</th></tr>
              </thead>
              <tbody>
                <tr v-for="(r, i) in ranking" :key="r.name + '|' + r.score + '|' + (r.rank || i)" :class="{ 'q-me': r.is_me }">
                  <td>{{ r.rank }}</td><td>{{ r.name }}</td><td>{{ r.score }}</td><td>{{ r.correct_answers }}</td><td>{{ r.time_spent }}s</td>
                </tr>
                <tr v-if="ranking.length === 0"><td colspan="5" class="q-empty">Chưa có ai xếp hạng.</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>