<script setup>
const props = defineProps({
  message: { type: String, default: 'Dang tai...' },
})
</script>

<template>
  <div class="q-state">
    <div class="q-spinner"></div>
    <div class="q-state-title">{{ props.message }}</div>
  </div>
</template>

<style scoped>
.q-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 64px 24px;
}
.q-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--q-muted);
  border-top-color: var(--q-brand);
  border-radius: 50%;
  animation: q-spin 0.8s linear infinite;
  margin-bottom: 16px;
}
@keyframes q-spin {
  to { transform: rotate(360deg); }
}
.q-state-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--q-text-soft);
}
@media (prefers-reduced-motion: reduce) {
  .q-spinner { animation-duration: 0.01s !important; }
}
</style>