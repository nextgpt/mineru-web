<template>
  <div class="project-detail-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" class="back-button">
          <el-icon><Back /></el-icon>
          返回项目列表
        </el-button>
        <div class="project-info">
          <h1 class="project-title">{{ project?.name || '加载中...' }}</h1>
          <div class="project-meta">
            <el-tag v-if="project" :type="getStatusType(project.status)" size="small">
              {{ getStatusText(project.status) }}
            </el-tag>
            <span v-if="project" class="create-time">
              创建于 {{ formatDate(project.created_at) }}
            </span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <el-button v-if="!project?.original_file" type="primary" @click="showUploadDialog = true">
          <el-icon><Upload /></el-icon>
          上传招标文件
        </el-button>
        <el-dropdown @command="handleMenuCommand">
          <el-button>
            更多操作
            <el-icon class="el-icon--right"><Setting /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="edit">编辑项目</el-dropdown-item>
              <el-dropdown-item command="delete" divided>删除项目</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="page-content" v-loading="loading">
      <div v-if="project" class="content-container">
        <!-- 标签页导航 -->
        <el-tabs v-model="activeTab" class="project-tabs">
          <!-- 基本信息 -->
          <el-tab-pane label="基本信息" name="info">
            <div class="tab-content">
              <ProjectInfo :project="project" @refresh="loadProject" />
            </div>
          </el-tab-pane>

          <!-- 需求分析 -->
          <el-tab-pane label="需求分析" name="analysis" :disabled="!project.original_file">
            <div class="tab-content">
              <RequirementAnalysis :project-id="project.id" />
            </div>
          </el-tab-pane>

          <!-- 标书大纲 -->
          <el-tab-pane label="标书大纲" name="outline" :disabled="project.status === 'created' || project.status === 'parsing'">
            <div class="tab-content">
              <BidOutline :project-id="project.id" />
            </div>
          </el-tab-pane>

          <!-- 标书内容 -->
          <el-tab-pane label="标书内容" name="document" :disabled="project.status !== 'completed' && project.status !== 'outline_generated'">
            <div class="tab-content">
              <BidDocument :project-id="project.id" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 上传文件对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传招标文件"
      width="500px"
      :before-close="handleUploadDialogClose"
    >
      <div class="upload-content">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          :before-upload="beforeUpload"
          drag
          accept=".pdf,.doc,.docx"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 PDF、Word 格式，文件大小不超过 100MB
            </div>
          </template>
        </el-upload>
        
        <div v-if="uploadProgress > 0" class="upload-progress">
          <el-progress :percentage="uploadProgress" :status="uploadStatus" />
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showUploadDialog = false" :disabled="uploading">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleUpload" 
            :loading="uploading"
            :disabled="!selectedFile"
          >
            上传
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type UploadInstance, type UploadFile } from 'element-plus'
import { Back, Setting, Upload, UploadFilled } from '@element-plus/icons-vue'
import { projectsApi, type Project } from '@/api/projects'

// 导入子组件（这些组件将在后续任务中实现）
import ProjectInfo from '@/components/ProjectInfo.vue'
import RequirementAnalysis from '@/components/RequirementAnalysis.vue'
import BidOutline from '@/components/BidOutline.vue'
import BidDocument from '@/components/BidDocument.vue'

const route = useRoute()
const router = useRouter()

// 响应式数据
const project = ref<Project | null>(null)
const loading = ref(false)
const activeTab = ref('info')

// 上传相关
const showUploadDialog = ref(false)
const uploadRef = ref<UploadInstance>()
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref<'success' | 'exception' | undefined>()

// 计算属性
const projectId = computed(() => {
  const id = route.params.id
  return typeof id === 'string' ? parseInt(id) : 0
})

// 方法
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

// 返回项目列表
const goBack = () => {
  router.push('/projects')
}

// 加载项目详情
const loadProject = async () => {
  if (!projectId.value) {
    ElMessage.error('项目ID无效')
    goBack()
    return
  }

  try {
    loading.value = true
    project.value = await projectsApi.getProject(projectId.value)
  } catch (error) {
    console.error('加载项目详情失败:', error)
    ElMessage.error('加载项目详情失败')
    goBack()
  } finally {
    loading.value = false
  }
}

// 处理菜单命令
const handleMenuCommand = (command: string) => {
  switch (command) {
    case 'edit':
      handleEditProject()
      break
    case 'delete':
      handleDeleteProject()
      break
  }
}

// 编辑项目
const handleEditProject = () => {
  ElMessage.info('编辑功能开发中...')
}

// 删除项目
const handleDeleteProject = async () => {
  if (!project.value) return

  try {
    await ElMessageBox.confirm(
      `确定要删除项目"${project.value.name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await projectsApi.deleteProject(project.value.id)
    ElMessage.success('项目删除成功')
    goBack()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除项目失败:', error)
      ElMessage.error('删除项目失败')
    }
  }
}

// 文件上传相关方法
const handleFileChange = (file: UploadFile) => {
  if (file.raw) {
    selectedFile.value = file.raw
  }
}

const handleFileRemove = () => {
  selectedFile.value = null
}

const beforeUpload = (file: File) => {
  const isValidType = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)
  const isValidSize = file.size / 1024 / 1024 < 100

  if (!isValidType) {
    ElMessage.error('只支持 PDF、Word 格式的文件')
    return false
  }
  if (!isValidSize) {
    ElMessage.error('文件大小不能超过 100MB')
    return false
  }
  return true
}

const handleUpload = async () => {
  if (!selectedFile.value || !project.value) return

  try {
    uploading.value = true
    uploadProgress.value = 0
    uploadStatus.value = undefined

    await projectsApi.uploadTenderFile(
      project.value.id,
      selectedFile.value,
      (progress) => {
        uploadProgress.value = progress
      }
    )

    uploadStatus.value = 'success'
    ElMessage.success('文件上传成功')
    showUploadDialog.value = false
    
    // 重新加载项目信息
    await loadProject()
  } catch (error) {
    console.error('文件上传失败:', error)
    uploadStatus.value = 'exception'
    ElMessage.error('文件上传失败')
  } finally {
    uploading.value = false
  }
}

const handleUploadDialogClose = (done: () => void) => {
  if (uploading.value) {
    ElMessage.warning('正在上传文件，请稍候...')
    return
  }
  
  selectedFile.value = null
  uploadProgress.value = 0
  uploadStatus.value = undefined
  uploadRef.value?.clearFiles()
  done()
}

// 生命周期
onMounted(() => {
  loadProject()
})
</script>

<style scoped>
.project-detail-page {
  background: #f7f8fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.back-button {
  align-self: flex-start;
}

.project-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.project-title {
  font-size: 28px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.project-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}

.create-time {
  font-size: 14px;
  color: #6b7280;
}

.header-right {
  display: flex;
  gap: 12px;
}

.page-content {
  flex: 1;
}

.content-container {
  background: #fff;
  margin: 0 24px 24px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.project-tabs {
  padding: 0 24px;
}

.project-tabs :deep(.el-tabs__header) {
  margin: 0;
  border-bottom: 1px solid #e5e7eb;
}

.project-tabs :deep(.el-tabs__nav-wrap) {
  padding: 0;
}

.project-tabs :deep(.el-tabs__item) {
  padding: 0 20px;
  height: 48px;
  line-height: 48px;
  font-size: 14px;
}

.tab-content {
  padding: 24px 0;
  min-height: 400px;
}

.upload-content {
  padding: 20px 0;
}

.upload-progress {
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-left {
    gap: 12px;
  }
  
  .project-title {
    font-size: 24px;
  }
  
  .project-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .content-container {
    margin: 0 16px 16px 16px;
  }
  
  .project-tabs {
    padding: 0 16px;
  }
  
  .tab-content {
    padding: 16px 0;
  }
}
</style>