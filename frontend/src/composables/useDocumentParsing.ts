import { ref, onUnmounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { ragflowService } from '@/api/ragflow'
import { useProjectStore } from '@/store/project'
import type { TenderProject } from '@/types/tender'

export interface ParsingProgress {
  stage: number
  stageName: string
  progress: number
  details: string
  status: 'pending' | 'processing' | 'completed' | 'error'
}

export function useDocumentParsing() {
  const projectStore = useProjectStore()
  
  const isMonitoring = ref(false)
  const parsingProgress = ref<ParsingProgress>({
    stage: 1,
    stageName: '准备中',
    progress: 0,
    details: '',
    status: 'pending'
  })
  
  let monitoringTimer: number | null = null
  let currentProjectId: string | null = null

  /**
   * 开始监控文档解析进度
   */
  const startMonitoring = async (
    projectId: string,
    datasetId: string,
    documentId: string,
    onCompleted?: (project: TenderProject) => void,
    onError?: (error: string) => void
  ) => {
    if (isMonitoring.value) {
      console.warn('[DocumentParsing] Already monitoring, stopping previous monitoring')
      stopMonitoring()
    }

    currentProjectId = projectId
    isMonitoring.value = true
    parsingProgress.value = {
      stage: 3,
      stageName: '解析文档',
      progress: 0,
      details: '开始解析文档内容...',
      status: 'processing'
    }

    // 更新项目状态
    projectStore.updateProject(projectId, { status: 'parsing' })

    const checkProgress = async () => {
      if (!isMonitoring.value || !currentProjectId) {
        return
      }

      try {
        const notification = await ragflowService.getParsingNotification(datasetId, documentId)
        
        parsingProgress.value.progress = notification.progress
        parsingProgress.value.details = notification.message

        // 根据进度更新阶段
        if (notification.progress >= 50 && parsingProgress.value.stage === 3) {
          parsingProgress.value.stage = 4
          parsingProgress.value.stageName = '内容分析'
        } else if (notification.progress >= 90 && parsingProgress.value.stage === 4) {
          parsingProgress.value.stage = 5
          parsingProgress.value.stageName = '完成处理'
        }

        if (notification.isCompleted) {
          // 解析完成
          parsingProgress.value.status = 'completed'
          parsingProgress.value.progress = 100
          parsingProgress.value.details = notification.message

          // 更新项目状态
          projectStore.updateProject(projectId, { 
            status: 'ready',
            lastModified: new Date().toISOString()
          })

          // 显示成功通知
          ElNotification({
            title: '解析完成',
            message: notification.message,
            type: 'success',
            duration: 5000
          })

          // 停止监控
          stopMonitoring()

          // 调用完成回调
          const project = projectStore.projects.find(p => p.id === projectId)
          if (project && onCompleted) {
            onCompleted(project)
          }

          return
        }

        // 继续监控
        monitoringTimer = window.setTimeout(checkProgress, 2000)

      } catch (error) {
        console.error('[DocumentParsing] Monitoring error:', error)
        
        parsingProgress.value.status = 'error'
        parsingProgress.value.details = (error as Error).message || '解析过程中发生错误'

        // 更新项目状态
        projectStore.updateProject(projectId, { 
          status: 'error',
          lastModified: new Date().toISOString()
        })

        // 检查是否是RAGFLOW特定错误并显示相应通知
        const errorMessage = (error as Error).message || ''
        if (errorMessage.includes('float()') || errorMessage.includes('NoneType') || errorMessage.includes('embedding')) {
          ElNotification({
            title: 'RAGFLOW解析错误',
            message: '解析配置错误，系统已自动修复，建议重试解析',
            type: 'error',
            duration: 0
          })
        } else {
          ElNotification({
            title: '解析失败',
            message: errorMessage || '文档解析过程中发生错误',
            type: 'error',
            duration: 0
          })
        }

        // 停止监控
        stopMonitoring()

        // 调用错误回调
        if (onError) {
          onError((error as Error).message || '解析失败')
        }
      }
    }

    // 开始检查
    checkProgress()
  }

  /**
   * 停止监控
   */
  const stopMonitoring = () => {
    isMonitoring.value = false
    currentProjectId = null
    
    if (monitoringTimer) {
      clearTimeout(monitoringTimer)
      monitoringTimer = null
    }
  }

  /**
   * 重试解析
   */
  const retryParsing = async (
    projectId: string,
    datasetId: string,
    documentId: string
  ): Promise<boolean> => {
    try {
      parsingProgress.value = {
        stage: 3,
        stageName: '重试解析',
        progress: 0,
        details: '正在重新解析文档...',
        status: 'processing'
      }

      // 更新项目状态
      projectStore.updateProject(projectId, { status: 'parsing' })

      // 重试解析
      await ragflowService.retryDocumentParsing(datasetId, documentId)

      // 更新项目状态为就绪
      projectStore.updateProject(projectId, { 
        status: 'ready',
        lastModified: new Date().toISOString()
      })

      parsingProgress.value.status = 'completed'
      parsingProgress.value.progress = 100
      parsingProgress.value.details = '重试解析成功！'

      ElMessage.success('文档重新解析成功！')
      return true

    } catch (error) {
      console.error('[DocumentParsing] Retry failed:', error)
      
      parsingProgress.value.status = 'error'
      parsingProgress.value.details = (error as Error).message || '重试解析失败'

      // 更新项目状态
      projectStore.updateProject(projectId, { 
        status: 'error',
        lastModified: new Date().toISOString()
      })

      ElMessage.error('重试解析失败：' + ((error as Error).message || '未知错误'))
      return false
    }
  }

  /**
   * 检查项目解析状态
   */
  const checkProjectParsingStatus = async (project: TenderProject): Promise<{
    needsParsing: boolean
    canStartOutline: boolean
    statusMessage: string
  }> => {
    if (!project.datasetId || !project.documentId) {
      return {
        needsParsing: true,
        canStartOutline: false,
        statusMessage: '项目信息不完整，需要重新上传'
      }
    }

    if (project.status === 'ready') {
      return {
        needsParsing: false,
        canStartOutline: true,
        statusMessage: '文档已解析完成，可以开始生成大纲'
      }
    }

    if (project.status === 'parsing') {
      return {
        needsParsing: false,
        canStartOutline: false,
        statusMessage: '文档正在解析中，请稍候...'
      }
    }

    if (project.status === 'error') {
      return {
        needsParsing: true,
        canStartOutline: false,
        statusMessage: '文档解析失败，需要重试'
      }
    }

    // 对于其他状态，检查实际解析状态
    try {
      const notification = await ragflowService.getParsingNotification(
        project.datasetId,
        project.documentId
      )

      if (notification.isCompleted) {
        // 更新项目状态
        projectStore.updateProject(project.id, { status: 'ready' })
        return {
          needsParsing: false,
          canStartOutline: true,
          statusMessage: '文档已解析完成，可以开始生成大纲'
        }
      }

      return {
        needsParsing: false,
        canStartOutline: false,
        statusMessage: notification.message
      }

    } catch (error) {
      return {
        needsParsing: true,
        canStartOutline: false,
        statusMessage: '检查解析状态失败，建议重新解析'
      }
    }
  }

  // 组件卸载时清理
  onUnmounted(() => {
    stopMonitoring()
  })

  return {
    isMonitoring,
    parsingProgress,
    startMonitoring,
    stopMonitoring,
    retryParsing,
    checkProjectParsingStatus
  }
}