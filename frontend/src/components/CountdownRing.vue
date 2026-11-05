<script setup>
import { computed } from 'vue'

const props = defineProps({
  seconds: { type: Number, default: 0 },
  limit: { type: Number, default: 30 },
})

const radius = 24
const cx = 28
const cy = 28
const circumference = computed(() => 2 * Math.PI * radius)

const ratio = computed(() => Math.max(0, Math.min(1, (props.seconds || 0) / Math.max(1, props.limit || 30))))
const offset = computed(() => circumference.value * (1 - ratio.value))
const warn = computed(() => (props.seconds || 0) <= 5 && (props.seconds || 0) > 0)
</script>

<template>
  <div class="q-ring-wrap" :class="{ 'q-ring--warn': warn }">
    <svg class="q-ring" viewBox="0 0 56 56">
      <circle class="q-ring-bg" :cx="cx" :cy="cy" :r="radius" stroke="#E2E8F0" stroke-width="4" fill="none"></circle>
      <circle
        class="q-ring-fg"
        :cx="cx"
        :cy="cy"
        :r="radius"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="offset"
        :stroke="warn ? '#DC2626' : '#6C5CE7'"
        stroke-width="4"
        stroke-linecap="round"
        fill="none"
      ></circle>
    </svg>
  </div>
</template>