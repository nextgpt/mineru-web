import { defineStore } from 'pinia'
import { 
  type OutlineGenerationState, 
  type OutlineStage, 
  type TenderProject,
  type GenerationSettings 
} from '@/types/tender'

// 五阶段提示词定义
const OUTLINE_STAGES: Omit<OutlineStage, 'result' | 'status' | 'startTime' | 'endTime' | 'error'>[] = [
  {
    id: 1,
    title: '项目需求概况分析',
    prompt: '请深入理解项目的技术/服务需求并总结成概况概要，不超过300字'
  },
  {
    id: 2,
    title: '需求重要性分析',
    prompt: '请通过行业理解和项目的技术/服务需求分析，根据甲方需求的关注程度将技术/服务需求分为：关键需求、重要需求、一般需求。特别注意请忽略商务需求内容'
  },
  {
    id: 3,
    title: '评分项内容分析',
    prompt: '逐行分析和锁定具体的评分项内容，分点输出得分点、得分分数，内容要求（内容要求必须原文输出，不能伪造数字或要求'
  },
  {
    id: 4,
    title: '评分策略分析',
    prompt: '输出客观评分项、主观评分项、主观评分项整体应答策略逻辑、技术方案重点应答评分项及原因'
  },
  {
    id: 5,
    title: '最终大纲整合',
    prompt: '根据前四个阶段的内容整合输出技术/服务方案大纲'
  }
]

export const useOutlineStore = defineStore('outline', {
  state: (): OutlineGenerationState => ({
    currentStage: 0,
    stages: OUTLINE_STAGES.map(stage => ({
      ...stage,
      result: '',
      status: 'pending'
    })),
    isGenerating: false,
    finalOutline: '',
    error: undefined
  }),

  getters: {
    // 当前阶段信息
    currentStageInfo: (state) => {
      if (state.currentStage === 0) return null
      return state.stages[state.currentStage - 1]
    },

    // 已完成的阶段数量
    completedStagesCount: (state) => {
      return state.stages.filter(stage => stage.status === 'completed').length
    },

    // 生成进度百分比
    progressPercentage(): number {
      return Math.round((this.completedStagesCount / this.stages.length) * 100)
    },

    // 是否所有阶段都已完成
    isAllStagesCompleted: (state) => {
      return state.stages.every(stage => stage.status === 'completed')
    },

    // 是否有错误发生
    hasError: (state) => {
      return state.stages.some(stage => stage.status === 'error') || !!state.error
    },

    // 获取错误信息
    errorMessages: (state) => {
      const stageErrors = state.stages
        .filter(stage => stage.status === 'error' && stage.error)
        .map(stage => `阶段${stage.id}: ${stage.error}`)
      
      if (state.error) {
        stageErrors.push(state.error)
      }
      
      return stageErrors
    }
  },

  actions: {
    // 开始生成大纲
    async startGeneration(project: TenderProject, settings: GenerationSettings) {
      this.resetState()
      this.isGenerating = true
      this.error = undefined

      try {
        // 依次执行五个阶段
        for (let i = 0; i < this.stages.length; i++) {
          await this.executeStage(i + 1, project, settings)
          
          // 如果某个阶段失败，停止后续执行
          if (this.stages[i].status === 'error') {
            break
          }
        }

        // 如果所有阶段都成功完成，设置最终大纲
        if (this.isAllStagesCompleted) {
          this.finalOutline = this.stages[4].result // 第五阶段的结果作为最终大纲
        }
      } catch (error) {
        console.error('Outline generation failed:', error)
        this.error = error instanceof Error ? error.message : '大纲生成失败'
      } finally {
        this.isGenerating = false
        this.currentStage = 0
      }
    },

    // 执行单个阶段
    async executeStage(stageNumber: number, project: TenderProject, settings: GenerationSettings) {
      const stageIndex = stageNumber - 1
      const stage = this.stages[stageIndex]
      
      this.currentStage = stageNumber
      stage.status = 'processing'
      stage.startTime = Date.now()
      stage.error = undefined

      try {
        // 这里应该调用 RAGFLOW API 进行检索
        // 暂时使用模拟数据，实际实现时需要集成 RAGFlowService
        const result = await this.mockStageExecution(stage, project, settings)
        
        stage.result = result
        stage.status = 'completed'
        stage.endTime = Date.now()
      } catch (error) {
        console.error(`Stage ${stageNumber} execution failed:`, error)
        stage.status = 'error'
        stage.error = error instanceof Error ? error.message : `阶段${stageNumber}执行失败`
        stage.endTime = Date.now()
      }
    },

    // 模拟阶段执行（实际实现时替换为真实的API调用）
    async mockStageExecution(stage: OutlineStage, project: TenderProject, settings: GenerationSettings): Promise<string> {
      // 模拟网络延迟
      await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000))
      
      // 模拟可能的错误
      if (Math.random() < 0.1) { // 10% 的概率出错
        throw new Error(`模拟错误：阶段${stage.id}执行失败`)
      }

      // 返回模拟结果
      return `阶段${stage.id}的模拟结果：\n\n${stage.title}\n\n基于项目"${project.name}"和设置（篇幅：${settings.length}，质量：${settings.quality}）生成的内容...\n\n这是一个模拟的结果，实际实现时将调用RAGFLOW API进行内容检索和生成。`
    },

    // 重试失败的阶段
    async retryStage(stageNumber: number, project: TenderProject, settings: GenerationSettings) {
      if (stageNumber < 1 || stageNumber > this.stages.length) {
        throw new Error('无效的阶段编号')
      }

      const stage = this.stages[stageNumber - 1]
      stage.status = 'pending'
      stage.result = ''
      stage.error = undefined

      await this.executeStage(stageNumber, project, settings)
    },

    // 重置状态
    resetState() {
      this.currentStage = 0
      this.isGenerating = false
      this.finalOutline = ''
      this.error = undefined
      
      this.stages.forEach(stage => {
        stage.result = ''
        stage.status = 'pending'
        stage.startTime = undefined
        stage.endTime = undefined
        stage.error = undefined
      })
    },

    // 停止生成
    stopGeneration() {
      this.isGenerating = false
      this.currentStage = 0
      
      // 将正在处理的阶段标记为错误
      const processingStage = this.stages.find(stage => stage.status === 'processing')
      if (processingStage) {
        processingStage.status = 'error'
        processingStage.error = '用户取消操作'
        processingStage.endTime = Date.now()
      }
    },

    // 获取阶段执行时间
    getStageExecutionTime(stageNumber: number): number | null {
      const stage = this.stages[stageNumber - 1]
      if (stage.startTime && stage.endTime) {
        return stage.endTime - stage.startTime
      }
      return null
    },

    // 获取总执行时间
    getTotalExecutionTime(): number | null {
      const completedStages = this.stages.filter(stage => 
        stage.status === 'completed' && stage.startTime && stage.endTime
      )
      
      if (completedStages.length === 0) return null
      
      const startTimes = completedStages.map(stage => stage.startTime!).filter(Boolean)
      const endTimes = completedStages.map(stage => stage.endTime!).filter(Boolean)
      
      if (startTimes.length === 0 || endTimes.length === 0) return null
      
      return Math.max(...endTimes) - Math.min(...startTimes)
    },

    // 导出大纲结果
    exportOutlineResults() {
      return {
        finalOutline: this.finalOutline,
        stages: this.stages.map(stage => ({
          id: stage.id,
          title: stage.title,
          result: stage.result,
          status: stage.status,
          executionTime: this.getStageExecutionTime(stage.id)
        })),
        totalExecutionTime: this.getTotalExecutionTime(),
        completedAt: new Date().toISOString()
      }
    },

    // 从导出数据恢复状态
    restoreFromExport(exportData: any) {
      if (exportData.finalOutline) {
        this.finalOutline = exportData.finalOutline
      }
      
      if (exportData.stages && Array.isArray(exportData.stages)) {
        exportData.stages.forEach((exportedStage: any, index: number) => {
          if (index < this.stages.length) {
            this.stages[index].result = exportedStage.result || ''
            this.stages[index].status = exportedStage.status || 'pending'
          }
        })
      }
    }
  }
})