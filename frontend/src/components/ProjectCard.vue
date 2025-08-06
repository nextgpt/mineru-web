<template>
  <div 
    class="project-card"
    @click="handleClick"
  >
    <div class="card-header">
      <el-icon class="file-icon"><Document /></el-icon>
      <div class="card-status">
        <el-tag 
          :type="getStatusType(project.status)" 
          size="small"
        >
          {{ getStatusText(project.status) }}
        </el-tag>
      </div>
    </div>
    
    <div class="card-content">
      <h3 class="project-name" :title="project.name">
        {{ project.name }}
      </h3>
      <p class="project-filename" :title="project.fileName">
        {{ project.fileName }}
      </p>
      <div class="project-meta">
        <span class="upload-time">{{ formatTime(project.uploadTime) }}</span>
        <span class="file-size">{{ formatFileSize(project.fileSize) }}</span>
      </div>
    </div>
    
    <div v-if="showActions" class="card-actions" @click.stop>
      <el-dropdown trigger="click" placement="bottom-end">
        <el-button type="text" size="small" class="action-button">
          <el-icon><MoreFilled /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="$emit('view', project)">
              <el-icon><View /></el-icon>
              查看详情
            </el-dropdown-item>
            <el-dropdown-item @click="$emit('edit', project)">
              <el-icon><Edit /></el-icon>
              编辑项目
            </el-dropdown-item>
            <el-dropdown-item 
              @click="$emit('delete', project)"
              divided
            >
              <el-icon><Delete /></el-icon>
              删除项目
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
    
    <!-- 状态指示器 -->
    <div v-if="project.status === 'uploading' || project.status === 'parsing' || project.status === 'generating'" class="progress-indicator">
      <el-progress 
        :percentage="getProgressPercentage(project.status)" 
        :show-text="false" 
        :stroke-width="3"
        status="success"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Document, MoreFilled, View, Edit, Delete } from '@element-plus/icons-vue'
import type { TenderProject } from '@/types/tender'

interface Props {
  project: TenderProject
  showActions?: boolean
}

interface Emits {
  (e: 'click', project: TenderProject): void
  (e: 'view', project: TenderProject): void
  (e: 'edit', project: TenderProject): void
  (e: 'delete', project: TenderProject): void
}

const props = withDefaults(defineProps<Props>(), {
  showActions: true
})

const emit = defineEmits<Emits>()

const handleClick = () => {
  emit('click', props.project)
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'ready':
    case 'completed':
      return 'success'
    case 'uploading':
    case 'parsing':
    case 'generating':
      return 'warning'
    case 'error':
      return 'danger'
    default:
      return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'uploading':
      return '上传中'
    case 'parsing':
      return '解析中'
    case 'ready':
      return '就绪'
    case 'generating':
      return '生成中'
    case 'completed':
      return '已完成'
    case 'error':
      return '错误'
    default:
      return '未知'
  }
}

const getProgressPercentage = (status: string) => {
  switch (status) {
    case 'uploading':
      return 30
    case 'parsing':
      return 60
    case 'generating':
      return 80
    default:
      return 0
  }
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatFileSize = (size: number) => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  if (size < 1024 * 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`
  return `${(size / 1024 / 1024 / 1024).toFixed(1)} GB`
}
</script>

<style scoped>
.project-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.04);
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #f0f0f0;
  position: relative;
  height: 200px;
  display: flex;
  flex-direction: column;
}

.project-card:hover {
  box-shadow: 0 4px 20px 0 rgba(0,0,0,0.08);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.file-icon {
  font-size: 24px;
  color: #409eff;
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.project-name {
  font-size: 16px;
  font-weight: 600;
  color: #222;
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.project-filename {
  font-size: 14px;
  color: #666;
  margin: 0 0 12px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.3;
}

.project-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #999;
  margin-top: auto;
}

.card-actions {
  position: absolute;
  top: 16px;
  right: 16px;
  opacity: 0;
  transition: opacity 0.2s;
}

.project-card:hover .card-actions {
  opacity: 1;
}

.action-button {
  width: 24px;
  height: 24px;
  padding: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
}

.action-button:hover {
  background: rgba(255, 255, 255, 1);
}

.progress-indicator {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0 20px 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .project-card {
    height: auto;
    min-height: 160px;
  }
  
  .card-actions {
    opacity: 1;
  }
  
  .project-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>