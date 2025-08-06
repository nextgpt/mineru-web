<template>
  <div class="upload-root">
    <div class="upload-card">
      <div class="upload-header">
        <span class="upload-title">点击或拖拽上传招标文档</span>
      </div>
      <el-upload
        ref="uploadRef"
        class="upload-area"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :before-upload="beforeUpload"
        accept=".pdf,.doc,.docx"
        :limit="1"
        :disabled="uploading"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽招标文档到此处，或 <span class="upload-link">点击上传</span>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持的文件类型：PDF、Word文档（.doc, .docx）
            <br>
            单个文档不超过 <b>200MB</b>，系统将自动解析文档内容
          </div>
        </template>
      </el-upload>
      
      <!-- 上传进度显示 -->
      <div class="upload-progress" v-if="uploading">
        <div class="progress-header">
          <span class="progress-title">{{ currentStep }}</span>
          <el-tag :type="getProgressType(uploadStatus)" size="small">
            {{ getProgressText(uploadStatus) }}
          </el-tag>
        </div>
        <el-progress 
          :percentage="uploadProgress" 
          :status="uploadStatus === 'error' ? 'exception' : uploadStatus === 'success' ? 'success' : undefined"
          :stroke-width="8"
        />
        <div class="progress-details" v-if="progressDetails">
          {{ progressDetails }}
        </div>
      </div>

      <!-- 文件列表 -->
      <div class="upload-list" v-if="fileList.length > 0 && !uploading">
        <div class="upload-list-header">
          <span>待上传文件</span>
          <el-button 
            type="primary" 
            @click="handleUpload" 
            :disabled="fileList.length === 0" 
            size="small"
          >
            <el-icon><upload-filled /></el-icon>
            开始上传
          </el-button>
        </div>
        <el-table :data="fileList" border stripe>
          <el-table-column prop="name" label="文件名" />
          <el-table-column prop="size" label="大小" width="120">
            <template #default="{ row }">{{ formatFileSize(row.size) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button 
                type="danger" 
                link 
                @click="handleFileRemove(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <el-empty 
        v-else-if="!uploading" 
        description="暂无待上传文件，请选择招标文档开始智能标书生成！" 
        :image-size="100" 
        class="upload-empty" 
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { UploadInstance } from 'element-plus'
import { formatFileSize } from '@/utils/format'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/store/project'
import { ragflowService } from '@/api/ragflow'
import { NotificationService } from '@/utils/notificationService'
import { ErrorHandler } from '@/utils/errorHandler'
import type { TenderProject } from '@/types/tender'

interface UploadFile {
  name: string
  size: number
  raw: File
}

const router = useRouter()
const projectStore = useProjectStore()

const fileList = ref<UploadFile[]>([])
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref<'normal' | 'success' | 'error'>('normal')
const currentStep = ref('')
const progressDetails = ref('')

const uploadRef = ref<UploadInstance>()

const beforeUpload = (file: File) => {
  const validation = ErrorHandler.validateFile(file)
  if (!validation.valid) {
    ElMessage.error(validation.error!)
    return false
  }
  return true
}

const handleFileChange = (file: any) => {
  // 在文件变化时也进行类型检查
  if (!beforeUpload(file.raw)) {
    return
  }
  
  // 清空之前的文件（只允许上传一个文件）
  fileList.value = [{
    name: file.name,
    size: file.size,
    raw: file.raw
  }]
}

const handleFileRemove = (_file: UploadFile) => {
  fileList.value = []
  uploadRef.value?.clearFiles()
}

const getProgressType = (status: string) => {
  const map: Record<string, string> = {
    normal: 'info',
    success: 'success',
    error: 'danger'
  }
  return map[status] || 'info'
}

const getProgressText = (status: string) => {
  const map: Record<string, string> = {
    normal: '处理中',
    success: '完成',
    error: '失败'
  }
  return map[status] || '处理中'
}

const generateProjectId = (): string => {
  return `project_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

const handleUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择要上传的文件')
    return
  }

  const file = fileList.value[0]
  uploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = 'normal'

  try {
    // 创建项目记录
    const projectId = generateProjectId()
    const project: TenderProject = {
      id: projectId,
      name: file.name.replace(/\.[^/.]+$/, ''), // 移除文件扩展名
      fileName: file.name,
      fileSize: file.size,
      uploadTime: new Date().toISOString(),
      status: 'uploading',
      lastModified: new Date().toISOString()
    }

    // 添加到项目存储
    projectStore.addProject(project)

    // 步骤1: 创建RAGFLOW数据集
    currentStep.value = '创建数据集...'
    progressDetails.value = '正在为您的招标文档创建专用数据集'
    uploadProgress.value = 20

    const dataset = await ragflowService.createDataset(project.name)
    console.log('[Upload] Dataset created:', dataset)

    // 更新项目信息
    projectStore.updateProject(projectId, { 
      datasetId: dataset.id,
      status: 'uploading'
    })

    // 步骤2: 上传文档到RAGFLOW
    currentStep.value = '上传文档...'
    progressDetails.value = '正在将文档上传到知识库'
    uploadProgress.value = 50

    const document = await ragflowService.uploadDocument(dataset.id, file.raw)
    console.log('[Upload] Document uploaded:', document)

    // 更新项目信息
    projectStore.updateProject(projectId, { 
      documentId: document.id,
      status: 'parsing'
    })

    // 步骤3: 开始解析文档
    currentStep.value = '解析文档...'
    progressDetails.value = '正在解析文档内容，提取关键信息'
    uploadProgress.value = 70

    await ragflowService.parseDocument(dataset.id, [document.id])
    console.log('[Upload] Document parsing started')

    // 步骤4: 等待解析完成
    await ragflowService.waitForDocumentParsing(
      dataset.id, 
      document.id,
      (progress, details) => {
        uploadProgress.value = 70 + (progress * 0.3) // 70-100%
        if (details) {
          progressDetails.value = details
        }
      },
      (_stage, stageName) => {
        currentStep.value = stageName
      }
    )

    // 完成
    currentStep.value = '上传完成'
    progressDetails.value = '文档已成功上传并解析完成'
    uploadProgress.value = 100
    uploadStatus.value = 'success'

    // 更新项目状态为就绪
    projectStore.updateProject(projectId, { 
      status: 'ready',
      lastModified: new Date().toISOString()
    })

    // 显示成功通知
    NotificationService.showUploadSuccess(
      project.name,
      () => router.push(`/preview/${projectId}`)
    )
    
    // 清空文件列表
    fileList.value = []
    uploadRef.value?.clearFiles()

    // 延迟跳转到文档预览页面
    setTimeout(() => {
      router.push(`/preview/${projectId}`)
    }, 1500)

  } catch (error) {
    console.error('[Upload] Upload failed:', error)
    
    uploadStatus.value = 'error'
    currentStep.value = '上传失败'
    
    // 检查是否是RAGFLOW特定错误
    const errorMessage = (error as Error).message || ''
    if (errorMessage.includes('float()') || errorMessage.includes('NoneType') || errorMessage.includes('embedding')) {
      // 显示RAGFLOW特定错误通知
      NotificationService.showRagflowParsingError(
        file.name,
        errorMessage,
        () => handleUpload()
      )
      progressDetails.value = 'RAGFLOW解析配置错误，请重试'
    } else {
      // 使用通用错误处理器
      const errorInfo = ErrorHandler.handleUploadError(
        error, 
        file.name,
        () => handleUpload()
      )
      progressDetails.value = errorInfo.userMessage
    }
    
    // 如果项目已创建，更新状态为错误
    if (fileList.value.length > 0) {
      const projectName = fileList.value[0].name.replace(/\.[^/.]+$/, '')
      const existingProject = projectStore.projects.find(p => p.name === projectName)
      if (existingProject) {
        projectStore.updateProject(existingProject.id, { 
          status: 'error',
          lastModified: new Date().toISOString()
        })
      }
    }
  } finally {
    // 延迟重置上传状态，让用户看到结果
    setTimeout(() => {
      uploading.value = false
      uploadProgress.value = 0
      uploadStatus.value = 'normal'
      currentStep.value = ''
      progressDetails.value = ''
    }, 3000)
  }
}
</script>

<style scoped>

.upload-root {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 32px 0 0 0;
  box-sizing: border-box;
}

.upload-card {
  width: 100%;
  max-width: 80vw;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  padding: 24px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.upload-header {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 18px;
}

.upload-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: #222;
}

.upload-area {
  width: 100%;
  margin-bottom: 18px;
}

.upload-link {
  color: #409eff;
  font-weight: 500;
  cursor: pointer;
}

.upload-progress {
  width: 100%;
  margin: 24px 0;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-title {
  font-size: 1rem;
  font-weight: 500;
  color: #333;
}

.progress-details {
  margin-top: 8px;
  font-size: 0.9rem;
  color: #666;
  text-align: center;
}

.upload-list {
  width: 100%;
  margin-top: 18px;
  overflow-y: auto;
}

.upload-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.upload-empty {
  margin: 32px 0 0 0;
  height: auto;
  max-height: 10vh;
}

:deep(.el-upload-dragger) {
  width: 100%;
  border-radius: 12px;
  background: #f7f8fa;
  border: 1.5px dashed #b1b3b8;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

:deep(.el-upload__tip) {
  margin-top: 8px;
  color: #909399;
}

:deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.el-progress-bar__outer) {
  border-radius: 4px;
}

:deep(.el-progress-bar__inner) {
  border-radius: 4px;
}
</style> 