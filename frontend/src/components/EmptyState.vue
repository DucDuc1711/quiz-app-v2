<script setup>
const props = defineProps({
  message: { type: String, default: 'Khong co du lieu.' },
  hint: { type: String, default: '' },
})
</script>

<template>
  <div class="q-state">
    <div class="q-empty-icon">&#129369;</div>
    <div class="q-state-title">{{ props.message }}</div>
    <div v-if="props.hint" class="q-empty-hint">{{ props.hint }}</div>
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
.q-empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
  opacity: 0.6;
}
.q-state-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--q-text);
  margin-bottom: 8px;
}
.q-empty-hint {
  font-size: 0.95rem;
  color: var(--q-text-soft);
  max-width: 320px;
}
</style>