<template>
  <div class="home-page">
    <!-- 顶部导航 -->
    <div class="top-nav">
      <div class="nav-left">
        <div class="logo">
          <el-icon size="24" color="#6366f1"><Document /></el-icon>
          <span class="logo-text">创建投标方案</span>
        </div>
      </div>
      <div class="nav-right">
        <el-button type="text" @click="goToProjects">
          <el-icon><List /></el-icon>
          项目列表
        </el-button>
        <el-button type="text" @click="goToSettings">
          <el-icon><Setting /></el-icon>
          设置
        </el-button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 中心内容 -->
      <div class="center-content">
        <div class="title-section">
          <h1 class="main-title">
            通过招标文件<span class="highlight">智能生成标书</span>
          </h1>
          <p class="subtitle">
            上传您的招标文件，AI将为您分析需求并生成专业的投标方案，生成高质量文档，完成全流程投标
          </p>
        </div>

        <!-- 上传区域 -->
        <div class="upload-section">
          <div class="upload-container">
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :limit="1"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              :before-upload="beforeUpload"
              drag
              accept=".pdf,.doc,.docx,.xlsx,.xls"
              class="upload-dragger"
            >
              <div class="upload-content">
                <!-- 文件类型图标 -->
                <div class="file-icons">
                  <div class="file-icon pdf-icon">
                    <el-icon size="24"><Document /></el-icon>
                  </div>
                  <div class="file-icon doc-icon">
                    <el-icon size="24"><Document /></el-icon>
                  </div>
                  <div class="file-icon excel-icon">
                    <el-icon size="24"><Document /></el-icon>
                  </div>
                </div>
                
                <div class="upload-text">
                  <p class="upload-main-text">
                    支持(.doc/.docx/.pdf/.xlsx/.xls)格式文件，<span class="highlight-text">拖拽上传或点击文件</span>
                  </p>
                  <p class="upload-sub-text">可拖拽上传或点击文件（文件大小限制）</p>
                </div>
                
                <el-button type="primary" class="upload-button">
                  选择上传招标文件
                </el-button>
              </div>
            </el-upload>
          </div>
        </div>

        <!-- 进度显示 -->
        <div v-if="uploadProgress > 0" class="progress-section">
          <div class="progress-container">
            <el-progress 
              :percentage="uploadProgress" 
              :status="uploadStatus"
              :stroke-width="8"
              class="upload-progress"
            />
            <p class="progress-text">{{ progressText }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建项目对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建新项目"
      width="500px"
      :before-close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="projectForm"
        :rules="formRules"
        label-width="80px"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input
            v-model="projectForm.name"
            placeholder="请输入项目名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="projectForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入项目描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false" :disabled="creating">取消</el-button>
          <el-button type="primary" @click="handleCreateProject" :loading="creating">
            创建项目
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type UploadFile } from 'element-plus'
import { Document, List, Setting } from '@element-plus/icons-vue'
import { projectsApi } from '@/api/projects'

const router = useRouter()

// 响应式数据
const uploadRef = ref()
const formRef = ref<FormInstance>()
const selectedFile = ref<File | null>(null)
const uploadProgress = ref(0)
const uploadStatus = ref<'success' | 'exception' | undefined>()
const progressText = ref('')
const showCreateDialog = ref(false)
const creating = ref(false)

const projectForm = ref({
  name: '',
  description: ''
})

const formRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 100, message: '项目名称长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

// 方法
const goToProjects = () => {
  router.push('/projects')
}

const goToSettings = () => {
  router.push('/settings')
}

const handleFileChange = (file: UploadFile) => {
  if (file.raw) {
    selectedFile.value = file.raw
    // 自动填充项目名称
    const fileName = file.name.replace(/\.[^/.]+$/, '')
    projectForm.value.name = fileName
    showCreateDialog.value = true
  }
}

const handleFileRemove = () => {
  selectedFile.value = null
  uploadProgress.value = 0
  uploadStatus.value = undefined
}

const beforeUpload = (file: File) => {
  const validTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ]
  
  const isValidType = validTypes.includes(file.type)
  const isValidSize = file.size / 1024 / 1024 < 100

  if (!isValidType) {
    ElMessage.error('只支持 PDF、Word、Excel 格式的文件')
    return false
  }
  if (!isValidSize) {
    ElMessage.error('文件大小不能超过 100MB')
    return false
  }
  return true
}

const handleCreateProject = async () => {
  if (!formRef.value || !selectedFile.value) return

  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    creating.value = true
    progressText.value = '正在创建项目...'

    // 创建项目
    const project = await projectsApi.createProject({
      name: projectForm.value.name,
      description: projectForm.value.description
    })

    progressText.value = '正在上传文件...'
    uploadProgress.value = 10

    // 上传文件
    await projectsApi.uploadTenderFile(
      project.id,
      selectedFile.value,
      (progress) => {
        uploadProgress.value = Math.max(10, progress)
        if (progress === 100) {
          progressText.value = '文件上传完成，正在处理...'
        }
      }
    )

    uploadStatus.value = 'success'
    progressText.value = '项目创建成功！'
    
    ElMessage.success('项目创建成功，正在跳转...')
    
    // 跳转到项目详情页
    setTimeout(() => {
      router.push(`/projects/${project.id}`)
    }, 1500)

  } catch (error: any) {
    console.error('创建项目失败:', error)
    uploadStatus.value = 'exception'
    progressText.value = '创建失败，请重试'
    ElMessage.error(error.response?.data?.detail || '创建项目失败')
  } finally {
    creating.value = false
  }
}

const handleDialogClose = (done: () => void) => {
  if (creating.value) {
    ElMessage.warning('正在创建项目，请稍候...')
    return
  }
  
  // 重置表单
  projectForm.value = { name: '', description: '' }
  selectedFile.value = null
  uploadProgress.value = 0
  uploadStatus.value = undefined
  progressText.value = ''
  uploadRef.value?.clearFiles()
  done()
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #f7f8fa;
  position: relative;
  overflow: hidden;
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.nav-left .logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.nav-right {
  display: flex;
  gap: 16px;
}

.nav-right .el-button {
  color: #6b7280;
  border: 1px solid #e5e7eb;
  background: #fff;
}

.nav-right .el-button:hover {
  background: #f9fafb;
  color: #374151;
}

.main-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 80px);
  padding: 40px 20px;
  position: relative;
}



.center-content {
  max-width: 800px;
  width: 100%;
  text-align: center;
  z-index: 1;
}

.title-section {
  margin-bottom: 60px;
}

.main-title {
  font-size: 48px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 20px 0;
  line-height: 1.2;
}

.main-title .highlight {
  background: linear-gradient(45deg, #ff6b6b, #feca57);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 18px;
  color: #6b7280;
  line-height: 1.6;
  margin: 0;
  max-width: 600px;
  margin: 0 auto;
}

.upload-section {
  margin-bottom: 40px;
}

.upload-container {
  background: #fff;
  border-radius: 24px;
  padding: 40px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
  border: 1px solid #e5e7eb;
}

.upload-dragger {
  width: 100%;
}

.upload-dragger :deep(.el-upload-dragger) {
  border: 2px dashed #d1d5db;
  border-radius: 16px;
  background: transparent;
  padding: 40px 20px;
  transition: all 0.3s ease;
}

.upload-dragger :deep(.el-upload-dragger:hover) {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.05);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.file-icons {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
}

.file-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
}

.pdf-icon {
  background: linear-gradient(45deg, #ff6b6b, #ee5a52);
}

.doc-icon {
  background: linear-gradient(45deg, #4dabf7, #339af0);
}

.excel-icon {
  background: linear-gradient(45deg, #51cf66, #40c057);
}

.upload-text {
  text-align: center;
}

.upload-main-text {
  font-size: 16px;
  color: #374151;
  margin: 0 0 8px 0;
  font-weight: 500;
}

.highlight-text {
  color: #409eff;
  font-weight: 600;
}

.upload-sub-text {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.upload-button {
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: #409eff;
  border: none;
  color: white;
  transition: all 0.3s ease;
}

.upload-button:hover {
  background: #337ecc;
}

.progress-section {
  margin-top: 40px;
}

.progress-container {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}

.upload-progress {
  margin-bottom: 12px;
}

.upload-progress :deep(.el-progress-bar__outer) {
  border-radius: 8px;
  background: #f0f2f5;
}

.upload-progress :deep(.el-progress-bar__inner) {
  border-radius: 8px;
  background: #409eff;
}

.progress-text {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  text-align: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .top-nav {
    padding: 16px 20px;
  }
  
  .main-title {
    font-size: 32px;
  }
  
  .subtitle {
    font-size: 16px;
  }
  
  .upload-container {
    padding: 24px;
    margin: 0 16px;
  }
  
  .file-icons {
    gap: 12px;
  }
  
  .file-icon {
    width: 40px;
    height: 40px;
  }
  
  .upload-main-text {
    font-size: 14px;
  }
  
  .upload-button {
    padding: 10px 24px;
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: 28px;
  }
  
  .upload-container {
    padding: 20px;
  }
  
  .upload-content {
    gap: 16px;
  }
}
</style>