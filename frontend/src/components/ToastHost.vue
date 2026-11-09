<script setup>
import { useToast } from '@/composables/useToast'

const { toasts, remove } = useToast()

const typeClass = (type) => (type === 'error' ? 'q-toast--error' : 'q-toast--success')
const typeIcon = (type) => (type === 'error' ? '\u26A0' : '\u2713')
</script>

<template>
  <div class="q-toast-host" aria-live="polite" aria-visible="true">
    <div
      v-for="t in toasts"
      :key="t.id"
      class="q-toast"
      :class="typeClass(t.type)"
      role="alert"
      aria-label="{{ t.title }}: {{ t.message }}"
    >
      <span class="q-toast-icon">{{ typeIcon(t.type) }}</span>
      <div class="q-toast-content">
        <div v-if="t.title" class="q-toast-title">{{ t.title }}</div>
        <div class="q-toast-message">{{ t.message }}</div>
      </div>
      <button class="q-toast-close" @click="remove(t.id)" aria-label="Dong thong bao">&#215;</button>
    </div>
  </div>
</template>

<style scoped>
.q-toast-host {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}
.q-toast {
  pointer-events: auto;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  border-radius: var(--q-radius-lg);
  box-shadow: var(--q-shadow);
  min-width: 300px;
  max-width: 500px;
  animation: q-toast-slide 0.3s ease;
  border: 1px solid var(--q-border);
  background: var(--q-card);
  color: var(--q-text);
}
.q-toast--success {
  border-color: var(--q-success);
  background: var(--q-success-bg);
  color: var(--q-success-text);
}
.q-toast--error {
  border-color: var(--q-danger);
  background: var(--q-danger-bg);
  color: var(--q-danger-text);
}
.q-toast-icon {
  flex-shrink: 0;
  font-weight: 800;
  font-size: 1.25rem;
}
.q-toast-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}
.q-toast-title {
  font-weight: 700;
  font-size: 0.95rem;
}
.q-toast-message {
  font-size: 0.9rem;
  opacity: 0.95;
}
.q-toast-close {
  flex-shrink: 0;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  opacity: 0.7;
}
.q-toast-close:hover {
  opacity: 1;
}
@keyframes q-toast-slide {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
@media (prefers-reduced-motion: reduce) {
  @keyframes q-toast-slide {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  .q-toast { animation-duration: 0.01s !important; }
}
</style>