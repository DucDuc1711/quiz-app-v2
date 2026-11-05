<script setup>
import { useRoute } from 'vue-router'

const props = defineProps({
  label: { type: String, default: 'Trang nay' },
})
const route = useRoute()
</script>

<template>
  <div class="q-state">
    <div class="q-state-title">Sap co</div>
    <div class="q-text-soft">Trang "{{ label }}" dang phat trien (P5/P6).</div>
    <button class="q-btn q-btn-primary mt-3" @click="$router.push('/')">Ve trang chu</button>
  </div>
</template>