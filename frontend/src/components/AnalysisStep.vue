<template>
  <div class="analysis-step">
    <div class="step-header">
      <h2 class="step-title">招标文件分析</h2>
      <p class="step-description">系统正在分析招标文件，提取关键信息</p>
    </div>

    <div class="step-body">
      <!-- 分析状态 -->
      <div v-if="project?.status === 'analyzing'" class="analyzing-state">
        <div class="loading-container">
          <el-icon class="loading-icon" size="48"><Loading /></el-icon>
          <h3>正在分析招标文件...</h3>
          <p>请稍候，系统正在提取项目信息、技术要求和评分标准</p>
        </div>
      </div>

      <!-- 分析结果 -->
      <div v-else-if="analysisResult" class="analysis-result">
        <el-tabs v-model="activeTab" type="border-card">
          <el-tab-pane label="项目信息" name="project_info">
            <div class="info-section">
              <div class="info-grid">
                <div class="info-item" v-for="(value, key) in analysisResult.project_info" :key="key">
                  <label class="info-label">{{ formatLabel(key) }}</label>
                  <div class="info-value">{{ value || '未提取到' }}</div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="技术要求" name="technical_requirements">
            <div class="info-section">
              <div v-if="analysisResult.technical_requirements.functional_requirements" class="requirement-group">
                <h4>功能性要求</h4>
                <ul class="requirement-list">
                  <li v-for="(req, index) in analysisResult.technical_requirements.functional_requirements" :key="index">
                    {{ req }}
                  </li>
                </ul>
              </div>
              
              <div v-if="analysisResult.technical_requirements.performance_requirements" class="requirement-group">
                <h4>性能要求</h4>
                <div class="requirement-content">{{ analysisResult.technical_requirements.performance_requirements }}</div>
              </div>
              
              <div v-if="analysisResult.technical_requirements.technical_specifications" class="requirement-group">
                <h4>技术规格</h4>
                <div class="requirement-content">{{ analysisResult.technical_requirements.technical_specifications }}</div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="评分标准" name="evaluation_criteria">
            <div class="info-section">
              <div v-if="analysisResult.evaluation_criteria.technical_score" class="criteria-group">
                <h4>技术分评分</h4>
                <div class="criteria-content">{{ analysisResult.evaluation_criteria.technical_score }}</div>
              </div>
              
              <div v-if="analysisResult.evaluation_criteria.commercial_score" class="criteria-group">
                <h4>商务分评分</h4>
                <div class="criteria-content">{{ analysisResult.evaluation_criteria.commercial_score }}</div>
              </div>
              
              <div v-if="analysisResult.evaluation_criteria.evaluation_method" class="criteria-group">
                <h4>评标方法</h4>
                <div class="criteria-content">{{ analysisResult.evaluation_criteria.evaluation_method }}</div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="提交要求" name="submission_requirements">
            <div class="info-section">
              <div class="info-grid">
                <div class="info-item" v-for="(value, key) in analysisResult.submission_requirements" :key="key">
                  <label class="info-label">{{ formatLabel(key) }}</label>
                  <div class="info-value">{{ value || '未提取到' }}</div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>

        <!-- 编辑按钮 -->
        <div class="edit-section">
          <el-button @click="showEditDialog = true" type="primary" plain>
            <el-icon><Edit /></el-icon> 编辑分析结果
          </el-button>
        </div>
      </div>

      <!-- 分析失败 -->
      <div v-else-if="project?.status === 'failed'" class="failed-state">
        <el-result icon="error" title="分析失败" sub-title="招标文件分析过程中出现错误">
          <template #extra>
            <el-button type="primary" @click="retryAnalysis">重新分析</el-button>
          </template>
        </el-result>
      </div>

      <!-- 未开始分析 -->
      <div v-else class="not-started-state">
        <el-result icon="info" title="等待分析" sub-title="点击下方按钮开始分析招标文件">
          <template #extra>
            <el-button type="primary" @click="startAnalysis" :loading="analyzing">开始分析</el-button>
          </template>
        </el-result>
      </div>
    </div>

    <!-- 步骤操作 -->
    <div class="step-actions" v-if="project?.status === 'analyzed'">
      <el-button type="primary" @click="proceedToNext" size="large">
        下一步：生成大纲 <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑分析结果" width="800px" :close-on-click-modal="false">
      <el-form :model="editForm" label-width="120px">
        <el-tabs v-model="editActiveTab">
          <el-tab-pane label="项目信息" name="project_info">
            <div v-for="(value, key) in editForm.project_info" :key="key" style="margin-bottom: 16px;">
              <el-form-item :label="formatLabel(key)">
                <el-input v-model="editForm.project_info[key]" />
              </el-form-item>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="技术要求" name="technical_requirements">
            <el-form-item label="功能性要求">
              <el-input 
                v-model="editForm.technical_requirements.functional_requirements_text" 
                type="textarea" 
                :rows="4"
                placeholder="每行一个要求"
              />
            </el-form-item>
            <el-form-item label="性能要求">
              <el-input 
                v-model="editForm.technical_requirements.performance_requirements" 
                type="textarea" 
                :rows="3"
              />
            </el-form-item>
            <el-form-item label="技术规格">
              <el-input 
                v-model="editForm.technical_requirements.technical_specifications" 
                type="textarea" 
                :rows="3"
              />
            </el-form-item>
          </el-tab-pane>
          
          <el-tab-pane label="评分标准" name="evaluation_criteria">
            <el-form-item label="技术分评分">
              <el-input 
                v-model="editForm.evaluation_criteria.technical_score" 
                type="textarea" 
                :rows="3"
              />
            </el-form-item>
            <el-form-item label="商务分评分">
              <el-input 
                v-model="editForm.evaluation_criteria.commercial_score" 
                type="textarea" 
                :rows="3"
              />
            </el-form-item>
            <el-form-item label="评标方法">
              <el-input 
                v-model="editForm.evaluation_criteria.evaluation_method" 
                type="textarea" 
                :rows="3"
              />
            </el-form-item>
          </el-tab-pane>
        </el-tabs>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAnalysis" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { Loading, Edit, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { getUserId } from '@/utils/user'

interface ProjectItem {
  id: string
  project_name: string
  source_filename: string
  status: string
  progress?: number
  created_at: string
  updated_at: string
}

interface AnalysisResult {
  project_info: Record<string, any>
  technical_requirements: Record<string, any>
  evaluation_criteria: Record<string, any>
  submission_requirements: Record<string, any>
}

const props = defineProps<{
  project: ProjectItem | null
}>()

const emit = defineEmits<{
  next: []
  update: [project: ProjectItem]
}>()

const activeTab = ref('project_info')
const editActiveTab = ref('project_info')
const showEditDialog = ref(false)
const analyzing = ref(false)
const saving = ref(false)
const analysisResult = ref<AnalysisResult | null>(null)

const editForm = reactive({
  project_info: {} as Record<string, string>,
  technical_requirements: {
    functional_requirements_text: '',
    performance_requirements: '',
    technical_specifications: ''
  },
  evaluation_criteria: {
    technical_score: '',
    commercial_score: '',
    evaluation_method: ''
  },
  submission_requirements: {} as Record<string, string>
})

const formatLabel = (key: string) => {
  const labelMap: Record<string, string> = {
    project_name: '项目名称',
    budget: '项目预算',
    duration: '项目工期',
    location: '项目地点',
    contact_info: '联系方式',
    deadline: '投标截止时间',
    document_format: '文档格式要求',
    submission_method: '提交方式',
    required_documents: '必需文档清单',
    document_structure: '文档结构要求'
  }
  return labelMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const fetchAnalysisResult = async () => {
  if (!props.project) return
  
  try {
    const res = await axios.get(`/api/tender/projects/${props.project.id}/analysis`, {
      headers: { 'X-User-Id': getUserId() }
    })
    analysisResult.value = res.data
    
    // 初始化编辑表单
    if (res.data) {
      Object.assign(editForm.project_info, res.data.project_info || {})
      Object.assign(editForm.technical_requirements, {
        functional_requirements_text: Array.isArray(res.data.technical_requirements?.functional_requirements) 
          ? res.data.technical_requirements.functional_requirements.join('\n')
          : res.data.technical_requirements?.functional_requirements || '',
        performance_requirements: res.data.technical_requirements?.performance_requirements || '',
        technical_specifications: res.data.technical_requirements?.technical_specifications || ''
      })
      Object.assign(editForm.evaluation_criteria, res.data.evaluation_criteria || {})
      Object.assign(editForm.submission_requirements, res.data.submission_requirements || {})
    }
  } catch (e: any) {
    if (e.response?.status !== 404) {
      ElMessage.error('获取分析结果失败')
    }
  }
}

const startAnalysis = async () => {
  if (!props.project) return
  
  analyzing.value = true
  try {
    await axios.post(`/api/tender/projects/${props.project.id}/analyze`, {}, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    ElMessage.success('分析任务已启动')
    
    // 更新项目状态
    emit('update', { ...props.project, status: 'analyzing' })
    
    // 开始轮询检查状态
    pollAnalysisStatus()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '启动分析失败')
  } finally {
    analyzing.value = false
  }
}

const retryAnalysis = () => {
  startAnalysis()
}

const pollAnalysisStatus = () => {
  const timer = setInterval(async () => {
    if (!props.project) {
      clearInterval(timer)
      return
    }
    
    try {
      const res = await axios.get(`/api/tender/projects/${props.project.id}`, {
        headers: { 'X-User-Id': getUserId() }
      })
      
      emit('update', res.data)
      
      if (res.data.status === 'analyzed') {
        clearInterval(timer)
        await fetchAnalysisResult()
      } else if (res.data.status === 'failed') {
        clearInterval(timer)
      }
    } catch (e) {
      clearInterval(timer)
    }
  }, 3000)
}

const saveAnalysis = async () => {
  if (!props.project) return
  
  saving.value = true
  try {
    // 处理功能性要求
    const functionalRequirements = editForm.technical_requirements.functional_requirements_text
      .split('\n')
      .filter(req => req.trim())
    
    const updateData = {
      project_info: editForm.project_info,
      technical_requirements: {
        functional_requirements: functionalRequirements,
        performance_requirements: editForm.technical_requirements.performance_requirements,
        technical_specifications: editForm.technical_requirements.technical_specifications
      },
      evaluation_criteria: editForm.evaluation_criteria,
      submission_requirements: editForm.submission_requirements
    }
    
    await axios.put(`/api/tender/projects/${props.project.id}/analysis`, updateData, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    ElMessage.success('分析结果已保存')
    showEditDialog.value = false
    await fetchAnalysisResult()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const proceedToNext = () => {
  emit('next')
}

// 监听项目变化
watch(() => props.project, (newProject) => {
  if (newProject && (newProject.status === 'analyzed' || newProject.status === 'outlined')) {
    fetchAnalysisResult()
  }
}, { immediate: true })

onMounted(() => {
  if (props.project?.status === 'analyzing') {
    pollAnalysisStatus()
  }
})
</script>

<style scoped>
.analysis-step {
  padding: 32px;
}

.step-header {
  text-align: center;
  margin-bottom: 32px;
}

.step-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.step-description {
  color: #6b7280;
  font-size: 1rem;
  margin: 0;
}

.step-body {
  margin-bottom: 32px;
}

.analyzing-state {
  text-align: center;
  padding: 64px 32px;
}

.loading-container h3 {
  font-size: 1.25rem;
  color: #1f2937;
  margin: 16px 0 8px 0;
}

.loading-container p {
  color: #6b7280;
  margin: 0;
}

.loading-icon {
  color: #409eff;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.analysis-result {
  margin-bottom: 24px;
}

.info-section {
  padding: 24px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.info-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  background: #f9fafb;
}

.info-label {
  display: block;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
  font-size: 0.875rem;
}

.info-value {
  color: #1f2937;
  font-size: 0.875rem;
  line-height: 1.5;
  word-break: break-word;
}

.requirement-group, .criteria-group {
  margin-bottom: 24px;
}

.requirement-group h4, .criteria-group h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e5e7eb;
}

.requirement-list {
  margin: 0;
  padding-left: 20px;
}

.requirement-list li {
  margin-bottom: 8px;
  color: #374151;
  line-height: 1.5;
}

.requirement-content, .criteria-content {
  color: #374151;
  line-height: 1.6;
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.edit-section {
  text-align: center;
  padding: 24px;
  border-top: 1px solid #e5e7eb;
}

.step-actions {
  text-align: center;
  padding: 24px;
  border-top: 1px solid #e5e7eb;
}

.failed-state, .not-started-state {
  padding: 32px;
}

:deep(.el-tabs--border-card) {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

:deep(.el-tabs--border-card .el-tabs__header) {
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

:deep(.el-result) {
  padding: 32px;
}
</style>