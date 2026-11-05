<script setup>
import { computed } from 'vue'

const props = defineProps({
  letter: { type: String, required: true },
  content: { type: String, required: true },
  id: { type: [Number, String], required: true },
  selected: { type: Boolean, default: false },
  correct: { type: Boolean, default: false },
  wrong: { type: Boolean, default: false },
  faded: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['pick'])

const LETTER_COLORS = {
  A: '#8B5CF6',
  B: '#2563EB',
  C: '#EA580C',
  D: '#DB2777',
  E: '#0891B2',
  F: '#D97706',
}

const letterStyle = computed(() => ({
  backgroundColor: LETTER_COLORS[props.letter] || '#6C5CE7',
}))

function pick() {
  if (props.disabled) return
  emit('pick')
}
</script>

<template>
  <div
    class="q-opt"
    :class="[
      'q-opt-' + props.letter.toLowerCase(),
      { 'q-opt-selected': props.selected, 'q-opt-correct': props.correct, 'q-opt-wrong': props.wrong, 'q-opt-faded': props.faded, 'q-opt-disabled': props.disabled },
    ]"
    @click="pick"
  >
    <div class="q-opt-letter" :style="letterStyle">{{ props.letter }}</div>
    <div class="q-opt-content" v-text="props.content"></div>
    <span class="q-opt-mark" v-if="props.correct">&#10003;</span>
    <span class="q-opt-mark" v-if="props.wrong">&#10007;</span>
  </div>
</template>