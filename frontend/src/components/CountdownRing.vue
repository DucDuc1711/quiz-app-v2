<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  seconds: { type: Number, default: 0 },
  limit: { type: Number, default: 30 },
  deadline: { type: Number, default: null }, // moc thoi gian (ms) hoac null
})

const radius = 24
const cx = 28
const cy = 28
const circumference = 2 * Math.PI * radius

const ratio = ref(1) // ty le thoi gian con lai (0 den 1), cap nhat tu tu
let raf = null

function tick() {
  if (!props.deadline) {
    ratio.value = 1
    raf = requestAnimationFrame(tick)
    return
  }
  const remain = props.deadline - Date.now()
  ratio.value = Math.max(0, Math.min(1, remain / Math.max(1, props.limit * 1000)))
  raf = requestAnimationFrame(tick)
}

onMounted(tick)
onUnmounted(() => {
  if (raf) {
    cancelAnimationFrame(raf)
    raf = null
  }
})

// Khi deadline duoc cap nhat tu cha (resync), tiep tuc chay tick doc gia tri moi.
watch(
  () => props.deadline,
  () => {
    if (!raf) tick()
  }
)

const warn = computed(() => (props.seconds || 0) <= 5 && (props.seconds || 0) > 0)
</script>

<template>
  <div class="q-ring-wrap" :class="{ 'q-ring--warn': warn }">
    <!-- Bieu tuong dong ho bao thuc (SVG) -->
    <svg class="q-clock-icon" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="9.5" fill="none" stroke="#94A3B8" stroke-width="1.5"></circle>
      <path d="M12 7V5l2 2-2 2" fill="none" stroke="#64748B" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path>
      <circle cx="12" cy="12" r="1.2" fill="#64748B"></circle>
    </svg>

    <svg class="q-ring" viewBox="0 0 56 56">
      <circle class="q-ring-bg" :cx="cx" :cy="cy" :r="radius" stroke="#E2E8F0" stroke-width="4" fill="none"></circle>
      <circle
        class="q-ring-fg"
        :cx="cx"
        :cy="cy"
        :r="radius"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="circumference * (1 - ratio.value)"
        :class="{ 'q-ring-fg--danger': warn }"
        stroke-width="4"
        stroke-linecap="round"
        fill="none"
      ></circle>
    </svg>

    <!-- So giay nguyen (lam tron len) o giua mat dong ho -->
    <div class="q-clock-number" :class="{ 'q-clock-number--warn': warn }">{{ Math.max(0, Math.ceil(seconds || 0)) }}</div>
  </div>
</template>

<style scoped>
.q-ring-wrap {
  position: relative;
  width: 88px;
  height: 88px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.q-clock-icon {
  position: absolute;
  width: 30px;
  height: 30px;
  z-index: 2;
}
.q-ring {
  width: 88px;
  height: 88px;
  transform: rotate(-90deg);
  z-index: 1;
}
.q-ring-bg {
  opacity: 0.35;
}
.q-ring-fg {
  stroke: var(--q-brand, #6C5CE7);
  transition: stroke-dashoffset 0.15s linear;
}
.q-ring-fg--danger { stroke: var(--q-danger, #B91C1C); }
.q-ring--warn .q-ring-fg {
  animation: q-ring-pulse 1.2s ease-in-out infinite;
}
.q-clock-number {
  position: absolute;
  z-index: 3;
  font-weight: 800;
  font-size: 1.5rem;
  line-height: 1;
  color: var(--q-text);
  transition: color 0.2s ease;
}
.q-clock-number--warn {
  color: var(--q-danger, #B91C1C);
  animation: q-shake 0.5s ease-in-out infinite;
}
@keyframes q-ring-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
@keyframes q-shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-2px); }
  75% { transform: translateX(2px); }
}

@media (prefers-reduced-motion: reduce) {
  .q-ring--warn .q-ring-fg { animation: none; }
  .q-clock-number--warn { animation: none; }
  .q-ring-fg { transition: none !important; }
}
</style>
