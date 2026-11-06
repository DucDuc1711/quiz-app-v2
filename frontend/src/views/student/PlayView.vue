<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { playApi } from '@/api/play'
import { useCountdown } from '@/composables/useCountdown'
import OptionCard from '@/components/OptionCard.vue'
import CountdownRing from '@/components/CountdownRing.vue'

const route = useRoute()
const router = useRouter()
const token = route.params.token

const question = ref(null)
const timeLimit = ref(30)
const phase = ref('question')
const isLast = ref(false)
const index = ref(0)
const total = ref(0)
const selected = ref([])
const feedback = ref(null)
const err = ref(null)
const loadingState = ref(true)
const answering = ref(false)

const { seconds, formatted, deadline, start: cdStart, stop: cdStop, resync: cdResync } = useCountdown({
  onFinish: onTimeout,
})

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

const advancing = ref(false)
const advanceDeadline = ref(null)
let advanceRaf = null
const advanceTotalMs = ref(0)

function cardStatus(c) {
  if (!feedback.value) {
    return selected.value.includes(c.id) ? 'selected' : 'idle'
  }
  const isCorrect = feedback.value.correct_choice_ids.includes(c.id)
  const isSelected = selected.value.includes(c.id)
  if (isCorrect && isSelected) return 'correct'
  if (!isCorrect && isSelected) return 'wrong'
  if (isCorrect && !isSelected) return 'skipped'
  return 'idle'
}

const cardShape = computed(() => (question.value && question.value.type === 'multiple' ? 'rect' : 'rounded'))

onMounted(() => {
  loadState()
  document.addEventListener('keydown', onKeyDown)
  document.addEventListener('visibilitychange', onVisibilityChange)
  window.addEventListener('beforeunload', onBeforeUnload)
})

onBeforeUnmount(() => {
  cdStop()
  stopAdvanceTimer()
  document.removeEventListener('keydown', onKeyDown)
  document.removeEventListener('visibilitychange', onVisibilityChange)
  window.removeEventListener('beforeunload', onBeforeUnload)
})

async function loadState() {
  loadingState.value = true
  err.value = null
  try {
    const res = await playApi.state(token)
    const d = res.data
    if (d.status === 'finished') {
      router.replace({ name: 'result', params: { token } })
      return
    }
    index.value = d.index
    total.value = d.total
    timeLimit.value = d.time_limit
    phase.value = d.phase
    isLast.value = d.is_last
    feedback.value = null
    err.value = null
    stopAdvanceTimer()
    if (d.phase === 'feedback') {
      feedback.value = d.feedback || null
      if (d.question) question.value = d.question
      selected.value = (feedback.value && feedback.value.selected_choice_ids) || []
      cdStop()
      const delay = (feedback.value && feedback.value.explanation && feedback.value.explanation.trim()) ? 8 : 5
      startAdvanceTimer(delay)
      return
    }
    question.value = d.question
    selected.value = []
    cdStart(d.seconds_left ?? d.time_limit)
  } catch (e) {
    err.value = e.response && e.response.data && e.response.data.error ? e.response.data.error : 'Không lấy được trạng thái câu hỏi.'
  } finally {
    loadingState.value = false
  }
}

function toggleChoice(id) {
  const s = selected.value
  if (s.includes(id)) selected.value = s.filter((x) => x !== id)
  else selected.value = [...s, id]
}

function selectChoice(id) {
  if (answering.value || phase.value !== 'question') return
  if (question.value.type === 'single') {
    selected.value = [id]
  } else {
    toggleChoice(id)
  }
}

async function commitAnswer() {
  if (answering.value || selected.value.length === 0 || phase.value !== 'question') return
  await submitAnswer([...selected.value])
}

async function submitAnswer(ids) {
  answering.value = true
  try {
    const res = await playApi.answer(token, question.value.id, ids)
    const fb = res.data.feedback
    feedback.value = fb
    phase.value = 'feedback'
    isLast.value = res.data.is_last
    cdStop()
    stopAdvanceTimer()
    const delay = (fb && fb.explanation && fb.explanation.trim()) ? 8 : 5
    advanceTotalMs.value = delay
    startAdvanceTimer(delay)
  } catch (e) {
    err.value = e.response && e.response.data && e.response.data.error ? e.response.data.error : 'Không nộp được đáp án.'
    answering.value = false
  }
}

function onTimeout() {
  if (phase.value !== 'question') return
  submitAnswer([...selected.value])
}

async function nextQuestion() {
  if (answering.value) return
  answering.value = true
  stopAdvanceTimer()
  try {
    const res = await playApi.next(token)
    const d = res.data
    if (d.status === 'finished') {
      router.replace({ name: 'result', params: { token } })
      return
    }
    question.value = d.question
    index.value = d.index
    total.value = d.total
    timeLimit.value = d.time_limit
    phase.value = d.phase
    isLast.value = d.is_last
    selected.value = []
    feedback.value = null
    err.value = null
    cdStart(d.seconds_left ?? d.time_limit)
  } catch (e) {
    err.value = e.response && e.response.data && e.response.data.error ? e.response.data.error : 'Không lấy câu tiếp theo.'
  } finally {
    answering.value = false
  }
}

function startAdvanceTimer(delaySeconds) {
  stopAdvanceTimer()
  advanceDeadline.value = Date.now() + Math.max(0, delaySeconds) * 1000
  advancing.value = true
  advanceTick()
}

function advanceTick() {
  if (!advancing.value || !advanceDeadline.value) return
  if (Date.now() >= advanceDeadline.value) {
    stopAdvanceTimer()
    nextQuestion()
    return
  }
  advanceRaf = requestAnimationFrame(advanceTick)
}

function stopAdvanceTimer() {
  advancing.value = false
  advanceDeadline.value = null
  if (advanceRaf) {
    cancelAnimationFrame(advanceRaf)
    advanceRaf = null
  }
}

function advanceSeconds() {
  if (!advanceDeadline.value) return 0
  return Math.max(0, Math.ceil((advanceDeadline.value - Date.now()) / 1000))
}

function advancePct() {
  if (!advanceDeadline.value) return 0
  return Math.max(0, Math.min(100, (1 - (advanceDeadline.value - Date.now()) / (advanceTotalMs.value * 1000)) * 100))
}

function onKeyDown(e) {
  if (answering.value || !question.value) return
  const letterIdx = 'ABCDEF'.indexOf(e.key.toUpperCase())
  const digitIdx = '123456'.indexOf(e.key)
  const optIdx = digitIdx >= 0 ? digitIdx : letterIdx >= 0 ? letterIdx : -1
  const choices = question.value.choices || []
  if (optIdx >= 0 && optIdx < choices.length) {
    e.preventDefault()
    selectChoice(choices[optIdx].id)
  } else if (e.key === 'Enter' && phase.value === 'question') {
    e.preventDefault()
    commitAnswer()
  } else if (e.key === 'Enter' && phase.value === 'feedback') {
    e.preventDefault()
    nextQuestion()
  }
}

function onVisibilityChange() {
  if (document.hidden) {
    playApi.event(token, 'tab_hidden').catch(() => {})
  } else if (phase.value === 'question') {
    playApi.state(token).then((res) => {
      const d = res.data
      if (d.phase === 'question') {
        cdResync(d.seconds_left ?? d.time_limit)
      }
    }).catch(() => {})
  }
}

function onBeforeUnload(e) {
  if (phase.value === 'question' && !feedback.value) {
    e.preventDefault()
    e.returnValue = ''
  }
}
</script>

<template>
  <div class="q-play-wrap">
    <div v-if="loadingState" class="q-state">
      <div class="q-spinner"></div>
      <div class="q-state-title">Đang tải câu hỏi...</div>
    </div>
    <div v-else-if="err" class="q-state">
      <div class="q-state-title">Có lỗi xảy ra</div>
      <div class="q-text-soft">{{ err }}</div>
      <button class="q-btn q-btn-primary mt-3" @click="loadState">Thử lại</button>
    </div>
    <div v-else class="q-play-card">
      <div class="q-play-top">
        <div class="q-play-progress">
          <div class="q-text-soft">Câu hỏi</div>
          <div class="q-play-counter">Câu <span style="color: var(--q-brand); font-weight: 700">{{ index + 1 }}</span> / {{ total }}</div>
        </div>
        <div class="q-countdown-col">
          <CountdownRing :seconds="seconds" :limit="timeLimit" :deadline="deadline" />
          <div class="q-ring-text" :class="{ 'q-ring-text--warn': seconds <= 5 }">{{ formatted }}</div>
        </div>
      </div>
      <div class="q-question-panel" v-if="question">
        <div class="q-question-content" v-text="question.content"></div>
        <img v-if="question.image_url" :src="question.image_url" :alt="question.content" class="q-question-img" />
        <div class="q-options">
          <OptionCard
            v-for="(c, i) in question.choices"
            :key="c.id"
            :letter="LETTERS[i]"
            :content="c.content"
            :id="c.id"
            :shape="cardShape"
            :status="cardStatus(c)"
            @pick="selectChoice(c.id)"
          />
        </div>
        <div v-if="feedback" class="q-feedback" :class="{ 'q-feedback--ok': feedback.is_correct, 'q-feedback--bad': !feedback.is_correct && !feedback.timed_out, 'q-feedback--timeout': feedback.timed_out }">
          <span class="q-feedback-icon">{{ feedback.timed_out ? 'Hết giờ!' : (feedback.is_correct ? 'Chính xác!' : 'Sai rồi!') }}</span>
          <div v-if="feedback.explanation" class="q-feedback-expl">{{ feedback.explanation }}</div>
        </div>
        <div v-if="phase === 'question'" class="q-actions">
          <button
            class="q-btn q-btn-primary q-btn-full q-commit"
            :class="{ 'q-commit--warn': seconds <= 5 }"
            :disabled="selected.length === 0 || answering"
            @click="commitAnswer"
          >
            Chốt!
          </button>
        </div>
        <div v-if="phase === 'feedback'" class="q-advance">
          <div class="q-advance-bar">
            <div class="q-advance-fill" :style="{ width: advancePct() + '%' }"></div>
          </div>
          <div class="q-advance-text">{{ isLast ? 'Đang chuyển tới kết quả...' : 'Sang câu sau trong ' + advanceSeconds() + 's' }}</div>
        </div>
        <div v-if="phase === 'question'" class="q-hint">
          <span>1-6 / A-F: chọn</span>
          <span>&bull; Enter: chốt đáp án</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.q-commit--warn {
  animation: q-blink 1.2s ease-in-out infinite;
}
@keyframes q-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.55; }
}
.q-advance {
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.q-advance-bar {
  width: 100%;
  height: 6px;
  background: #E2E8F0;
  border-radius: 999px;
  overflow: hidden;
}
.q-advance-fill {
  height: 100%;
  background: var(--q-brand);
  transition: width 0.1s linear;
}
.q-advance-text {
  font-size: 0.95rem;
  color: var(--q-text-soft);
}
@media (prefers-reduced-motion: reduce) {
  .q-commit--warn { animation: none; }
  .q-advance-fill { transition: none !important; }
}
</style>
