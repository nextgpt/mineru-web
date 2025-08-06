<template>
  <div class="parsing-progress">
    <div class="progress-header">
      <div class="progress-info">
        <h3 class="progress-title">{{ title }}</h3>
        <p class="progress-subtitle">{{ subtitle }}</p>
      </div>
      <el-tag :type="getStatusType(status)" size="large">
        {{ getStatusText(status) }}
      </el-tag>
    </div>

    <div class="progress-content">
      <!-- 解析阶段指示器 -->
      <div class="parsing-stages">
        <div 
          v-for="stage in stages" 
          :key="stage.id"
          class="stage-item"
          :class="{ 
            'active': currentStage === stage.id,
            'completed': currentStage > stage.id,
            'error': status === 'error' && currentStage === stage.id
          }"
        >
          <div class="stage-icon">
            <el-icon v-if="currentStage > stage.id" class="success-icon">
              <Check />
            </el-icon>
            <el-icon v-else-if="status === 'error' && currentStage === stage.id" class="error-icon">
              <Close />
            </el-icon>
            <div v-else-if="currentStage === stage.id" class="loading-icon">
              <el-icon class="rotating">
                <Loading />
              </el-icon>
            </div>
            <div v-else class="pending-icon">{{ stage.id }}</div>
          </div>
          <div class="stage-content">
            <div class="stage-title">{{ stage.title }}</div>
            <div class="stage-description">{{ stage.description }}</div>
          </div>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-bar-container">
        <el-progress 
          :percentage="progressPercentage" 
          :status="status === 'error' ? 'exception' : status === 'completed' ? 'success' : undefined"
          :stroke-width="12"
          :show-text="false"
        />
        <div class="progress-text">
          {{ progressText }}
        </div>
      </div>

      <!-- 详细信息 -->
      <div class="progress-details" v-if="details">
        <div class="details-content">
          {{ details }}
        </div>
      </div>

      <!-- 错误信息 -->
      <div class="error-message" v-if="status === 'error' && errorMessage">
        <el-alert
          :title="errorMessage"
          type="error"
          :closable="false"
          show-icon
        />
        <div class="error-actions">
          <el-button type="primary" @click="$emit('retry')">
            <el-icon><Refresh /></el-icon>
            重试
          </el-button>
          <el-button @click="$emit('cancel')">取消</el-button>
        </div>
      </div>

      <!-- 成功操作 -->
      <div class="success-actions" v-if="status === 'completed'">
        <el-button type="primary" @click="$emit('continue')">
          <el-icon><ArrowRight /></el-icon>
          继续下一步
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Check, Close, Loading, Refresh, ArrowRight } from '@element-plus/icons-vue'

interface ParsingStage {
  id: number
  title: string
  description: string
}

interface Props {
  title: string
  subtitle: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  currentStage: number
  progressPercentage: number
  progressText: string
  details?: string
  errorMessage?: string
}

withDefaults(defineProps<Props>(), {
  title: '文档解析中',
  subtitle: '正在解析您的招标文档，请稍候...',
  status: 'processing',
  currentStage: 1,
  progressPercentage: 0,
  progressText: '准备中...'
})

defineEmits<{
  retry: []
  cancel: []
  continue: []
}>()

const stages: ParsingStage[] = [
  {
    id: 1,
    title: '创建数据集',
    description: '为文档创建专用知识库'
  },
  {
    id: 2,
    title: '上传文档',
    description: '将文档上传到知识库'
  },
  {
    id: 3,
    title: '启动解析',
    description: '开始解析文档内容'
  },
  {
    id: 4,
    title: '内容分析',
    description: '分析文档结构和内容'
  },
  {
    id: 5,
    title: '完成处理',
    description: '解析完成，准备生成大纲'
  }
]

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    error: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    error: '失败'
  }
  return map[status] || '未知'
}
</script>

<style scoped>
.parsing-progress {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.progress-info {
  flex: 1;
}

.progress-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.progress-subtitle {
  font-size: 1rem;
  color: #666;
  margin: 0;
}

.parsing-stages {
  margin-bottom: 32px;
}

.stage-item {
  display: flex;
  align-items: center;
  padding: 16px 0;
  border-left: 2px solid #e9ecef;
  margin-left: 20px;
  position: relative;
  transition: all 0.3s ease;
}

.stage-item.active {
  border-left-color: #409eff;
}

.stage-item.completed {
  border-left-color: #67c23a;
}

.stage-item.error {
  border-left-color: #f56c6c;
}

.stage-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border: 2px solid #e9ecef;
  margin-left: -21px;
  margin-right: 16px;
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
}

.stage-item.active .stage-icon {
  background: #409eff;
  border-color: #409eff;
  color: white;
}

.stage-item.completed .stage-icon {
  background: #67c23a;
  border-color: #67c23a;
  color: white;
}

.stage-item.error .stage-icon {
  background: #f56c6c;
  border-color: #f56c6c;
  color: white;
}

.pending-icon {
  font-size: 14px;
  font-weight: 600;
  color: #909399;
}

.stage-item.active .pending-icon {
  color: white;
}

.success-icon,
.error-icon {
  font-size: 18px;
}

.loading-icon {
  color: white;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.stage-content {
  flex: 1;
}

.stage-title {
  font-size: 1rem;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.stage-item.active .stage-title {
  color: #409eff;
  font-weight: 600;
}

.stage-item.completed .stage-title {
  color: #67c23a;
}

.stage-item.error .stage-title {
  color: #f56c6c;
}

.stage-description {
  font-size: 0.9rem;
  color: #666;
}

.progress-bar-container {
  margin-bottom: 24px;
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  font-size: 0.9rem;
  color: #666;
}

.progress-details {
  margin-bottom: 24px;
}

.details-content {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  font-size: 0.9rem;
  color: #666;
  border-left: 4px solid #409eff;
}

.error-message {
  margin-bottom: 24px;
}

.error-actions {
  margin-top: 16px;
  text-align: center;
}

.error-actions .el-button {
  margin: 0 8px;
}

.success-actions {
  text-align: center;
}

:deep(.el-progress-bar__outer) {
  border-radius: 6px;
  background-color: #f0f2f5;
}

:deep(.el-progress-bar__inner) {
  border-radius: 6px;
}

:deep(.el-alert) {
  border-radius: 8px;
}
</style>