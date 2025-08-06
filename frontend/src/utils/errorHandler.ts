import { ElMessage, ElNotification } from 'element-plus'
import { AxiosError } from 'axios'

export interface ErrorInfo {
  code: string
  message: string
  details?: any
  userMessage: string
  canRetry: boolean
}

export class ErrorHandler {
  /**
   * 处理API错误
   */
  static handleApiError(error: unknown, context: string = ''): ErrorInfo {
    console.error(`[ErrorHandler] ${context}:`, error)

    if (error instanceof AxiosError) {
      return this.handleAxiosError(error, context)
    }

    if (error instanceof Error) {
      return this.handleGenericError(error, context)
    }

    return {
      code: 'UNKNOWN_ERROR',
      message: 'Unknown error occurred',
      userMessage: '发生未知错误，请重试',
      canRetry: true
    }
  }

  /**
   * 处理Axios错误
   */
  private static handleAxiosError(error: AxiosError, _context: string): ErrorInfo {
    const response = error.response

    if (!response) {
      // 网络错误
      return {
        code: 'NETWORK_ERROR',
        message: error.message,
        userMessage: '网络连接失败，请检查网络设置后重试',
        canRetry: true
      }
    }

    const status = response.status
    const data = response.data as any

    switch (status) {
      case 400:
        return {
          code: 'BAD_REQUEST',
          message: data?.message || 'Bad request',
          details: data,
          userMessage: data?.message || '请求参数错误，请检查输入内容',
          canRetry: false
        }

      case 401:
        return {
          code: 'UNAUTHORIZED',
          message: 'Unauthorized',
          userMessage: 'API认证失败，请检查配置',
          canRetry: false
        }

      case 403:
        return {
          code: 'FORBIDDEN',
          message: 'Forbidden',
          userMessage: '没有权限执行此操作',
          canRetry: false
        }

      case 404:
        return {
          code: 'NOT_FOUND',
          message: 'Resource not found',
          userMessage: '请求的资源不存在',
          canRetry: false
        }

      case 413:
        return {
          code: 'FILE_TOO_LARGE',
          message: 'File too large',
          userMessage: '文件过大，请选择较小的文件',
          canRetry: false
        }

      case 429:
        return {
          code: 'RATE_LIMIT',
          message: 'Too many requests',
          userMessage: '请求过于频繁，请稍后重试',
          canRetry: true
        }

      case 500:
        return {
          code: 'SERVER_ERROR',
          message: 'Internal server error',
          userMessage: '服务器内部错误，请稍后重试',
          canRetry: true
        }

      case 502:
      case 503:
      case 504:
        return {
          code: 'SERVICE_UNAVAILABLE',
          message: 'Service unavailable',
          userMessage: '服务暂时不可用，请稍后重试',
          canRetry: true
        }

      default:
        return {
          code: 'HTTP_ERROR',
          message: `HTTP ${status}: ${data?.message || error.message}`,
          details: data,
          userMessage: data?.message || `服务器返回错误 (${status})`,
          canRetry: status >= 500
        }
    }
  }

  /**
   * 处理通用错误
   */
  private static handleGenericError(error: Error, _context: string): ErrorInfo {
    // 检查是否是超时错误
    if (error.message.includes('timeout')) {
      return {
        code: 'TIMEOUT_ERROR',
        message: error.message,
        userMessage: '操作超时，请重试',
        canRetry: true
      }
    }

    // 检查是否是文件相关错误
    if (error.message.includes('file') || error.message.includes('upload')) {
      return {
        code: 'FILE_ERROR',
        message: error.message,
        userMessage: '文件处理失败：' + error.message,
        canRetry: true
      }
    }

    // 检查是否是解析相关错误
    if (error.message.includes('parsing') || error.message.includes('parse')) {
      return {
        code: 'PARSING_ERROR',
        message: error.message,
        userMessage: '文档解析失败：' + error.message,
        canRetry: true
      }
    }

    return {
      code: 'GENERIC_ERROR',
      message: error.message,
      userMessage: error.message || '操作失败，请重试',
      canRetry: true
    }
  }

  /**
   * 显示错误消息
   */
  static showError(error: unknown, context: string = '', showNotification: boolean = false) {
    const errorInfo = this.handleApiError(error, context)

    if (showNotification) {
      ElNotification({
        title: '操作失败',
        message: errorInfo.userMessage,
        type: 'error',
        duration: 0,
        showClose: true
      })
    } else {
      ElMessage.error(errorInfo.userMessage)
    }

    return errorInfo
  }

  /**
   * 显示错误消息并提供重试选项
   */
  static showErrorWithRetry(
    error: unknown,
    context: string = '',
    onRetry?: () => void
  ): ErrorInfo {
    const errorInfo = this.handleApiError(error, context)

    if (errorInfo.canRetry && onRetry) {
      ElNotification({
        title: '操作失败',
        message: `${errorInfo.userMessage}\n点击此通知重试`,
        type: 'error',
        duration: 0,
        showClose: true,
        onClick: onRetry
      })
    } else {
      ElNotification({
        title: '操作失败',
        message: errorInfo.userMessage,
        type: 'error',
        duration: 0,
        showClose: true
      })
    }

    return errorInfo
  }

  /**
   * 处理文件上传错误
   */
  static handleUploadError(error: unknown, fileName: string, onRetry?: () => void): ErrorInfo {
    const errorInfo = this.handleApiError(error, 'File Upload')

    // 特殊处理文件上传错误
    if (errorInfo.code === 'FILE_TOO_LARGE') {
      errorInfo.userMessage = `文件 "${fileName}" 过大，请选择小于200MB的文件`
    } else if (errorInfo.code === 'BAD_REQUEST' && errorInfo.message.includes('format')) {
      errorInfo.userMessage = `文件 "${fileName}" 格式不支持，请选择PDF或Word文档`
    }

    this.showErrorWithRetry(errorInfo, 'File Upload', onRetry)
    return errorInfo
  }

  /**
   * 处理文档解析错误
   */
  static handleParsingError(error: unknown, projectName: string, onRetry?: () => void): ErrorInfo {
    const errorInfo = this.handleApiError(error, 'Document Parsing')

    // 特殊处理解析错误
    if (errorInfo.message.includes('timeout')) {
      errorInfo.userMessage = `文档 "${projectName}" 解析超时，可能文档过大或内容复杂，请重试`
    } else if (errorInfo.message.includes('format')) {
      errorInfo.userMessage = `文档 "${projectName}" 格式不支持或已损坏，请检查文档`
      errorInfo.canRetry = false
    } else if (errorInfo.message.includes('float()') || errorInfo.message.includes('NoneType')) {
      errorInfo.userMessage = `文档 "${projectName}" 解析配置错误，系统正在重试`
      errorInfo.canRetry = true
    } else if (errorInfo.message.includes('embedding')) {
      errorInfo.userMessage = `文档 "${projectName}" 向量化处理失败，请重试`
      errorInfo.canRetry = true
    }

    this.showErrorWithRetry(errorInfo, 'Document Parsing', onRetry)
    return errorInfo
  }

  /**
   * 处理大纲生成错误
   */
  static handleOutlineError(error: unknown, projectName: string, onRetry?: () => void): ErrorInfo {
    const errorInfo = this.handleApiError(error, 'Outline Generation')

    errorInfo.userMessage = `项目 "${projectName}" 大纲生成失败：${errorInfo.userMessage}`

    this.showErrorWithRetry(errorInfo, 'Outline Generation', onRetry)
    return errorInfo
  }

  /**
   * 处理内容生成错误
   */
  static handleContentError(error: unknown, projectName: string, onRetry?: () => void): ErrorInfo {
    const errorInfo = this.handleApiError(error, 'Content Generation')

    errorInfo.userMessage = `项目 "${projectName}" 内容生成失败：${errorInfo.userMessage}`

    this.showErrorWithRetry(errorInfo, 'Content Generation', onRetry)
    return errorInfo
  }

  /**
   * 验证文件
   */
  static validateFile(file: File): { valid: boolean; error?: string } {
    // 检查文件大小 (200MB)
    const maxSize = 200 * 1024 * 1024
    if (file.size > maxSize) {
      return {
        valid: false,
        error: '文件大小不能超过200MB'
      }
    }

    // 检查文件类型
    const allowedTypes = ['.pdf', '.doc', '.docx']
    const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))

    if (!allowedTypes.includes(fileExt)) {
      return {
        valid: false,
        error: `不支持的文件类型，仅支持：${allowedTypes.join('、')}`
      }
    }

    // 检查文件名
    if (file.name.length > 100) {
      return {
        valid: false,
        error: '文件名过长，请使用较短的文件名'
      }
    }

    return { valid: true }
  }
}

export default ErrorHandler