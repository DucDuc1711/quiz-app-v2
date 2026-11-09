<template>
  <div class="q-auth-wrap">
    <div class="q-auth-card q-panel q-pad">
      <div class="q-auth-header">
        <span class="q-mark">Q</span>uiz App
      </div>
      <h2 class="q-auth-title">{{ title }}</h2>
      <p class="q-auth-sub">{{ subtitle }}</p>

      <div v-if="error" class="q-auth-error">{{ error }}</div>

      <form @submit.prevent="handleSubmit" class="q-auth-form">
        <slot name="form"></slot>
        <button
          type="submit"
          class="q-btn q-btn-primary q-btn-full"
          :disabled="loading"
        >
          {{ loading ? 'Đang xử lý...' : submitLabel }}
        </button>
      </form>

      <div v-if="showToggle" class="q-auth-toggle">
        <span>{{ toggleBefore }}</span>
        <a class="q-link" @click="handleToggle">{{ toggleText }}</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  submitLabel: { type: String, required: true },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  showToggle: { type: Boolean, default: true },
  toggleBefore: { type: String, default: '' },
  toggleText: { type: String, default: '' },
})

const emit = defineEmits(['submit', 'toggle'])

const handleSubmit = () => {
  emit('submit')
}

const handleToggle = () => {
  emit('toggle')
}
</script>

<style scoped>
.q-auth-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - var(--q-header-height));
  padding: 24px;
}
.q-auth-card {
  width: 100%;
  max-width: 400px;
}
.q-auth-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--q-brand);
  margin-bottom: 24px;
}
.q-mark {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: var(--q-brand);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
}
.q-auth-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: var(--q-text);
}
.q-auth-sub {
  font-size: 0.95rem;
  color: var(--q-text-soft);
  margin: 0 0 24px 0;
}
.q-auth-error {
  margin-bottom: 16px;
  padding: 8px 12px;
  background: var(--q-danger-bg);
  border: 1px solid var(--q-danger);
  border-radius: var(--q-radius-md);
  color: var(--q-danger-text);
  font-size: 0.9rem;
}
.q-auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.q-auth-toggle {
  margin-top: 24px;
  text-align: center;
  font-size: 0.95rem;
  color: var(--q-text-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.q-link {
  color: var(--q-brand);
  font-weight: 600;
}
.q-link:hover {
  text-decoration: underline;
}
@media (max-width: 360px) {
  .q-auth-wrap {
    padding: 12px;
  }
  .q-auth-card {
    max-width: 100%;
    padding: 20px 24px;
  }
}
</style>
