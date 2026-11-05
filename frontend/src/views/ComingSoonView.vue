<script setup>
import { useRoute } from 'vue-router'

const props = defineProps({
  label: { type: String, default: 'Trang nay' },
})
const route = useRoute()
</script>

<template>
  <div class="q-state">
    <div class="q-state-title">Sắp có</div>
    <div class="q-text-soft">Trang "{{ label }}" đang phát triển (P5/P6).</div>
    <button class="q-btn q-btn-primary mt-3" @click="$router.push('/')">Về trang chủ</button>
  </div>
</template>