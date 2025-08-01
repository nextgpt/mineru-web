<template>
  <div class="requirement-analysis-component">
    <div class="analysis-header">
      <h3 class="section-title">需求分析</h3>
      <el-button 
        v-if="!analysis && !analyzing" 
        type="primary" 
        @click="startAnalysis"
      >
        开始分析
      </el-button>
    </div>

    <!-- 分析进行中 -->
    <div v-if="analyzing" class="analyzing-state">
      <div class="analyzing-content">
        <el-icon class="analyzing-icon" size="48"><Loading /></el-icon>
        <h4 class="analyzing-title">正在分析招标文件...</h4>
        <p class="analyzing-text">AI正在深度分析招标文件内容，提取关键需求信息，请稍候。</p>
        
        <!-- 进度条 -->
        <div class="progress-container">
          <el-progress 
            :percentage="analysisProgress" 
            :stroke-width="8"
            :show-text="true"
            :format="(percentage) => `${percentage}%`"
            color="#3b82f6"
          />
          
          <!-- 详细步骤 -->
          <div class="progress-steps">
            <div 
              v-for="(step, index) in progressSteps" 
              :key="step.key"
              class="progress-step"
              :class="{
                'step-completed': step.completed,
                'step-active': index === currentStep && !step.completed,
                'step-pending': index > currentStep
              }"
            >
              <div class="step-icon">
                <el-icon v-if="step.completed" size="16" color="#10b981">
                  <Check />
                </el-icon>
                <el-icon v-else-if="index === currentStep" size="16" color="#3b82f6">
                  <Loading />
                </el-icon>
                <span v-else class="step-number">{{ index + 1 }}</span>
              </div>
              <span class="step-label">{{ step.label }}</span>
            </div>
          </div>
          
          <p class="progress-text">
            {{ currentStep < progressSteps.length ? progressSteps[currentStep].label + '...' : '分析即将完成...' }}
          </p>
        </div>
      </div>
    </div>

    <!-- 分析结果 -->
    <div v-else-if="analysis" class="analysis-results">
      <div class="results-grid">
        <!-- 项目概览 -->
        <div class="result-card">
          <div class="card-header">
            <h4 class="card-title">项目概览</h4>
          </div>
          <div class="card-content">
            <p class="content-text">{{ analysis.project_overview || '暂无数据' }}</p>
          </div>
        </div>

        <!-- 甲方信息 -->
        <div class="result-card">
          <div class="card-header">
            <h4 class="card-title">甲方信息</h4>
          </div>
          <div class="card-content">
            <p class="content-text">{{ analysis.client_info || '暂无数据' }}</p>
          </div>
        </div>

        <!-- 预算信息 -->
        <div class="result-card">
          <div class="card-header">
            <h4 class="card-title">预算信息</h4>
          </div>
          <div class="card-content">
            <p class="content-text">{{ analysis.budget_info || '暂无数据' }}</p>
          </div>
        </div>

        <!-- 详细需求 -->
        <div class="result-card full-width">
          <div class="card-header">
            <h4 class="card-title">详细需求</h4>
          </div>
          <div class="card-content">
            <p class="content-text">{{ analysis.detailed_requirements || '暂无数据' }}</p>
          </div>
        </div>
      </div>

      <!-- 需求分级 -->
      <div class="requirements-classification">
        <h4 class="classification-title">需求分级</h4>
        <el-tabs v-model="activeRequirementTab" class="requirement-tabs">
          <el-tab-pane label="关键需求" name="critical">
            <div class="requirement-content">
              <div v-if="analysis.critical_requirements" v-html="analysis.critical_requirements"></div>
              <p v-else class="empty-requirement">暂无关键需求数据</p>
            </div>
          </el-tab-pane>
          <el-tab-pane label="重要需求" name="important">
            <div class="requirement-content">
              <div v-if="analysis.important_requirements" v-html="analysis.important_requirements"></div>
              <p v-else class="empty-requirement">暂无重要需求数据</p>
            </div>
          </el-tab-pane>
          <el-tab-pane label="一般需求" name="general">
            <div class="requirement-content">
              <div v-if="analysis.general_requirements" v-html="analysis.general_requirements"></div>
              <p v-else class="empty-requirement">暂无一般需求数据</p>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="analysisError" class="error-state">
      <el-icon size="48" color="#ef4444"><Warning /></el-icon>
      <h4 class="error-title">分析失败</h4>
      <p class="error-text">{{ analysisError }}</p>
      <div class="error-actions">
        <el-button 
          type="primary" 
          @click="retryAnalysis"
          :disabled="retryCount >= maxRetries"
        >
          {{ retryCount >= maxRetries ? '已达到最大重试次数' : `重新分析 (${retryCount}/${maxRetries})` }}
        </el-button>
        <el-button 
          v-if="retryCount > 0" 
          @click="resetRetryCount"
          type="default"
        >
          重置重试次数
        </el-button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-icon size="48" color="#d1d5db"><Document /></el-icon>
      <h4 class="empty-title">尚未进行需求分析</h4>
      <p class="empty-text">点击"开始分析"按钮，AI将自动分析招标文件并提取关键需求信息。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Document, Warning, Check } from '@element-plus/icons-vue'
import { analysisApi } from '@/api/projects'

interface Props {
  projectId: number
}

interface RequirementAnalysis {
  id: number
  project_id: number
  user_id: string
  project_overview?: string
  client_info?: string
  budget_info?: string
  detailed_requirements?: string
  critical_requirements?: string
  important_requirements?: string
  general_requirements?: string
  created_at: string
}

interface AnalysisStatus {
  project_status: string
  has_analysis: boolean
  analysis_created_at?: string
}

const props = defineProps<Props>()

const analysis = ref<RequirementAnalysis | null>(null)
const analyzing = ref(false)
const analysisError = ref<string | null>(null)
const retryCount = ref(0)
const maxRetries = 3
const analysisTimeout = ref<number | null>(null)
const activeRequirementTab = ref('critical')
const progressInterval = ref<number | null>(null)
const analysisProgress = ref(0)
const progressSteps = ref([
  { key: 'parsing', label: '解析文档结构', completed: false },
  { key: 'extracting', label: '提取关键信息', completed: false },
  { key: 'classifying', label: '进行需求分级', completed: false },
  { key: 'finalizing', label: '生成分析报告', completed: false }
])
const currentStep = ref(0)

const startAnalysis = async () => {
  try {
    analyzing.value = true
    analysisError.value = null
    analysisProgress.value = 0
    ElMessage.info('开始分析招标文件，请稍候...')
    
    const response = await analysisApi.startAnalysis(props.projectId)
    
    if (response.status === 'exists') {
      ElMessage.info('分析结果已存在')
      analyzing.value = false
      await loadAnalysis()
    } else if (response.status === 'started') {
      ElMessage.success('分析已开始，正在处理中...')
      startProgressTracking()
      startAnalysisTimeout()
    }
  } catch (error: any) {
    console.error('开始分析失败:', error)
    const errorMessage = error.response?.data?.detail || '开始分析失败'
    ElMessage.error(errorMessage)
    analysisError.value = errorMessage
    analyzing.value = false
  }
}

const startAnalysisTimeout = () => {
  // 设置5分钟超时
  analysisTimeout.value = window.setTimeout(() => {
    if (analyzing.value) {
      analyzing.value = false
      analysisError.value = '分析超时，请重试'
      ElMessage.error('分析超时，请重试')
      stopProgressTracking()
    }
  }, 5 * 60 * 1000) // 5分钟
}

const startProgressTracking = () => {
  analysisProgress.value = 10
  currentStep.value = 0
  
  // 重置步骤状态
  progressSteps.value.forEach(step => {
    step.completed = false
  })
  
  progressInterval.value = window.setInterval(async () => {
    try {
      const status = await analysisApi.getAnalysisStatus(props.projectId)
      
      if (status.has_analysis) {
        // 分析完成
        analysisProgress.value = 100
        currentStep.value = progressSteps.value.length
        progressSteps.value.forEach(step => {
          step.completed = true
        })
        analyzing.value = false
        resetRetryCount() // 成功后重置重试次数
        ElMessage.success('需求分析完成')
        await loadAnalysis()
        stopProgressTracking()
      } else if (status.project_status === 'analyzing') {
        // 仍在分析中，更新进度
        updateProgressSteps()
      } else if (status.project_status === 'failed') {
        // 分析失败
        analyzing.value = false
        analysisError.value = '分析过程中发生错误'
        ElMessage.error('分析失败，请重试')
        stopProgressTracking()
      }
    } catch (error) {
      console.error('获取分析状态失败:', error)
      // 继续轮询，不中断用户体验
    }
  }, 2000) // 每2秒检查一次状态
}

const updateProgressSteps = () => {
  const elapsed = Date.now() - (analyzing.value ? Date.now() - 2000 : Date.now())
  const totalSteps = progressSteps.value.length
  
  // 模拟进度更新
  if (analysisProgress.value < 25) {
    analysisProgress.value = Math.min(analysisProgress.value + 3, 25)
    currentStep.value = 0
  } else if (analysisProgress.value < 50) {
    analysisProgress.value = Math.min(analysisProgress.value + 2, 50)
    currentStep.value = 1
    progressSteps.value[0].completed = true
  } else if (analysisProgress.value < 75) {
    analysisProgress.value = Math.min(analysisProgress.value + 2, 75)
    currentStep.value = 2
    progressSteps.value[1].completed = true
  } else if (analysisProgress.value < 90) {
    analysisProgress.value = Math.min(analysisProgress.value + 1, 90)
    currentStep.value = 3
    progressSteps.value[2].completed = true
  }
}

const stopProgressTracking = () => {
  if (progressInterval.value) {
    clearInterval(progressInterval.value)
    progressInterval.value = null
  }
  if (analysisTimeout.value) {
    clearTimeout(analysisTimeout.value)
    analysisTimeout.value = null
  }
}

const loadAnalysis = async () => {
  try {
    const response = await analysisApi.getAnalysisResult(props.projectId)
    
    if (response.analysis) {
      analysis.value = response.analysis
    } else if (response.status === 'analyzing') {
      analyzing.value = true
      startProgressTracking()
    }
  } catch (error: any) {
    console.error('加载分析结果失败:', error)
    if (error.response?.status !== 404) {
      const errorMessage = error.response?.data?.detail || '加载分析结果失败'
      ElMessage.error(errorMessage)
    }
  }
}

const retryAnalysis = async () => {
  if (retryCount.value >= maxRetries) {
    ElMessage.error(`已达到最大重试次数 (${maxRetries})，请稍后再试`)
    return
  }
  
  retryCount.value++
  analysisError.value = null
  ElMessage.info(`正在重试... (${retryCount.value}/${maxRetries})`)
  await startAnalysis()
}

const resetRetryCount = () => {
  retryCount.value = 0
}

onMounted(() => {
  loadAnalysis()
})

onUnmounted(() => {
  stopProgressTracking()
})
</script>

<style scoped>
.requirement-analysis-component {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.analyzing-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.analyzing-content {
  text-align: center;
  max-width: 400px;
}

.analyzing-icon {
  color: #3b82f6;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.analyzing-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 16px 0 8px 0;
}

.analyzing-text {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
  margin: 0 0 24px 0;
}

.progress-container {
  width: 100%;
  max-width: 400px;
  margin-top: 24px;
}

.progress-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 20px 0;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.progress-step {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.step-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
}

.step-completed .step-icon {
  background: #dcfce7;
  border: 2px solid #10b981;
}

.step-active .step-icon {
  background: #dbeafe;
  border: 2px solid #3b82f6;
}

.step-pending .step-icon {
  background: #f1f5f9;
  border: 2px solid #cbd5e1;
}

.step-number {
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
}

.step-active .step-number {
  color: #3b82f6;
}

.step-label {
  color: #374151;
  font-weight: 500;
}

.step-completed .step-label {
  color: #059669;
}

.step-active .step-label {
  color: #1d4ed8;
  font-weight: 600;
}

.step-pending .step-label {
  color: #9ca3af;
}

.progress-text {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
  margin: 8px 0 0 0;
  font-weight: 500;
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  text-align: center;
}

.error-title {
  font-size: 18px;
  font-weight: 600;
  color: #ef4444;
  margin: 16px 0 8px 0;
}

.error-text {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
  max-width: 400px;
  margin: 0 0 24px 0;
}

.error-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.analysis-results {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.result-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.result-card.full-width {
  grid-column: 1 / -1;
}

.card-header {
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.card-content {
  padding: 20px;
}

.content-text {
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
  margin: 0;
}

.requirements-classification {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.classification-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  padding: 16px 20px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.requirement-tabs {
  padding: 0 20px;
}

.requirement-content {
  padding: 20px 0;
  min-height: 200px;
}

.requirement-content :deep(ul) {
  margin: 0;
  padding-left: 20px;
}

.requirement-content :deep(li) {
  margin-bottom: 8px;
  line-height: 1.5;
}

.empty-requirement {
  color: #9ca3af;
  font-style: italic;
  text-align: center;
  margin: 40px 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  text-align: center;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #6b7280;
  margin: 16px 0 8px 0;
}

.empty-text {
  font-size: 14px;
  color: #9ca3af;
  line-height: 1.5;
  max-width: 400px;
  margin: 0;
}

@media (max-width: 768px) {
  .results-grid {
    grid-template-columns: 1fr;
  }
  
  .analysis-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
}
</style>