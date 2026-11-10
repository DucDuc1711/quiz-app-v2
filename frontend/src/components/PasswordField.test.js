import { mount } from '@vue/test-utils'
import PasswordField from '@/components/PasswordField.vue'

describe('PasswordField', () => {
  it('nút Hiện/Ẩn đổi type của ô nhập', async () => {
    const wrapper = mount(PasswordField, {
      props: { modelValue: '', ariaLabel: 'Mật khẩu' },
    })

    const input = wrapper.find('input')
    expect(input.element.type).toBe('password')

    await wrapper.find('button').trigger('click')
    expect(input.element.type).toBe('text')

    await wrapper.find('button').trigger('click')
    expect(input.element.type).toBe('password')

    wrapper.unmount()
  })

  it('có aria-label tiếng Việt', async () => {
    const wrapper = mount(PasswordField, {
      props: { modelValue: '', ariaLabel: 'Mật khẩu' },
    })

    const input = wrapper.find('input')
    expect(input.attributes('aria-label')).toBe('Mật khẩu')

    const toggle = wrapper.find('button')
    expect(toggle.attributes('aria-label')).toBe('Hiện mật khẩu')

    await toggle.trigger('click')
    expect(toggle.attributes('aria-label')).toBe('Ẩn mật khẩu')

    wrapper.unmount()
  })
})