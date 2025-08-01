<template>
  <div class="project-info-component">
    <div class="info-section">
      <h3 class="section-title">项目基本信息</h3>
      <div class="info-grid">
        <div class="info-item">
          <label class="info-label">项目名称</label>
          <div class="info-value">{{ project.name }}</div>
        </div>
        <div class="info-item">
          <label class="info-label">项目状态</label>
          <div class="info-value">
            <el-tag :type="getStatusType(project.status)" size="small">
              {{ getStatusText(project.status) }}
            </el-tag>
          </div>
        </div>
        <div class="info-item">
          <label class="info-label">创建时间</label>
          <div class="info-value">{{ formatDate(project.created_at) }}</div>
        </div>
        <div class="info-item">
          <label class="info-label">最后更新</label>
          <div class="info-value">{{ formatDate(project.updated_at) }}</div>
        </div>
        <div class="info-item full-width">
          <label class="info-label">项目描述</label>
          <div class="info-value">{{ project.description || '暂无描述' }}</div>
        </div>
      </div>
    </div>

    <div class="info-section" v-if="project.original_file">
      <h3 class="section-title">招标文件信息</h3>
      <div class="file-info-card">
        <div class="file-icon">
          <el-icon size="32"><Document /></el-icon>
        </div>
        <div class="file-details">
          <div class="file-name">{{ project.original_file.filename }}</div>
          <div class="file-meta">
            <span class="file-size">{{ formatFileSize(project.original_file.size) }}</span>
            <span class="file-status">{{ project.original_file.status }}</span>
          </div>
        </div>
        <div class="file-actions">
          <el-button size="small" @click="downloadFile">下载</el-button>
          <el-button size="small" type="primary" @click="previewFile">预览</el-button>
        </div>
      </div>
    </div>

    <div class="info-section" v-else>
      <h3 class="section-title">招标文件</h3>
      <div class="empty-state">
        <el-icon size="48" color="#d1d5db"><UploadFilled /></el-icon>
        <p class="empty-text">尚未上传招标文件</p>
        <p class="empty-hint">请先上传招标文件以开始项目分析</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { Document, UploadFilled } from '@element-plus/icons-vue'
import type { Project } from '@/api/projects'

interface Props {
  project: Project
}

const props = defineProps<Props>()
const emit = defineEmits<{
  refresh: []
}>()

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    created: 'info',
    parsing: 'warning',
    analyzing: 'warning', 
    outline_generated: 'primary',
    document_generating: 'primary',
    completed: 'success',
    failed: 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    created: '已创建',
    parsing: '解析中',
    analyzing: '分析中',
    outline_generated: '大纲已生成',
    document_generating: '生成中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[status] || status
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const downloadFile = () => {
  ElMessage.info('下载功能开发中...')
}

const previewFile = () => {
  ElMessage.info('预览功能开发中...')
}
</script>

<style scoped>
.project-info-component {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e5e7eb;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
}

.info-value {
  font-size: 14px;
  color: #1f2937;
  line-height: 1.5;
}

.file-info-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.file-icon {
  color: #6b7280;
}

.file-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-name {
  font-size: 16px;
  font-weight: 500;
  color: #1f2937;
}

.file-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #6b7280;
}

.file-actions {
  display: flex;
  gap: 8px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  color: #6b7280;
  margin: 16px 0 8px 0;
}

.empty-hint {
  font-size: 14px;
  color: #9ca3af;
  margin: 0;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .file-info-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .file-actions {
    align-self: stretch;
    justify-content: flex-end;
  }
}
</style>