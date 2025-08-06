<template>
  <div class="project-list">
    <el-table 
      :data="projects" 
      @row-click="handleRowClick"
      stripe
      style="width: 100%"
      :header-cell-style="{ background: '#fafafa', color: '#606266' }"
    >
      <el-table-column prop="name" label="项目名称" min-width="200">
        <template #default="{ row }">
          <div class="project-name-cell">
            <el-icon class="file-icon"><Document /></el-icon>
            <span class="project-name" :title="row.name">{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column prop="fileName" label="文件名" min-width="180">
        <template #default="{ row }">
          <span class="filename" :title="row.fileName">{{ row.fileName }}</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <div class="status-cell">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
            <div 
              v-if="row.status === 'uploading' || row.status === 'parsing' || row.status === 'generating'" 
              class="status-progress"
            >
              <el-progress 
                :percentage="getProgressPercentage(row.status)" 
                :show-text="false" 
                :stroke-width="2"
                status="success"
              />
            </div>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column prop="fileSize" label="文件大小" width="100">
        <template #default="{ row }">
          <span class="file-size">{{ formatFileSize(row.fileSize) }}</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="uploadTime" label="上传时间" width="160">
        <template #default="{ row }">
          <span class="upload-time">{{ formatTime(row.uploadTime) }}</span>
        </template>
      </el-table-column>
      
      <el-table-column v-if="showActions" label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <div class="action-buttons">
            <el-dropdown trigger="click" placement="bottom-end">
              <el-button type="text" size="small">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="$emit('view', row)">
                    <el-icon><View /></el-icon>
                    查看详情
                  </el-dropdown-item>
                  <el-dropdown-item @click="$emit('edit', row)">
                    <el-icon><Edit /></el-icon>
                    编辑项目
                  </el-dropdown-item>
                  <el-dropdown-item 
                    @click="$emit('delete', row)"
                    divided
                  >
                    <el-icon><Delete /></el-icon>
                    删除项目
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { 
  Document, 
  MoreFilled, 
  View, 
  Edit, 
  Delete 
} from '@element-plus/icons-vue'
import type { TenderProject } from '@/types/tender'

interface Props {
  projects: TenderProject[]
  showActions?: boolean
}

interface Emits {
  (e: 'row-click', project: TenderProject): void
  (e: 'view', project: TenderProject): void
  (e: 'edit', project: TenderProject): void
  (e: 'delete', project: TenderProject): void
}

withDefaults(defineProps<Props>(), {
  showActions: true
})

const emit = defineEmits<Emits>()

const handleRowClick = (row: TenderProject) => {
  emit('row-click', row)
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
    year: 'numeric',
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
.project-list {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.04);
}

.project-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  font-size: 18px;
  color: #409eff;
  flex-shrink: 0;
}

.project-name {
  font-weight: 500;
  color: #222;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.filename {
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-progress {
  width: 80px;
}

.file-size {
  color: #666;
  font-size: 13px;
}

.upload-time {
  color: #666;
  font-size: 13px;
}

.action-buttons {
  display: flex;
  justify-content: center;
}

/* 表格行悬停效果 */
:deep(.el-table__row:hover) {
  cursor: pointer;
}

:deep(.el-table__row:hover .action-buttons) {
  opacity: 1;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .project-list {
    overflow-x: auto;
  }
  
  :deep(.el-table) {
    min-width: 600px;
  }
}
</style>