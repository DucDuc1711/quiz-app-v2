import { useToast } from '@/composables/useToast'

describe('useToast', () => {
  beforeEach(() => {
    // Clear toasts between tests since useToast is a singleton
    const toast = useToast()
    toast.toasts.value.forEach(t => toast.remove(t.id))
    vi.clearAllMocks()
  })

  it('should return correct API with toasts, success, error, remove', () => {
    const toast = useToast()
    expect(toast).toHaveProperty('toasts')
    expect(toast).toHaveProperty('success')
    expect(toast).toHaveProperty('error')
    expect(toast).toHaveProperty('remove')
    expect(typeof toast.success).toBe('function')
    expect(typeof toast.error).toBe('function')
    expect(typeof toast.remove).toBe('function')
    expect(Array.isArray(toast.toasts.value)).toBe(true)
  })

  it('should add success toast', () => {
    const toast = useToast()
    const id = toast.success('Test message', 'Test title')
    expect(id).toBeDefined()
    expect(toast.toasts.value).toHaveLength(1)
    expect(toast.toasts.value[0]).toMatchObject({
      type: 'success',
      message: 'Test message',
      title: 'Test title',
    })
  })

  it('should add error toast', () => {
    const toast = useToast()
    const id = toast.error('Error message', 'Error title')
    expect(id).toBeDefined()
    expect(toast.toasts.value).toHaveLength(1)
    expect(toast.toasts.value[0]).toMatchObject({
      type: 'error',
      message: 'Error message',
      title: 'Error title',
    })
  })

  it('should remove toast by id', () => {
    const toast = useToast()
    const id = toast.success('Test')
    toast.remove(id)
    expect(toast.toasts.value).toHaveLength(0)
  })

  it('should use default titles', () => {
    const toast = useToast()
    toast.success('Success msg')
    toast.error('Error msg')
    expect(toast.toasts.value[0].title).toBe('Thành công')
    expect(toast.toasts.value[1].title).toBe('Có lỗi xảy ra')
  })

  it('should use custom duration', () => {
    const toast = useToast()
    toast.success('Test', 'Title', 1000)
    expect(toast.toasts.value[0].duration).toBe(1000)
  })
})