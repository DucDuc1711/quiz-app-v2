const KEY = 'quiz_device_id'

export function useDeviceId() {
  let deviceId = localStorage.getItem(KEY)
  if (!deviceId) {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      deviceId = crypto.randomUUID()
    } else {
      deviceId = 'dev_' + Math.random().toString(36).slice(2) + Date.now().toString(36)
    }
    localStorage.setItem(KEY, deviceId)
  }
  return { deviceId }
}