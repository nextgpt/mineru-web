import { ElNotification, ElMessage } from 'element-plus'

export interface NotificationOptions {
  title: string
  message: string
  type?: 'success' | 'warning' | 'info' | 'error'
  duration?: number
  showClose?: boolean
  onClick?: () => void
}

export class NotificationService {
  /**
   * 显示解析完成通知
   */
  static showParsingCompleted(projectName: string, chunkCount: number, onClick?: () => void) {
    ElNotification({
      title: '文档解析完成',
      message: `"${projectName}" 已成功解析完成，共生成 ${chunkCount} 个文档片段。点击查看详情。`,
      type: 'success',
      duration: 8000,
      showClose: true,
      onClick: onClick || (() => {})
    })
  }

  /**
   * 显示解析失败通知
   */
  static showParsingFailed(projectName: string, error: string, onRetry?: () => void) {
    ElNotification({
      title: '文档解析失败',
      message: `"${projectName}" 解析失败：${error}。${onRetry ? '点击重试。' : ''}`,
      type: 'error',
      duration: 0, // 不自动关闭
      showClose: true,
      onClick: onRetry || (() => {})
    })
  }

  /**
   * 显示解析进度通知
   */
  static showParsingProgress(projectName: string, progress: number) {
    if (progress % 25 === 0 && progress > 0 && progress < 100) {
      ElMessage({
        message: `"${projectName}" 解析进度：${progress}%`,
        type: 'info',
        duration: 2000
      })
    }
  }

  /**
   * 显示上传成功通知
   */
  static showUploadSuccess(projectName: string, onViewProject?: () => void) {
    ElNotification({
      title: '上传成功',
      message: `"${projectName}" 已成功上传并开始解析。点击查看项目详情。`,
      type: 'success',
      duration: 5000,
      showClose: true,
      onClick: onViewProject || (() => {})
    })
  }

  /**
   * 显示上传失败通知
   */
  static showUploadFailed(fileName: string, error: string, onRetry?: () => void) {
    ElNotification({
      title: '上传失败',
      message: `"${fileName}" 上传失败：${error}。${onRetry ? '点击重试。' : ''}`,
      type: 'error',
      duration: 0,
      showClose: true,
      onClick: onRetry || (() => {})
    })
  }

  /**
   * 显示大纲生成完成通知
   */
  static showOutlineCompleted(projectName: string, onView?: () => void) {
    ElNotification({
      title: '大纲生成完成',
      message: `"${projectName}" 的技术方案大纲已生成完成。点击查看详情。`,
      type: 'success',
      duration: 6000,
      showClose: true,
      onClick: onView || (() => {})
    })
  }

  /**
   * 显示内容生成完成通知
   */
  static showContentCompleted(projectName: string, onView?: () => void) {
    ElNotification({
      title: '标书生成完成',
      message: `"${projectName}" 的标书内容已生成完成。点击查看和编辑。`,
      type: 'success',
      duration: 6000,
      showClose: true,
      onClick: onView || (() => {})
    })
  }

  /**
   * 显示RAGFLOW解析错误通知
   */
  static showRagflowParsingError(projectName: string, error: string, onRetry?: () => void) {
    let message = `"${projectName}" 解析失败：${error}`
    
    // 针对特定错误提供更友好的提示
    if (error.includes('float()') || error.includes('NoneType')) {
      message = `"${projectName}" 解析配置错误，系统已自动修复配置，请重试。`
    } else if (error.includes('embedding')) {
      message = `"${projectName}" 向量化处理失败，可能是文档内容过于复杂，请重试。`
    }
    
    if (onRetry) {
      message += ' 点击此通知重试。'
    }

    ElNotification({
      title: 'RAGFLOW解析错误',
      message,
      type: 'error',
      duration: 0,
      showClose: true,
      onClick: onRetry || (() => {})
    })
  }

  /**
   * 显示自定义通知
   */
  static show(options: NotificationOptions) {
    ElNotification({
      title: options.title,
      message: options.message,
      type: options.type || 'info',
      duration: options.duration ?? 4500,
      showClose: options.showClose ?? true,
      onClick: options.onClick || (() => {})
    })
  }

  /**
   * 显示简单消息
   */
  static showMessage(message: string, type: 'success' | 'warning' | 'info' | 'error' = 'info') {
    ElMessage({
      message,
      type,
      duration: 3000
    })
  }

  /**
   * 显示错误消息
   */
  static showError(message: string) {
    ElMessage.error(message)
  }

  /**
   * 显示成功消息
   */
  static showSuccess(message: string) {
    ElMessage.success(message)
  }

  /**
   * 显示警告消息
   */
  static showWarning(message: string) {
    ElMessage.warning(message)
  }
}

export default NotificationService