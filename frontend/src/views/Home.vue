<template>
  <div class="home-container">
    <div class="home-content">
      <!-- 标题区域 -->
      <div class="title-section">
        <h1 class="main-title">
          通过招标文件<span class="highlight">智能生成标书</span>
        </h1>
        <p class="subtitle">
          上传招标文档，AI智能解析，快速生成专业标书内容，提升中标率
        </p>
        <p class="description">
          支持 PDF、Word 等多种格式，智能提取关键信息
        </p>
      </div>

      <!-- 功能特色 -->
      <div class="features-row">
        <div class="feature-item">
          <div class="feature-icon pdf-icon">PDF</div>
          <span class="feature-text">PDF文档解析</span>
        </div>
        <div class="feature-item">
          <div class="feature-icon word-icon">W</div>
          <span class="feature-text">Word文档支持</span>
        </div>
        <div class="feature-item">
          <div class="feature-icon ai-icon">AI</div>
          <span class="feature-text">智能内容生成</span>
        </div>
      </div>

      <!-- 文件上传区域 -->
      <div class="upload-section">
        <el-upload
          ref="uploadRef"
          class="upload-dragger"
          drag
          :auto-upload="false"
          :show-file-list="false"
          :accept="acceptedFileTypes"
          :before-upload="handleBeforeUpload"
          :on-change="handleFileChange"
          :disabled="isUploading"
        >
          <div class="upload-content">
            <el-icon class="upload-icon" :class="{ 'is-loading': isUploading }">
              <component :is="isUploading ? Loading : UploadFilled" />
            </el-icon>
            <div class="upload-text">
              <p class="upload-title">{{ uploadTitle }}</p>
              <p class="upload-hint">{{ uploadHint }}</p>
            </div>
          </div>
        </el-upload>
        
        <div class="upload-actions" v-if="selectedFile && !isUploading">
          <el-button type="primary" size="large" @click="handleStartUpload" class="action-btn">
            开始上传解析
          </el-button>
        </div>
      </div>

      <!-- 快速入口 -->
      <div class="quick-actions">
        <el-button class="quick-btn" @click="$router.push('/projects')">
          查看项目管理
        </el-button>
      </div>
    </div>

    <!-- 状态弹窗 -->
    <el-dialog
      v-model="showStatusModal"
      :title="statusModal.title"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="statusModal.closable"
      center
      class="status-modal"
    >
      <div class="status-content">
        <div class="status-icon">
          <el-icon 
            :class="[
              'status-icon-inner',
              statusModal.type === 'loading' ? 'is-loading' : '',
              statusModal.type === 'success' ? 'success' : '',
              statusModal.type === 'error' ? 'error' : ''
            ]"
          >
            <component :is="getStatusIcon()" />
          </el-icon>
        </div>
        
        <div class="status-message">
          <p class="status-main-text">{{ statusModal.message }}</p>
          <p v-if="statusModal.detail" class="status-detail-text">{{ statusModal.detail }}</p>
        </div>
        
        <div v-if="statusModal.type === 'loading'" class="status-progress">
          <el-progress 
            :percentage="statusModal.progress" 
            :stroke-width="8"
            :show-text="false"
          />
          <div class="progress-text">{{ statusModal.progress }}%</div>
        </div>
      </div>
      
      <template #footer v-if="statusModal.closable">
        <el-button @click="handleCloseModal">关闭</el-button>
        <el-button 
          v-if="statusModal.type === 'success' && uploadResult" 
          type="primary" 
          @click="handleViewProject"
        >
          查看项目
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { 
  UploadFilled, 
  Loading, 
  SuccessFilled,
  CircleCloseFilled
} from '@element-plus/icons-vue'
import { ElMessage, type UploadFile, type UploadInstance } from 'element-plus'
import { useStatsStore } from '../store/stats'
import { useProjectStore } from '../store/project'
import { useRouter } from 'vue-router'
import { ragflowService, OperationStatus } from '@/api/ragflow'
import type { TenderProject } from '@/types/tender'

const router = useRouter()
const statsStore = useStatsStore()
const projectStore = useProjectStore()

// 上传相关状态
const uploadRef = ref<UploadInstance>()
const selectedFile = ref<File | null>(null)
const isUploading = ref(false)

// 状态弹窗
const showStatusModal = ref(false)
const statusModal = ref({
  title: '',
  message: '',
  detail: '',
  type: 'loading' as 'loading' | 'success' | 'error',
  progress: 0,
  closable: false
})

// 上传结果
const uploadResult = ref<{ documentId: string; fileName: string } | null>(null)

// 支持的文件类型
const acceptedFileTypes = '.pdf,.doc,.docx'

// 动态文本
const uploadTitle = computed(() => {
  if (isUploading.value) return '正在处理文件...'
  if (selectedFile.value) return `已选择: ${selectedFile.value.name}`
  return '拖拽文件到此处或点击上传'
})

const uploadHint = computed(() => {
  if (isUploading.value) return '请耐心等待，正在上传和解析文档'
  if (selectedFile.value) return '点击"开始上传"按钮开始处理'
  return '支持 PDF、DOC、DOCX 格式，最大 200MB'
})

// 获取状态图标
const getStatusIcon = () => {
  switch (statusModal.value.type) {
    case 'loading': return Loading
    case 'success': return SuccessFilled
    case 'error': return CircleCloseFilled
    default: return Loading
  }
}

// 文件选择前验证
const handleBeforeUpload = (file: File) => {
  // 检查文件类型
  const isValidType = /\.(pdf|doc|docx)$/i.test(file.name)
  if (!isValidType) {
    ElMessage.error('只支持 PDF、DOC、DOCX 格式的文件')
    return false
  }

  // 检查文件大小
  const isValidSize = file.size <= 200 * 1024 * 1024 // 200MB
  if (!isValidSize) {
    ElMessage.error('文件大小不能超过 200MB')
    return false
  }

  return false // 阻止自动上传
}

// 文件选择变化
const handleFileChange = (file: UploadFile) => {
  if (file.raw) {
    selectedFile.value = file.raw
  }
}

// 开始上传
const handleStartUpload = async () => {
  if (!selectedFile.value) return

  isUploading.value = true
  
  // 显示上传状态弹窗
  showStatusModal.value = true
  statusModal.value = {
    title: '文件上传',
    message: '正在上传文件...',
    detail: selectedFile.value.name,
    type: 'loading',
    progress: 0,
    closable: false
  }

  try {
    // 创建项目记录
    const project: TenderProject = {
      id: Date.now().toString(),
      name: selectedFile.value.name.replace(/\.[^/.]+$/, ''),
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      uploadTime: new Date().toISOString(),
      status: 'uploading',
      lastModified: new Date().toISOString()
    }

    projectStore.addProject(project)

    // 调用RAGFlow上传和解析
    const result = await ragflowService.uploadAndParseDocument(
      selectedFile.value,
      // 上传进度回调
      (progress, message) => {
        statusModal.value.progress = progress
        statusModal.value.message = message
        statusModal.value.detail = selectedFile.value!.name
      },
      // 解析进度回调
      (progress, message, stage) => {
        statusModal.value.progress = progress
        statusModal.value.message = message
        statusModal.value.detail = stage ? `当前阶段: ${stage}` : ''
      }
    )

    if (result.status === OperationStatus.SUCCESS) {
      // 上传成功
      uploadResult.value = result.data!
      
      // 更新项目状态
      projectStore.updateProject(project.id, {
        status: 'ready',
        documentId: result.data!.documentId,
        datasetId: ragflowService.getFixedDatasetId(),
        lastModified: new Date().toISOString()
      })

      // 显示成功状态
      statusModal.value = {
        title: '上传成功',
        message: '文件上传和解析完成！',
        detail: '您可以开始生成标书大纲了',
        type: 'success',
        progress: 100,
        closable: true
      }

      // 清除选中文件
      selectedFile.value = null
      uploadRef.value?.clearFiles()

    } else {
      // 上传失败
      projectStore.updateProject(project.id, {
        status: 'error',
        lastModified: new Date().toISOString()
      })

      statusModal.value = {
        title: '上传失败',
        message: result.message,
        detail: result.error || '请检查文件格式或网络连接',
        type: 'error',
        progress: 0,
        closable: true
      }
    }

  } catch (error) {
    console.error('Upload error:', error)
    
    statusModal.value = {
      title: '上传失败',
      message: '文件上传过程中发生错误',
      detail: (error as Error).message || '未知错误',
      type: 'error',
      progress: 0,
      closable: true
    }
  } finally {
    isUploading.value = false
  }
}



// 关闭弹窗
const handleCloseModal = () => {
  showStatusModal.value = false
  uploadResult.value = null
}

// 查看项目
const handleViewProject = () => {
  showStatusModal.value = false
  router.push('/projects')
}

onMounted(() => {
  statsStore.fetchStats()
})
</script>

<style scoped>
.home-container {
  position: relative;
}

.home-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 140px);
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 47px 40px 47px; /* 左右各47px，与项目页面保持一致 */
}

/* 标题区域 */
.title-section {
  text-align: center;
  margin-bottom: 48px;
}

.main-title {
  font-size: 36px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 16px 0;
  line-height: 1.2;
}

.highlight {
  color: #ff6b6b;
}

.subtitle {
  font-size: 18px;
  color: #606266;
  margin: 0 0 8px 0;
  line-height: 1.5;
}

.description {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

/* 功能特色 */
.features-row {
  display: flex;
  gap: 32px;
  margin-bottom: 48px;
  justify-content: center;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.pdf-icon {
  background: #ff4757;
}

.word-icon {
  background: #2e86de;
}

.ai-icon {
  background: #5f27cd;
}

.feature-text {
  font-size: 14px;
  color: #606266;
  text-align: center;
}

/* 文件上传区域 */
.upload-section {
  width: 100%;
  max-width: 600px;
  margin-bottom: 32px;
}

.upload-dragger {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 180px;
  border: 2px dashed #d9d9d9;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.el-upload-dragger:hover) {
  border-color: #409eff;
  background: rgba(240, 244, 255, 0.8);
}

:deep(.el-upload-dragger.is-dragover) {
  border-color: #409eff;
  background: rgba(230, 240, 255, 0.8);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.upload-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 16px;
  transition: all 0.3s;
}

.upload-icon.is-loading {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.upload-text {
  color: #606266;
}

.upload-title {
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 8px 0;
  color: #303133;
}

.upload-hint {
  font-size: 14px;
  margin: 0;
  color: #909399;
}

.upload-actions {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.action-btn {
  padding: 12px 32px;
  font-size: 16px;
  border-radius: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: #fff;
  font-weight: 500;
}

.action-btn:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

/* 快速入口 */
.quick-actions {
  display: flex;
  justify-content: center;
}

.quick-btn {
  padding: 8px 24px;
  font-size: 14px;
  color: #409eff;
  background: transparent;
  border: 1px solid #409eff;
  border-radius: 20px;
  transition: all 0.3s;
}

.quick-btn:hover {
  background: #409eff;
  color: #fff;
}

/* 状态弹窗样式 */
:deep(.status-modal) {
  .el-dialog {
    border-radius: 16px;
    overflow: hidden;
    backdrop-filter: blur(10px);
  }
  
  .el-dialog__header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px 24px;
    border-bottom: none;
  }
  
  .el-dialog__title {
    font-size: 18px;
    font-weight: 600;
    color: #fff;
  }
  
  .el-dialog__body {
    padding: 32px 24px;
    background: #fff;
  }
  
  .el-dialog__footer {
    padding: 16px 24px;
    border-top: 1px solid #e4e7ed;
    background: #f8f9fa;
  }
}

.status-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.status-icon {
  margin-bottom: 20px;
}

.status-icon-inner {
  font-size: 64px;
  transition: all 0.3s;
}

.status-icon-inner.is-loading {
  color: #409eff;
  animation: rotate 2s linear infinite;
}

.status-icon-inner.success {
  color: #67c23a;
}

.status-icon-inner.error {
  color: #f56c6c;
}

.status-message {
  margin-bottom: 20px;
}

.status-main-text {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 8px 0;
}

.status-detail-text {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.status-progress {
  width: 100%;
  max-width: 300px;
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

/* 弹窗背景遮罩 */
:deep(.el-overlay) {
  background-color: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .home-content {
    padding: 20px 16px;
  }
  
  .main-title {
    font-size: 28px;
  }
  
  .subtitle {
    font-size: 16px;
  }
  
  .features-row {
    gap: 20px;
    margin-bottom: 32px;
  }
  
  .feature-icon {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }
  
  .feature-text {
    font-size: 12px;
  }
  
  :deep(.el-upload-dragger) {
    height: 140px;
  }
  
  .upload-icon {
    font-size: 40px;
  }
  
  :deep(.status-modal .el-dialog) {
    width: 90% !important;
    margin: 0 5%;
  }
}

@media (max-width: 480px) {
  .features-row {
    flex-direction: column;
    gap: 16px;
  }
  
  .feature-item {
    flex-direction: row;
    gap: 12px;
  }
  
  .main-title {
    font-size: 24px;
  }
  
  .subtitle {
    font-size: 14px;
  }
}
</style> 