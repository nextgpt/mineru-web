import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

interface WebSocketMessage {
  type: string
  data: any
  project_id?: string
  user_id?: string
}

interface ProjectUpdate {
  project_id: string
  status: string
  progress?: number
  current_step?: string
  message?: string
}

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectTimer: number | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 3000
  private isConnecting = false

  // 响应式状态
  public connected = ref(false)
  public connecting = ref(false)
  public projectUpdates = reactive<Map<string, ProjectUpdate>>(new Map())

  // 事件监听器
  private listeners = new Map<string, Set<Function>>()

  constructor() {
    this.connect()
  }

  private connect() {
    if (this.isConnecting || this.connected.value) {
      return
    }

    this.isConnecting = true
    this.connecting.value = true

    try {
      // 构建WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      const wsUrl = `${protocol}//${host}/ws`

      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket连接已建立')
        this.connected.value = true
        this.connecting.value = false
        this.isConnecting = false
        this.reconnectAttempts = 0
        
        // 发送认证信息
        this.send({
          type: 'auth',
          data: {
            user_id: this.getUserId()
          }
        })
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (e) {
          console.error('解析WebSocket消息失败:', e)
        }
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket连接已关闭:', event.code, event.reason)
        this.connected.value = false
        this.connecting.value = false
        this.isConnecting = false
        this.ws = null

        // 如果不是主动关闭，尝试重连
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect()
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error)
        this.connecting.value = false
        this.isConnecting = false
      }

    } catch (e) {
      console.error('创建WebSocket连接失败:', e)
      this.connecting.value = false
      this.isConnecting = false
      this.scheduleReconnect()
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.reconnectAttempts++
    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1)

    console.log(`${delay}ms后尝试第${this.reconnectAttempts}次重连...`)

    this.reconnectTimer = window.setTimeout(() => {
      this.connect()
    }, delay)
  }

  private handleMessage(message: WebSocketMessage) {
    console.log('收到WebSocket消息:', message)

    switch (message.type) {
      case 'project_update':
        this.handleProjectUpdate(message.data)
        break
      case 'task_progress':
        this.handleTaskProgress(message.data)
        break
      case 'error':
        ElMessage.error(message.data.message || '发生错误')
        break
      case 'notification':
        ElMessage.info(message.data.message)
        break
      default:
        console.log('未知消息类型:', message.type)
    }

    // 触发事件监听器
    this.emit(message.type, message.data)
  }

  private handleProjectUpdate(data: ProjectUpdate) {
    this.projectUpdates.set(data.project_id, data)
    
    // 显示状态更新通知
    if (data.message) {
      ElMessage.success(data.message)
    }
  }

  private handleTaskProgress(data: any) {
    if (data.project_id) {
      const existing = this.projectUpdates.get(data.project_id)
      this.projectUpdates.set(data.project_id, {
        ...existing,
        project_id: data.project_id,
        status: data.status || existing?.status || 'unknown',
        progress: data.progress,
        current_step: data.current_step,
        message: data.message
      })
    }
  }

  private send(message: WebSocketMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket未连接，无法发送消息')
    }
  }

  private getUserId(): string {
    // 从localStorage或其他地方获取用户ID
    return localStorage.getItem('user_id') || 'anonymous'
  }

  // 公共方法
  public subscribe(projectId: string) {
    this.send({
      type: 'subscribe',
      data: {
        project_id: projectId
      }
    })
  }

  public unsubscribe(projectId: string) {
    this.send({
      type: 'unsubscribe',
      data: {
        project_id: projectId
      }
    })
  }

  public getProjectUpdate(projectId: string): ProjectUpdate | undefined {
    return this.projectUpdates.get(projectId)
  }

  public on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(callback)
  }

  public off(event: string, callback: Function) {
    const eventListeners = this.listeners.get(event)
    if (eventListeners) {
      eventListeners.delete(callback)
    }
  }

  private emit(event: string, data: any) {
    const eventListeners = this.listeners.get(event)
    if (eventListeners) {
      eventListeners.forEach(callback => {
        try {
          callback(data)
        } catch (e) {
          console.error('事件监听器执行失败:', e)
        }
      })
    }
  }

  public disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.ws) {
      this.ws.close(1000, '主动断开连接')
      this.ws = null
    }

    this.connected.value = false
    this.connecting.value = false
    this.isConnecting = false
    this.reconnectAttempts = 0
  }

  public reconnect() {
    this.disconnect()
    setTimeout(() => {
      this.connect()
    }, 1000)
  }
}

// 创建全局WebSocket服务实例
export const wsService = new WebSocketService()

// 导出类型
export type { WebSocketMessage, ProjectUpdate }