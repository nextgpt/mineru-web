<template>
  <div class="project-detail">
    <!-- 项目头部信息 -->
    <div class="project-header">
      <div class="header-left">
        <el-button @click="$router.back()" type="text" class="back-btn">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <div class="project-info">
          <h1 class="project-title">{{ project?.project_name || '加载中...' }}</h1>
          <p class="project-meta">
            <span>基于文件：{{ project?.source_filename }}</span>
            <span class="divider">•</span>
            <span>创建时间：{{ formatTime(project?.created_at) }}</span>
          </p>
        </div>
      </div>
      <div class="header-right">
        <el-tag :type="getStatusType(project?.status)" size="large">
          {{ getStatusText(project?.status) }}
        </el-tag>
      </div>
    </div>

    <!-- 步骤导航 -->
    <div class="steps-container">
      <el-steps :active="currentStep" align-center finish-status="success">
        <el-step title="文件分析" description="提取关键信息" />
        <el-step title="大纲生成" description="生成方案框架" />
        <el-step title="内容生成" description="AI撰写内容" />
        <el-step title="文档导出" description="生成最终标书" />
      </el-steps>
    </div>

    <!-- 步骤内容 -->
    <div class="step-content">
      <AnalysisStep 
        v-if="currentStep === 0" 
        :project="project" 
        @next="handleNext"
        @update="handleProjectUpdate"
      />
      <OutlineStep 
        v-else-if="currentStep === 1" 
        :project="project" 
        @next="handleNext"
        @prev="handlePrev"
        @update="handleProjectUpdate"
      />
      <ContentStep 
        v-else-if="currentStep === 2" 
        :project="project" 
        @next="handleNext"
        @prev="handlePrev"
        @update="handleProjectUpdate"
      />
      <ExportStep 
        v-else-if="currentStep === 3" 
        :project="project" 
        @prev="handlePrev"
        @update="handleProjectUpdate"
      />
    </div>

    <!-- 进度指示器 -->
    <ProgressIndicator 
      v-if="project && showProgressIndicator"
      :project-id="project.id"
      @cancel="handleTaskCancel"
      @hide="showProgressIndicator = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { getUserId } from '@/utils/user'
import { wsService } from '@/services/websocket'

import AnalysisStep from '@/components/AnalysisStep.vue'
import OutlineStep from '@/components/OutlineStep.vue'
import ContentStep from '@/components/ContentStep.vue'
import ExportStep from '@/components/ExportStep.vue'
import ProgressIndicator from '@/components/ProgressIndicator.vue'

interface ProjectItem {
  id: string
  project_name: string
  source_filename: string
  status: 'analyzing' | 'analyzed' | 'outlining' | 'outlined' | 'generating' | 'generated' | 'exporting' | 'completed' | 'failed'
  progress?: number
  created_at: string
  updated_at: string
}

const route = useRoute()
const project = ref<ProjectItem | null>(null)
const showProgressIndicator = ref(false)

const currentStep = computed(() => {
  if (!project.value) return 0
  
  const status = project.value.status
  switch (status) {
    case 'analyzing':
      return 0
    case 'analyzed':
    case 'outlining':
      return 1
    case 'outlined':
    case 'generating':
      return 2
    case 'generated':
    case 'exporting':
    case 'completed':
      return 3
    default:
      return 0
  }
})

const formatTime = (dateStr?: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

const getStatusType = (status?: string) => {
  const map: Record<string, string> = {
    analyzing: 'warning',
    analyzed: 'info',
    outlining: 'warning',
    outlined: 'info',
    generating: 'warning',
    generated: 'info',
    exporting: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status || ''] || 'info'
}

const getStatusText = (status?: string) => {
  const map: Record<string, string> = {
    analyzing: '分析中',
    analyzed: '已分析',
    outlining: '大纲生成中',
    outlined: '大纲已生成',
    generating: '内容生成中',
    generated: '内容已生成',
    exporting: '导出中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status || ''] || '未知状态'
}

const fetchProject = async () => {
  try {
    const res = await axios.get(`/api/tender/projects/${route.params.id}`, {
      headers: { 'X-User-Id': getUserId() }
    })
    project.value = res.data
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '获取项目信息失败')
  }
}

const handleNext = () => {
  // 步骤会根据项目状态自动更新
  fetchProject()
}

const handlePrev = () => {
  // 允许用户返回上一步查看
  fetchProject()
}

const handleProjectUpdate = (updatedProject: ProjectItem) => {
  project.value = updatedProject
  
  // 显示进度指示器（当任务正在进行时）
  const activeStatuses = ['analyzing', 'outlining', 'generating', 'exporting']
  showProgressIndicator.value = activeStatuses.includes(updatedProject.status)
}

const handleTaskCancel = async () => {
  if (!project.value) return
  
  try {
    await ElMessageBox.confirm(
      '确定要取消当前任务吗？',
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.post(`/api/tender/projects/${project.value.id}/cancel`, {}, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    ElMessage.success('任务已取消')
    await fetchProject()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '取消任务失败')
    }
  }
}

onMounted(() => {
  fetchProject()
  
  // 监听WebSocket项目更新
  wsService.on('project_update', (data: any) => {
    if (project.value && data.project_id === project.value.id) {
      handleProjectUpdate({
        ...project.value,
        status: data.status,
        progress: data.progress
      })
    }
  })
})

onUnmounted(() => {
  // 清理WebSocket监听器
  wsService.off('project_update', handleProjectUpdate)
})

// 监听路由参数变化
watch(() => route.params.id, () => {
  if (route.params.id) {
    fetchProject()
  }
})
</script>

<style scoped>
.project-detail {
  min-height: 100vh;
  background: #f7f8fa;
  padding: 24px 32px;
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.back-btn {
  padding: 8px;
  font-size: 16px;
  color: #6b7280;
  margin-top: 4px;
}

.back-btn:hover {
  color: #409eff;
}

.project-info {
  flex: 1;
}

.project-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
  line-height: 1.3;
}

.project-meta {
  color: #6b7280;
  font-size: 0.875rem;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.divider {
  color: #d1d5db;
}

.header-right {
  display: flex;
  align-items: center;
}

.steps-container {
  background: white;
  padding: 32px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  margin-bottom: 24px;
}

.step-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  min-height: 500px;
}

:deep(.el-steps) {
  max-width: 800px;
  margin: 0 auto;
}

:deep(.el-step__title) {
  font-size: 1rem;
  font-weight: 500;
}

:deep(.el-step__description) {
  font-size: 0.875rem;
}

:deep(.el-tag--large) {
  padding: 8px 16px;
  font-size: 0.875rem;
  font-weight: 500;
}
</style>