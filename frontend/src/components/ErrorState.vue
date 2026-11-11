<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  message: { type: [String, Object, Function], default: 'Có lỗi xảy ra.' },
  retry: { type: Function, default: null },
  backLabel: { type: String, default: 'Về danh sách bộ đề' },
  backRoute: { type: String, default: 'teacher' },
})

const router = useRouter()

const safeMessage = computed(() => {
  if (typeof props.message === 'string' && props.message.trim()) {
    return props.message
  }
  return 'Đã có lỗi xảy ra. Vui lòng thử lại.'
})
</script>

<template>
  <div class="q-state">
    <div class="q-error-icon">&#128310;</div>
    <div class="q-state-title">Có lỗi xảy ra</div>
    <div class="q-error-message" v-text="safeMessage"></div>
    <div class="q-error-actions">
      <button v-if="props.retry" class="q-btn q-btn-primary" @click="props.retry">Thử lại</button>
      <button class="q-btn q-btn-outline" @click="router.push({ name: props.backRoute })">{{ props.backLabel }}</button>
    </div>
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
.q-error-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}
.q-state-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--q-text);
  margin-bottom: 8px;
}
.q-error-message {
  font-size: 0.98rem;
  color: var(--q-text-soft);
  max-width: 360px;
  margin-bottom: 20px;
  line-height: 1.6;
}
.q-error-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}
</style>