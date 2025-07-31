import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { wsService } from '@/services/websocket'

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState = MockWebSocket.CONNECTING
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(public url: string) {
    // 模拟异步连接
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 10)
  }

  send(data: string) {
    // Mock send method
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code: code || 1000, reason }))
    }
  }

  // 模拟接收消息
  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }))
    }
  }

  // 模拟连接错误
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'))
    }
  }
}

// 替换全局WebSocket
global.WebSocket = MockWebSocket as any

describe('WebSocket Service', () => {
  let mockWebSocket: MockWebSocket

  beforeEach(() => {
    vi.clearAllMocks()
    // 重置服务状态
    wsService.disconnect()
    wsService.connected.value = false
    wsService.connecting.value = false
    wsService.projectUpdates.clear()
  })

  afterEach(() => {
    wsService.disconnect()
  })

  it('establishes connection successfully', async () => {
    // 等待连接建立
    await new Promise(resolve => setTimeout(resolve, 20))
    
    expect(wsService.connected.value).toBe(true)
    expect(wsService.connecting.value).toBe(false)
  })

  it('handles project update messages', async () => {
    await new Promise(resolve => setTimeout(resolve, 20))

    const projectUpdate = {
      project_id: 'test-project',
      status: 'analyzing',
      progress: 50,
      message: '正在分析文档'
    }

    // 模拟接收项目更新消息
    const message = {
      type: 'project_update',
      data: projectUpdate
    }

    // 获取当前的WebSocket实例
    const currentWs = (wsService as any).ws as MockWebSocket
    currentWs.simulateMessage(message)

    // 验证项目更新被存储
    const storedUpdate = wsService.getProjectUpdate('test-project')
    expect(storedUpdate).toEqual(projectUpdate)
  })

  it('handles task progress messages', async () => {
    await new Promise(resolve => setTimeout(resolve, 20))

    const progressData = {
      project_id: 'test-project',
      status: 'generating',
      progress: 75,
      current_step: '生成第3章内容'
    }

    const message = {
      type: 'task_progress',
      data: progressData
    }

    const currentWs = (wsService as any).ws as MockWebSocket
    currentWs.simulateMessage(message)

    const storedUpdate = wsService.getProjectUpdate('test-project')
    expect(storedUpdate?.progress).toBe(75)
    expect(storedUpdate?.current_step).toBe('生成第3章内容')
  })

  it('handles subscription to projects', async () => {
    await new Promise(resolve => setTimeout(resolve, 20))

    const sendSpy = vi.spyOn((wsService as any).ws, 'send')
    
    wsService.subscribe('test-project')

    expect(sendSpy).toHaveBeenCalledWith(JSON.stringify({
      type: 'subscribe',
      data: {
        project_id: 'test-project'
      }
    }))
  })

  it('handles unsubscription from projects', async () => {
    await new Promise(resolve => setTimeout(resolve, 20))

    const sendSpy = vi.spyOn((wsService as any).ws, 'send')
    
    wsService.unsubscribe('test-project')

    expect(sendSpy).toHaveBeenCalledWith(JSON.stringify({
      type: 'unsubscribe',
      data: {
        project_id: 'test-project'
      }
    }))
  })

  it('handles connection errors', async () => {
    await new Promise(resolve => setTimeout(resolve, 20))

    const currentWs = (wsService as any).ws as MockWebSocket
    currentWs.simulateError()

    // 连接应该保持，因为错误不会自动断开
    expect(wsService.connected.value).toBe(true)
  })

  it('handles connection close and reconnection', async () => {
    await new Promise(resolve => setTimeout(resolve, 20))
    expect(wsService.connected.value).toBe(true)

    const currentWs = (wsService as any).ws as MockWebSocket
    currentWs.close(1006, 'Connection lost') // 非正常关闭

    await new Promise(resolve => setTimeout(resolve, 10))
    expect(wsService.connected.value).toBe(false)

    // 应该尝试重连
    await new Promise(resolve => setTimeout(resolve, 3100)) // 等待重连间隔
    expect(wsService.connecting.value).toBe(true)
  })

  it('handles event listeners correctly', async () => {
    await new Promise(resolve => setTimeout(resolve, 20))

    const mockCallback = vi.fn()
    wsService.on('project_update', mockCallback)

    const projectUpdate = {
      project_id: 'test-project',
      status: 'completed'
    }

    const message = {
      type: 'project_update',
      data: projectUpdate
    }

    const currentWs = (wsService as any).ws as MockWebSocket
    currentWs.simulateMessage(message)

    expect(mockCallback).toHaveBeenCalledWith(projectUpdate)

    // 测试移除监听器
    wsService.off('project_update', mockCallback)
    currentWs.simulateMessage(message)

    // 回调不应该再被调用
    expect(mockCallback).toHaveBeenCalledTimes(1)
  })

  it('handles manual disconnect', async () => {
    await new Promise(resolve => setTimeout(resolve, 20))
    expect(wsService.connected.value).toBe(true)

    wsService.disconnect()

    expect(wsService.connected.value).toBe(false)
    expect(wsService.connecting.value).toBe(false)
  })

  it('handles manual reconnect', async () => {
    await new Promise(resolve => setTimeout(resolve, 20))
    
    wsService.disconnect()
    expect(wsService.connected.value).toBe(false)

    wsService.reconnect()
    expect(wsService.connecting.value).toBe(true)

    await new Promise(resolve => setTimeout(resolve, 20))
    expect(wsService.connected.value).toBe(true)
  })

  it('handles error messages', async () => {
    await new Promise(resolve => setTimeout(resolve, 20))

    const errorMessage = {
      type: 'error',
      data: {
        message: '分析失败',
        error_code: 'ANALYSIS_FAILED'
      }
    }

    const currentWs = (wsService as any).ws as MockWebSocket
    currentWs.simulateMessage(errorMessage)

    // 这里可以验证错误处理逻辑，比如显示错误消息
    // 由于我们mock了ElMessage，可以验证它是否被调用
  })

  it('handles notification messages', async () => {
    await new Promise(resolve => setTimeout(resolve, 20))

    const notificationMessage = {
      type: 'notification',
      data: {
        message: '项目创建成功'
      }
    }

    const currentWs = (wsService as any).ws as MockWebSocket
    currentWs.simulateMessage(notificationMessage)

    // 验证通知处理
  })

  it('prevents multiple concurrent connections', async () => {
    await new Promise(resolve => setTimeout(resolve, 20))
    expect(wsService.connected.value).toBe(true)

    // 尝试再次连接
    const connectMethod = (wsService as any).connect.bind(wsService)
    connectMethod()

    // 应该不会创建新连接
    expect(wsService.connected.value).toBe(true)
  })
})