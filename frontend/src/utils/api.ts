import { ElMessage } from 'element-plus'
import { AxiosError } from 'axios'
import { config } from '@/config'

/**
 * API错误处理器
 */
export class APIErrorHandler {
  static handle(error: any): void {
    console.error('API Error:', error)

    if (error instanceof AxiosError) {
      switch (error.response?.status) {
        case 401:
          ElMessage.error('API认证失败，请检查密钥配置')
          break
        case 403:
          ElMessage.error('访问被拒绝，请检查权限')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 429:
          ElMessage.error('请求过于频繁，请稍后重试')
          break
        case 500:
          ElMessage.error('服务器内部错误，请稍后重试')
          break
        default:
          ElMessage.error(error.message || '网络请求失败，请检查网络连接')
      }
    } else if (error instanceof Error) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error('未知错误，请稍后重试')
    }
  }
}

/**
 * 文件上传错误处理器
 */
export class UploadErrorHandler {
  static validateFile(file: File): boolean {
    const maxSize = config.app.maxFileSize
    const allowedTypes = config.app.supportedFileTypes

    if (file.size > maxSize) {
      ElMessage.error(`文件大小不能超过${Math.round(maxSize / 1024 / 1024)}MB`)
      return false
    }

    const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    if (!allowedTypes.includes(fileExt)) {
      ElMessage.error(`不支持的文件类型，支持的格式：${allowedTypes.join(', ')}`)
      return false
    }

    return true
  }

  static getFileIcon(fileName: string): string {
    const ext = fileName.toLowerCase().substring(fileName.lastIndexOf('.'))
    switch (ext) {
      case '.pdf':
        return 'document'
      case '.doc':
      case '.docx':
        return 'document'
      default:
        return 'document'
    }
  }
}

/**
 * 重试机制
 */
export class RetryHandler {
  static async withRetry<T>(
    fn: () => Promise<T>,
    maxAttempts: number = config.app.retryAttempts,
    delay: number = config.app.retryDelay
  ): Promise<T> {
    let lastError: Error

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await fn()
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error))
        
        if (attempt === maxAttempts) {
          throw lastError
        }

        console.warn(`Attempt ${attempt} failed, retrying in ${delay}ms...`, lastError.message)
        await this.sleep(delay)
        delay *= 2 // 指数退避
      }
    }

    throw lastError!
  }

  private static sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}

/**
 * 防抖函数
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null

  return (...args: Parameters<T>) => {
    if (timeout) {
      clearTimeout(timeout)
    }
    
    timeout = setTimeout(() => {
      func.apply(null, args)
    }, wait)
  }
}

/**
 * 节流函数
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let inThrottle = false

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func.apply(null, args)
      inThrottle = true
      setTimeout(() => inThrottle = false, wait)
    }
  }
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化时间
 */
export function formatTime(timestamp: string | number): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  
  if (diff < minute) {
    return '刚刚'
  } else if (diff < hour) {
    return `${Math.floor(diff / minute)}分钟前`
  } else if (diff < day) {
    return `${Math.floor(diff / hour)}小时前`
  } else if (diff < 7 * day) {
    return `${Math.floor(diff / day)}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

/**
 * 生成唯一ID
 */
export function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

/**
 * 深拷贝对象
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }
  
  if (obj instanceof Date) {
    return new Date(obj.getTime()) as unknown as T
  }
  
  if (obj instanceof Array) {
    return obj.map(item => deepClone(item)) as unknown as T
  }
  
  if (typeof obj === 'object') {
    const cloned = {} as T
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        cloned[key] = deepClone(obj[key])
      }
    }
    return cloned
  }
  
  return obj
}