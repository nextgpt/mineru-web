<template>
  <div class="export-step">
    <div class="step-header">
      <h2 class="step-title">文档导出</h2>
      <p class="step-description">生成最终的标书文档</p>
    </div>

    <div class="step-body">
      <!-- 导出中 -->
      <div v-if="project?.status === 'exporting'" class="exporting-state">
        <div class="loading-container">
          <el-icon class="loading-icon" size="48"><Loading /></el-icon>
          <h3>正在导出文档...</h3>
          <p>请稍候，系统正在生成最终的标书文档</p>
        </div>
      </div>

      <!-- 导出完成 -->
      <div v-else-if="project?.status === 'completed'" class="export-completed">
        <div class="success-container">
          <el-result icon="success" title="标书生成完成" sub-title="您的标书文档已成功生成">
            <template #extra>
              <div class="export-actions">
                <el-button type="primary" size="large" @click="downloadDocument">
                  <el-icon><Download /></el-icon> 下载标书
                </el-button>
                <el-button size="large" @click="previewDocument" plain>
                  <el-icon><View /></el-icon> 预览文档
                </el-button>
              </div>
            </template>
          </el-result>
        </div>

        <!-- 导出历史 -->
        <div class="export-history" v-if="exportHistory.length > 0">
          <h3>导出历史</h3>
          <div class="history-list">
            <div v-for="doc in exportHistory" :key="doc.id" class="history-item">
              <div class="doc-info">
                <div class="doc-name">{{ doc.filename }}</div>
                <div class="doc-meta">
                  <span>{{ formatFileSize(doc.file_size) }}</span>
                  <span class="divider">•</span>
                  <span>{{ formatTime(doc.created_at) }}</span>
                </div>
              </div>
              <div class="doc-actions">
                <el-button size="small" @click="downloadHistoryDocument(doc.id)">
                  下载
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 准备导出 -->
      <div v-else class="export-ready">
        <div class="export-options">
          <h3>选择导出格式</h3>
          <div class="format-options">
            <div 
              v-for="format in exportFormats" 
              :key="format.value"
              class="format-option"
              :class="{ active: selectedFormat === format.value }"
              @click="selectedFormat = format.value"
            >
              <div class="format-icon">
                <el-icon size="32"><component :is="format.icon" /></el-icon>
              </div>
              <div class="format-info">
                <div class="format-name">{{ format.name }}</div>
                <div class="format-desc">{{ format.description }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="export-settings">
          <h3>导出设置</h3>
          <el-form :model="exportForm" label-width="120px">
            <el-form-item label="文档标题">
              <el-input v-model="exportForm.title" placeholder="请输入文档标题" />
            </el-form-item>
            <el-form-item label="公司名称">
              <el-input v-model="exportForm.company_name" placeholder="请输入公司名称" />
            </el-form-item>
            <el-form-item label="包含封面">
              <el-switch v-model="exportForm.include_cover" />
            </el-form-item>
            <el-form-item label="包含目录">
              <el-switch v-model="exportForm.include_toc" />
            </el-form-item>
          </el-form>
        </div>

        <div class="export-action">
          <el-button 
            type="primary" 
            size="large" 
            @click="startExport" 
            :loading="exporting"
          >
            <el-icon><Upload /></el-icon> 开始导出
          </el-button>
        </div>
      </div>
    </div>

    <!-- 步骤操作 -->
    <div class="step-actions">
      <el-button @click="$emit('prev')" size="large">
        <el-icon><ArrowLeft /></el-icon> 上一步
      </el-button>
      <el-button 
        v-if="project?.status === 'completed'" 
        type="success" 
        size="large"
        @click="createNewProject"
      >
        <el-icon><Plus /></el-icon> 新建项目
      </el-button>
    </div>
  </div>
</template><script
 setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { Loading, Download, View, Upload, ArrowLeft, Plus, Document, FileText } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
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

interface ExportDocument {
  id: string
  filename: string
  file_size: number
  created_at: string
}

const props = defineProps<{
  project: ProjectItem | null
}>()

const emit = defineEmits<{
  prev: []
  update: [project: ProjectItem]
}>()

const router = useRouter()

const selectedFormat = ref('pdf')
const exporting = ref(false)
const exportHistory = ref<ExportDocument[]>([])

const exportFormats = [
  {
    value: 'pdf',
    name: 'PDF文档',
    description: '适合打印和正式提交',
    icon: Document
  },
  {
    value: 'docx',
    name: 'Word文档',
    description: '可编辑的文档格式',
    icon: FileText
  }
]

const exportForm = reactive({
  title: '',
  company_name: '',
  include_cover: true,
  include_toc: true
})

const formatTime = (dateStr: string) => {
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

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const fetchExportHistory = async () => {
  if (!props.project) return
  
  try {
    const res = await axios.get(`/api/tender/projects/${props.project.id}/documents`, {
      headers: { 'X-User-Id': getUserId() }
    })
    exportHistory.value = res.data.documents || []
  } catch (e: any) {
    if (e.response?.status !== 404) {
      ElMessage.error('获取导出历史失败')
    }
  }
}

const startExport = async () => {
  if (!props.project) return
  
  exporting.value = true
  try {
    await axios.post(`/api/tender/projects/${props.project.id}/export`, {
      format: selectedFormat.value,
      options: {
        title: exportForm.title || props.project.project_name,
        company_name: exportForm.company_name,
        include_cover: exportForm.include_cover,
        include_toc: exportForm.include_toc
      }
    }, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    ElMessage.success('导出任务已启动')
    
    // 更新项目状态
    emit('update', { ...props.project, status: 'exporting' })
    
    // 开始轮询检查状态
    pollExportStatus()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '启动导出失败')
  } finally {
    exporting.value = false
  }
}

const pollExportStatus = () => {
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
      
      if (res.data.status === 'completed') {
        clearInterval(timer)
        await fetchExportHistory()
      } else if (res.data.status === 'failed') {
        clearInterval(timer)
      }
    } catch (e) {
      clearInterval(timer)
    }
  }, 3000)
}

const downloadDocument = async () => {
  if (!props.project || exportHistory.value.length === 0) return
  
  try {
    const latestDoc = exportHistory.value[0] // 最新的文档
    const res = await axios.get(`/api/tender/documents/${latestDoc.id}/download`, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    // 打开下载链接
    window.open(res.data.download_url, '_blank')
  } catch (e: any) {
    ElMessage.error('下载失败')
  }
}

const downloadHistoryDocument = async (documentId: string) => {
  try {
    const res = await axios.get(`/api/tender/documents/${documentId}/download`, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    // 打开下载链接
    window.open(res.data.download_url, '_blank')
  } catch (e: any) {
    ElMessage.error('下载失败')
  }
}

const previewDocument = async () => {
  if (!props.project || exportHistory.value.length === 0) return
  
  try {
    const latestDoc = exportHistory.value[0] // 最新的文档
    const res = await axios.get(`/api/tender/documents/${latestDoc.id}/preview`, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    // 在新窗口中打开预览
    window.open(res.data.preview_url, '_blank')
  } catch (e: any) {
    ElMessage.error('预览失败')
  }
}

const createNewProject = () => {
  router.push('/projects')
}

// 监听项目变化
watch(() => props.project, (newProject) => {
  if (newProject) {
    // 初始化表单
    exportForm.title = newProject.project_name
    
    if (newProject.status === 'completed') {
      fetchExportHistory()
    }
  }
}, { immediate: true })

onMounted(() => {
  if (props.project?.status === 'exporting') {
    pollExportStatus()
  } else if (props.project?.status === 'completed') {
    fetchExportHistory()
  }
})
</script>

<style scoped>
.export-step {
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

.exporting-state {
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

.export-completed {
  max-width: 800px;
  margin: 0 auto;
}

.success-container {
  margin-bottom: 32px;
}

.export-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.export-history {
  background: #f9fafb;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
}

.export-history h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 16px 0;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.doc-info {
  flex: 1;
}

.doc-name {
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
}

.doc-meta {
  font-size: 0.875rem;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 8px;
}

.divider {
  color: #d1d5db;
}

.export-ready {
  max-width: 800px;
  margin: 0 auto;
}

.export-ready h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 16px 0;
}

.export-options {
  margin-bottom: 32px;
}

.format-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.format-option {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.format-option:hover {
  border-color: #409eff;
  background: #f0f4ff;
}

.format-option.active {
  border-color: #409eff;
  background: #f0f4ff;
}

.format-icon {
  color: #409eff;
}

.format-info {
  flex: 1;
}

.format-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.format-desc {
  font-size: 0.875rem;
  color: #6b7280;
}

.export-settings {
  background: #f9fafb;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
  margin-bottom: 32px;
}

.export-action {
  text-align: center;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-top: 1px solid #e5e7eb;
}

:deep(.el-result) {
  padding: 32px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}
</style>