<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
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

const { seconds, formatted, start: cdStart, stop: cdStop, resync: cdResync } = useCountdown(0, {
  onFinish: onTimeout,
})

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

const FB_PREFIX = 'qfb_' + token + '_'
function fbCacheSet(idx, fb) {
  try { sessionStorage.setItem(FB_PREFIX + idx, JSON.stringify(fb)) } catch (_) {}
}
function fbCacheGet(idx) {
  try { return JSON.parse(sessionStorage.getItem(FB_PREFIX + idx) || 'null') } catch (_) { return null }
}

onMounted(() => {
  loadState()
  document.addEventListener('keydown', onKeyDown)
  document.addEventListener('visibilitychange', onVisibilityChange)
  window.addEventListener('beforeunload', onBeforeUnload)
})

onBeforeUnmount(() => {
  cdStop()
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
    question.value = d.question
    index.value = d.index
    total.value = d.total
    timeLimit.value = d.time_limit
    phase.value = d.phase
    isLast.value = d.is_last
    selected.value = []
    feedback.value = null
    if (d.phase === 'feedback') {
      const cached = fbCacheGet(d.index)
      if (cached) {
        feedback.value = cached
        cdStop()
        return
      }
    }
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

async function submitChoice(choiceId) {
  if (answering.value || phase.value !== 'question') return
  if (question.value.type === 'single') {
    await submitAnswer([choiceId])
  } else {
    toggleChoice(choiceId)
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
    fbCacheSet(res.data.index, fb)
    phase.value = 'feedback'
    isLast.value = res.data.is_last
    cdStop()
  } catch (e) {
    err.value = e.response && e.response.data && e.response.data.error ? e.response.data.error : 'Gửi đáp án thất bại. Vui lòng thử lại.'
  } finally {
    answering.value = false
  }
}

async function onTimeout() {
  if (phase.value !== 'question') return
  await submitAnswer(selected.value.length ? [...selected.value] : [])
}

async function nextQuestion() {
  if (answering.value || phase.value !== 'feedback') return
  answering.value = true
  try {
    const res = await playApi.next(token)
    if (res.data.status === 'finished') {
      router.replace({ name: 'result', params: { token } })
      return
    }
    question.value = res.data.question
    index.value = res.data.index
    total.value = res.data.total
    timeLimit.value = res.data.time_limit
    phase.value = res.data.phase
    isLast.value = res.data.is_last
    selected.value = []
    feedback.value = null
    cdStart(res.data.seconds_left ?? res.data.time_limit)
  } catch (e) {
    err.value = e.response && e.response.data && e.response.data.error ? e.response.data.error : 'Không lấy được câu tiếp theo.'
  } finally {
    answering.value = false
  }
}

async function onVisibilityChange() {
  if (document.hidden) {
    try { await playApi.event(token, 'tab_hidden') } catch (_) {}
  } else {
    try {
      const res = await playApi.state(token)
      const d = res.data
      if (d.status === 'finished') {
        router.replace({ name: 'result', params: { token } })
        return
      }
      if (d.index === index.value && d.phase === 'question') cdResync(d.seconds_left)
    } catch (_) {}
  }
}

function onKeyDown(e) {
  if (loadingState.value || answering.value) return
  const key = e.key
  if (phase.value === 'feedback') {
    if (key === 'Enter') { nextQuestion(); e.preventDefault() }
    return
  }
  const idx = '123456'.indexOf(key)
  const letterIdx = 'ABCDEF'.indexOf(key.toUpperCase())
  const optIdx = idx >= 0 ? idx : letterIdx >= 0 ? letterIdx : -1
  const choices = question.value ? question.value.choices : []
  if (optIdx >= 0 && optIdx < choices.length) {
    e.preventDefault()
    submitChoice(choices[optIdx].id)
  } else if (key === 'Enter' && question.value && question.value.type === 'multiple') {
    commitAnswer()
    e.preventDefault()
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
          <CountdownRing :seconds="seconds" :limit="timeLimit" />
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
            :selected="selected.includes(c.id)"
            :correct="feedback && feedback.correct_choice_ids.includes(c.id)"
            :wrong="feedback && phase === 'feedback' && selected.includes(c.id) && !feedback.correct_choice_ids.includes(c.id)"
            :faded="phase === 'feedback'"
            :disabled="phase === 'feedback'"
            @pick="submitChoice(c.id)"
          />
        </div>
        <div v-if="feedback" class="q-feedback" :class="{ 'q-feedback--ok': feedback.is_correct, 'q-feedback--bad': !feedback.is_correct && !feedback.timed_out, 'q-feedback--timeout': feedback.timed_out }">
          <span class="q-feedback-icon">{{ feedback.timed_out ? 'Hết giờ!' : (feedback.is_correct ? 'Chính xác!' : 'Sai rồi!') }}</span>
          <div v-if="feedback.explanation" class="q-feedback-expl">{{ feedback.explanation }}</div>
        </div>
        <div v-if="phase === 'feedback'" class="q-actions">
          <button class="q-btn q-btn-primary q-btn-full" @click="nextQuestion">{{ isLast ? 'Xem kết quả' : 'Câu tiếp' }}</button>
        </div>
        <div v-if="phase === 'question'" class="q-hint">
          <span>1-6 / A-F: chọn</span>
          <span v-if="question.type === 'multiple'">&#8226; Enter: chốt đáp án</span>
        </div>
        <button v-if="question.type === 'multiple' && phase === 'question'" class="q-btn q-btn-outline q-commit mt-3" @click="commitAnswer" :disabled="selected.length === 0">
          Chốt đáp án
        </button>
      </div>
    </div>
  </div>
</template>