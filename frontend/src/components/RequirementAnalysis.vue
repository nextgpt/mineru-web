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

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-icon size="48" color="#d1d5db"><Document /></el-icon>
      <h4 class="empty-title">尚未进行需求分析</h4>
      <p class="empty-text">点击"开始分析"按钮，AI将自动分析招标文件并提取关键需求信息。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Document } from '@element-plus/icons-vue'

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

const props = defineProps<Props>()

const analysis = ref<RequirementAnalysis | null>(null)
const analyzing = ref(false)
const activeRequirementTab = ref('critical')

const startAnalysis = async () => {
  try {
    analyzing.value = true
    ElMessage.info('开始分析招标文件，请稍候...')
    
    // TODO: 调用后端API开始分析
    // await analysisApi.startAnalysis(props.projectId)
    
    // 模拟分析过程
    setTimeout(() => {
      analyzing.value = false
      ElMessage.success('需求分析完成')
      loadAnalysis()
    }, 3000)
  } catch (error) {
    console.error('开始分析失败:', error)
    ElMessage.error('开始分析失败')
    analyzing.value = false
  }
}

const loadAnalysis = async () => {
  try {
    // TODO: 调用后端API获取分析结果
    // analysis.value = await analysisApi.getAnalysis(props.projectId)
    
    // 模拟数据
    analysis.value = {
      id: 1,
      project_id: props.projectId,
      user_id: 'user123',
      project_overview: '这是一个关于智能办公系统建设的招标项目，旨在提升办公效率和数字化水平。',
      client_info: '招标单位：某市政府办公厅，联系人：张主任，预算范围：100-200万元。',
      budget_info: '项目总预算约150万元，包含软件开发、硬件采购、实施部署等费用。',
      detailed_requirements: '系统需要包含文档管理、流程审批、视频会议、即时通讯等核心功能模块。',
      critical_requirements: '<ul><li>系统稳定性要求99.9%以上</li><li>支持1000+并发用户</li><li>数据安全等级要求三级</li></ul>',
      important_requirements: '<ul><li>界面友好易用</li><li>移动端适配</li><li>与现有系统集成</li></ul>',
      general_requirements: '<ul><li>提供用户培训</li><li>一年免费维护</li><li>技术文档完整</li></ul>',
      created_at: new Date().toISOString()
    }
  } catch (error) {
    console.error('加载分析结果失败:', error)
  }
}

onMounted(() => {
  loadAnalysis()
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
  margin: 0;
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