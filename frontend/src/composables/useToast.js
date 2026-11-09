import { ref } from 'vue'

const toasts = ref([])
let idCounter = 0

export function useToast() {
  function add({ type = 'success', message, title = '', duration = 4000 }) {
    const id = ++idCounter
    toasts.value.push({
      id,
      type, // 'success' | 'error'
      message,
      title,
      duration,
    })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, duration)
    return id
  }

  function success(message, title = 'Thành công', duration = 4000) {
    return add({ type: 'success', message, title, duration })
  }

  function error(message, title = 'Có lỗi xảy ra', duration = 5000) {
    return add({ type: 'error', message, title, duration })
  }

  function remove(id) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  return { toasts, success, error, remove }
}

export default { toasts, useToast }