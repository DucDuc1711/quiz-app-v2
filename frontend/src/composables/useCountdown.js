import { ref, computed } from 'vue'

// Dong ho thoi gian thuc theo chuan gio (deadline), khong dem so tick.
// Tinh toan tu moc deadline nhan duoc tu server, hoat dong khi tab an
// va dong bo lai khi quay lai tab qua resync().
export function useCountdown({ onFinish } = {}) {
  const seconds = ref(0)
  const running = ref(false)
  const deadline = ref(null) // moc thoi gian (ms), null khi khong chay
  let raf = null

  const formatted = computed(() => {
    const total = Math.max(0, Math.ceil(seconds.value || 0))
    const m = Math.floor(total / 60)
    const s = total % 60
    return m + ':' + String(s).padStart(2, '0')
  })

  function tick() {
    if (!running.value || !deadline.value) return
    const remain = deadline.value - Date.now()
    if (remain <= 0) {
      seconds.value = 0
      stop()
      if (onFinish) onFinish()
      return
    }
    seconds.value = Math.ceil(remain / 1000)
    raf = requestAnimationFrame(tick)
  }

  function start(secondsLeft) {
    stop()
    const left = Math.max(0, Math.ceil(secondsLeft || 0))
    seconds.value = left
    deadline.value = Date.now() + left * 1000
    running.value = true
    tick()
  }

  function stop() {
    running.value = false
    deadline.value = null
    if (raf) {
      cancelAnimationFrame(raf)
      raf = null
    }
  }

  // Dong bo lai voi server khi quay lai tab (seconds_left tu server).
  function resync(secondsLeft) {
    if (!running.value) return
    const left = Math.max(0, Math.ceil(secondsLeft || 0))
    seconds.value = left
    deadline.value = Date.now() + left * 1000
  }

  return {
    seconds,
    running,
    deadline,
    formatted,
    start,
    stop,
    resync,
  }
}