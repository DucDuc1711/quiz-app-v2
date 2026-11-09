<script setup>
import { ref } from 'vue'

const props = defineProps({
  title: { type: String, default: 'Xac nhan thao tac' },
  message: { type: String, required: true },
  confirmLabel: { type: String, default: 'Xac nhan' },
  cancelLabel: { type: String, default: 'Huy' },
  confirmVariant: { type: String, default: 'danger' }, // 'danger' | 'primary'
  visible: { type: Boolean, default: true },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['confirm', 'cancel'])

const ok = ref(false)

function onConfirm() {
  ok.value = true
  emit('confirm')
}
function onCancel() {
  emit('cancel')
}
function onClose() {
  emit('cancel')
}
</script>

<template>
  <teleport to="body">
    <div v-if="props.visible" class="q-dialog-overlay" @click="onClose"></div>
    <div v-if="props.visible" class="q-dialog" role="dialog" aria-modal="true" aria-label="{{ props.title }}">
      <div class="q-dialog-card">
        <div class="q-dialog-title">{{ props.title }}</div>
        <div class="q-dialog-message" v-text="props.message"></div>
        <div class="q-dialog-actions">
          <button class="q-btn q-btn-outline" @click="onCancel">{{ props.cancelLabel }}</button>
          <button
            :class="['q-btn', `q-btn-${props.confirmVariant}`]"
            @click="onConfirm"
            :disabled="props.loading"
          >
            {{ props.loading ? 'Dang xu ly...' : props.confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<style scoped>
.q-dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(2px);
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: q-fade-in 0.2s ease;
}
.q-dialog {
  width: 90%;
  max-width: 480px;
  z-index: 3001;
  animation: q-dialog-zoom 0.25s ease;
}
.q-dialog-card {
  background: var(--q-card);
  border: 1px solid var(--q-border);
  border-radius: var(--q-radius-xl);
  box-shadow: var(--q-shadow);
  padding: 28px 32px;
  color: var(--q-text);
}
.q-dialog-title {
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 12px;
}
.q-dialog-message {
  font-size: 0.98rem;
  line-height: 1.6;
  color: var(--q-text-soft);
  margin-bottom: 24px;
  white-space: pre-wrap;
}
.q-dialog-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
@keyframes q-dialog-zoom {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
@keyframes q-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
@media (prefers-reduced-motion: reduce) {
  .q-dialog-overlay, .q-dialog { animation-duration: 0.01s !important; }
}
</style>