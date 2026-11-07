<script setup>
import { computed } from 'vue'

const props = defineProps({
  letter: { type: String, required: true },
  content: { type: String, required: true },
  id: { type: [Number, String], required: true },
  shape: { type: String, default: 'rounded' },
  status: { type: String, default: 'idle' },
})

const emit = defineEmits(['pick'])

const LETTER_COLORS = {
  A: '#7C3AED',
  B: '#2563EB',
  C: '#EA580C',
  D: '#DB2777',
  E: '#0369A1',
  F: '#D97706',
}

const letterStyle = computed(() => ({
  backgroundColor: LETTER_COLORS[props.letter] || '#6C5CE7',
}))

const classes = computed(() => {
  const cls = ['q-opt', 'q-opt-' + props.letter.toLowerCase()]
  const map = {
    idle: 'q-opt-idle',
    selected: 'q-opt-selected',
    correct: 'q-opt-correct',
    wrong: 'q-opt-wrong',
    skipped: 'q-opt-skipped',
  }
  if (map[props.status]) cls.push(map[props.status])
  if (props.shape === 'rect') cls.push('q-opt-rect')
  else cls.push('q-opt-rounded')
  return cls
})

function pick() {
  emit('pick')
}
</script>

<template>
  <div :class="classes" @click="pick">
    <div class="q-opt-letter" :style="letterStyle">{{ props.letter }}</div>
    <div class="q-opt-content" v-text="props.content"></div>
    <span class="q-opt-mark q-opt-mark-ok" v-if="props.status === 'correct'">&#10003;</span>
    <span class="q-opt-mark q-opt-mark-wrong" v-if="props.status === 'wrong'">&#10007;</span>
    <span class="q-opt-mark q-opt-mark-skipped" v-if="props.status === 'skipped'">
      &#10003; <span class="q-opt-label">Bỏ sót</span>
    </span>
  </div>
</template>

<style scoped>
.q-opt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 16px 12px;
  border: 2px solid var(--q-border);
  border-radius: var(--q-radius-md);
  background: var(--q-card);
  min-height: var(--q-touch-min);
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
  text-align: center;
}
.q-opt-rounded {
  border-radius: 44px;
}
.q-opt-rect {
  border-radius: 8px;
}
.q-opt-letter {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  font-size: 1.15rem;
  margin-bottom: 6px;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0,0,0,0.12);
}
.q-opt-content {
  font-size: 1.08rem;
  line-height: 1.4;
  font-weight: 600;
  color: var(--q-text);
}
.q-opt-idle:hover {
  border-color: var(--q-brand);
  background: var(--q-card-hover);
  box-shadow: var(--q-shadow-sm);
}
.q-opt-selected {
  border-color: var(--q-brand);
  background: #F3F0FF;
  box-shadow: 0 0 0 4px rgba(108, 92, 231, 0.2);
}
.q-opt-correct {
  background: var(--q-success-bg);
  border: 2px solid var(--q-success);
  color: var(--q-success-text);
  animation: none;
}
.q-opt-wrong {
  background: var(--q-danger-bg);
  border: 2px solid var(--q-danger);
  color: var(--q-danger-text);
  animation: none;
}
.q-opt-skipped {
  background: var(--q-success-bg);
  border: 2px dashed var(--q-success);
  color: var(--q-success-text);
}
.q-opt-mark {
  font-weight: 800;
  font-size: 1.15rem;
  margin-left: auto;
}
.q-opt-mark-ok { color: var(--q-success); }
.q-opt-mark-wrong { color: var(--q-danger); }
.q-opt-mark-skipped { color: var(--q-success); }
.q-opt-label {
  font-size: 0.78rem;
  font-weight: 700;
  margin-left: 4px;
}
@media (prefers-reduced-motion: reduce) {
  .q-opt-correct { animation: none; }
  .q-opt-wrong { animation: none; }
}
</style>
