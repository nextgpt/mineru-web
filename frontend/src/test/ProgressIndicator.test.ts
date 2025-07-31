import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ProgressIndicator from '@/components/ProgressIndicator.vue'
import { wsService } from '@/services/websocket'

// Mock WebSocket service
vi.mock('@/services/websocket', () => ({
  wsService: {
    connected: { value: true },
    connecting: { value: false },
    getProjectUpdate: vi.fn(),
    subscribe: vi.fn(),
    unsubscribe: vi.fn(),
    reconnect: vi.fn()
  }
}))

describe('ProgressIndicator.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders connection status correctly', async () => {
    const wrapper = mount(ProgressIndicator, {
      props: {
        projectId: 'test-project',
        showConnectionStatus: true
      },
      global: {
        stubs: {
          'el-icon': true,
          'el-button': true,
          'el-progress': true
        }
      }
    })

    await nextTick()

    expect(wrapper.find('.connection-status').exists()).toBe(true)
    expect(wrapper.find('.status-text').text()).toBe('已连接')
  })

  it('shows project progress when available', async () => {
    const mockProjectUpdate = {
      project_id: 'test-project',
      status: 'generating',
      progress: 75,
      current_step: '生成第3章内容',
      message: '正在生成内容'
    }

    vi.mocked(wsService.getProjectUpdate).mockReturnValue(mockProjectUpdate)

    const wrapper = mount(ProgressIndicator, {
      props: {
        projectId: 'test-project'
      },
      global: {
        stubs: {
          'el-icon': true,
          'el-button': true,
          'el-progress': true
        }
      }
    })

    await nextTick()

    expect(wrapper.find('.project-progress').exists()).toBe(true)
    expect(wrapper.find('.progress-title').text()).toBe('内容生成中')
    expect(wrapper.find('.current-step').text()).toContain('生成第3章内容')
    expect(wrapper.find('.progress-message').text()).toBe('正在生成内容')
  })

  it('shows cancel button for cancellable tasks', async () => {
    const mockProjectUpdate = {
      project_id: 'test-project',
      status: 'analyzing',
      progress: 50
    }

    vi.mocked(wsService.getProjectUpdate).mockReturnValue(mockProjectUpdate)

    const wrapper = mount(ProgressIndicator, {
      props: {
        projectId: 'test-project',
        showCancelButton: true
      },
      global: {
        stubs: {
          'el-icon': true,
          'el-button': { template: '<button @click="$emit(\'click\')"><slot /></button>' },
          'el-progress': true
        }
      }
    })

    await nextTick()

    const cancelButton = wrapper.find('.progress-header el-button')
    expect(cancelButton.exists()).toBe(true)
  })

  it('hides cancel button for non-cancellable tasks', async () => {
    const mockProjectUpdate = {
      project_id: 'test-project',
      status: 'completed',
      progress: 100
    }

    vi.mocked(wsService.getProjectUpdate).mockReturnValue(mockProjectUpdate)

    const wrapper = mount(ProgressIndicator, {
      props: {
        projectId: 'test-project',
        showCancelButton: true
      },
      global: {
        stubs: {
          'el-icon': true,
          'el-button': true,
          'el-progress': true
        }
      }
    })

    await nextTick()

    expect(wrapper.vm.canCancel).toBe(false)
  })

  it('emits cancel event when cancel button is clicked', async () => {
    const mockProjectUpdate = {
      project_id: 'test-project',
      status: 'generating',
      progress: 50
    }

    vi.mocked(wsService.getProjectUpdate).mockReturnValue(mockProjectUpdate)

    const wrapper = mount(ProgressIndicator, {
      props: {
        projectId: 'test-project',
        showCancelButton: true
      },
      global: {
        stubs: {
          'el-icon': true,
          'el-button': { template: '<button @click="$emit(\'click\')"><slot /></button>' },
          'el-progress': true
        }
      }
    })

    await nextTick()

    // 触发取消按钮点击
    wrapper.vm.cancelTask()

    expect(wrapper.emitted('cancel')).toBeTruthy()
  })

  it('emits hide event when hide button is clicked', async () => {
    const wrapper = mount(ProgressIndicator, {
      props: {
        projectId: 'test-project',
        showActions: true
      },
      global: {
        stubs: {
          'el-icon': true,
          'el-button': { template: '<button @click="$emit(\'click\')"><slot /></button>' },
          'el-progress': true
        }
      }
    })

    await nextTick()

    wrapper.vm.hide()

    expect(wrapper.emitted('hide')).toBeTruthy()
    expect(wrapper.vm.visible).toBe(false)
  })

  it('shows reconnect button when disconnected', async () => {
    // 模拟断开连接状态
    wsService.connected.value = false
    wsService.connecting.value = false

    const wrapper = mount(ProgressIndicator, {
      props: {
        projectId: 'test-project',
        showActions: true
      },
      global: {
        stubs: {
          'el-icon': true,
          'el-button': { template: '<button @click="$emit(\'click\')"><slot /></button>' },
          'el-progress': true
        }
      }
    })

    await nextTick()

    expect(wrapper.find('.progress-actions').exists()).toBe(true)
  })

  it('calls reconnect when reconnect button is clicked', async () => {
    wsService.connected.value = false
    wsService.connecting.value = false

    const wrapper = mount(ProgressIndicator, {
      props: {
        projectId: 'test-project',
        showActions: true
      },
      global: {
        stubs: {
          'el-icon': true,
          'el-button': { template: '<button @click="$emit(\'click\')"><slot /></button>' },
          'el-progress': true
        }
      }
    })

    await nextTick()

    wrapper.vm.reconnect()

    expect(wsService.reconnect).toHaveBeenCalled()
  })

  it('subscribes to project updates on mount', async () => {
    mount(ProgressIndicator, {
      props: {
        projectId: 'test-project'
      },
      global: {
        stubs: {
          'el-icon': true,
          'el-button': true,
          'el-progress': true
        }
      }
    })

    expect(wsService.subscribe).toHaveBeenCalledWith('test-project')
  })

  it('unsubscribes from project updates on unmount', async () => {
    const wrapper = mount(ProgressIndicator, {
      props: {
        projectId: 'test-project'
      },
      global: {
        stubs: {
          'el-icon': true,
          'el-button': true,
          'el-progress': true
        }
      }
    })

    wrapper.unmount()

    expect(wsService.unsubscribe).toHaveBeenCalledWith('test-project')
  })

  it('formats connection status text correctly', async () => {
    const wrapper = mount(ProgressIndicator, {
      props: {
        showConnectionStatus: true
      },
      global: {
        stubs: {
          'el-icon': true,
          'el-button': true,
          'el-progress': true
        }
      }
    })

    await nextTick()

    // 测试已连接状态
    wsService.connected.value = true
    wsService.connecting.value = false
    expect(wrapper.vm.getConnectionStatusText()).toBe('已连接')

    // 测试连接中状态
    wsService.connected.value = false
    wsService.connecting.value = true
    expect(wrapper.vm.getConnectionStatusText()).toBe('连接中...')

    // 测试断开连接状态
    wsService.connected.value = false
    wsService.connecting.value = false
    expect(wrapper.vm.getConnectionStatusText()).toBe('连接断开')
  })

  it('formats status text correctly', async () => {
    const wrapper = mount(ProgressIndicator, {
      props: {
        projectId: 'test-project'
      },
      global: {
        stubs: {
          'el-icon': true,
          'el-button': true,
          'el-progress': true
        }
      }
    })

    await nextTick()

    expect(wrapper.vm.getStatusText('analyzing')).toBe('分析中')
    expect(wrapper.vm.getStatusText('outlining')).toBe('生成大纲中')
    expect(wrapper.vm.getStatusText('generating')).toBe('生成内容中')
    expect(wrapper.vm.getStatusText('exporting')).toBe('导出中')
    expect(wrapper.vm.getStatusText('completed')).toBe('已完成')
    expect(wrapper.vm.getStatusText('failed')).toBe('失败')
  })

  it('determines progress status correctly', async () => {
    const wrapper = mount(ProgressIndicator, {
      props: {
        projectId: 'test-project'
      },
      global: {
        stubs: {
          'el-icon': true,
          'el-button': true,
          'el-progress': true
        }
      }
    })

    await nextTick()

    expect(wrapper.vm.getProgressStatus('failed')).toBe('exception')
    expect(wrapper.vm.getProgressStatus('completed')).toBe('success')
    expect(wrapper.vm.getProgressStatus('analyzing')).toBeUndefined()
  })
})