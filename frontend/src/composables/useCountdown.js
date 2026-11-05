import { ref, computed } from 'vue'

export function useCountdown(initialSeconds, { onTick, onFinish } = {}) {
  const seconds = ref(Math.max(0, Math.floor(initialSeconds || 0)))
  const running = ref(false)
  let timer = null

  const formatted = computed(() => {
    const m = Math.floor(seconds.value / 60)
    const s = seconds.value % 60
    return m + ':' + String(s).padStart(2, '0')
  })

  function tick() {
    if (!running.value) return
    if (onTick) onTick(seconds.value)
    if (seconds.value <= 0) {
      stop()
      running.value = false
      if (onFinish) onFinish()
      return
    }
    seconds.value -= 1
  }

  function start(startSeconds) {
    stop()
    seconds.value = Math.max(0, Math.floor(startSeconds || 0))
    running.value = true
    tick()
    timer = setInterval(tick, 1000)
  }

  function stop() {
    running.value = false
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  function reset(nextSeconds) {
    stop()
    seconds.value = Math.max(0, Math.floor(nextSeconds || 0))
  }

  function resync(serverSeconds) {
    const v = Math.max(0, Math.floor(serverSeconds || 0))
    seconds.value = v
    if (v <= 0 && running.value) {
      stop()
      if (onFinish) onFinish()
    }
  }

  return {
    seconds,
    running,
    formatted,
    start,
    stop,
    reset,
    resync,
  }
}