<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="q-state">
    <div class="q-state-title">404 - Trang khong ton tai</div>
    <div class="q-text-soft">Duong dan ban dang xem khong co trong he thong.</div>
    <button class="q-btn q-btn-primary mt-3" @click="router.push('/')">Ve trang chu</button>
  </div>
</template>