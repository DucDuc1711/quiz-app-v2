<template>
  <div class="q-password-wrap">
    <input
      ref="inputRef"
      class="q-form-control q-password-input"
      :type="showPassword ? 'text' : 'password'"
      :value="modelValue"
      @input="emit('update:modelValue', $event.target.value)"
      :aria-label="ariaLabel || 'Mật khẩu'"
      :autocomplete="autocomplete"
      autocapitalize="off"
      autocorrect="off"
      spellcheck="false"
      :disabled="disabled"
      :placeholder="placeholder"
      :class="{ 'q-form-error': error }"
    />
    <button
      type="button"
      class="q-password-toggle"
      @click="showPassword = !showPassword"
      :aria-label="showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'"
      :disabled="disabled"
    >
      {{ showPassword ? 'Ẩn' : 'Hiện' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  ariaLabel: { type: String, default: '' },
  autocomplete: { type: String, default: 'current-password' },
  disabled: { type: Boolean, default: false },
  error: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])
const showPassword = ref(false)
</script>

<style scoped></style>
