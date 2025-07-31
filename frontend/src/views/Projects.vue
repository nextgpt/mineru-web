<template>
  <div class="projects-root">
    <div class="projects-card">
      <div class="projects-header">
        <div class="header-left">
          <span class="projects-title">项目管理</span>
          <span class="projects-subtitle">管理您的招标项目</span>
        </div>
        <div class="header-right">
          <el-button type="primary" size="large" class="create-btn" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon> 新建项目
          </el-button>
        </div>
      </div>

      <!-- 搜索和筛选 -->
      <div class="filter-bar">
        <el-input
          v-model="params.search"
          placeholder="搜索项目名称"
          class="search-input"
          clearable
          prefix-icon="Search"
          @input="onParamChange"
        />
        <el-select v-model="params.status" placeholder="项目状态" class="status-select" clearable @change="onParamChange">
          <el-option label="全部" value="" />
          <el-option label="分析中" value="analyzing" />
          <el-option label="已分析" value="analyzed" />
          <el-option label="大纲生成中" value="outlining" />
          <el-option label="内容生成中" value="generating" />
          <el-option label="已完成" value="completed" />
        </el-select>
      </div>

      <!-- 项目列表 -->
      <div class="projects-grid" v-if="projects && projects.length > 0 && !loading">
        <div 
          v-for="project in projects" 
          :key="project.id" 
          class="project-card"
          @click="openProject(project.id)"
        >
          <div class="card-header">
            <div class="project-status">
              <el-tag :type="getStatusType(project.status)">
                {{ getStatusText(project.status) }}
              </el-tag>
            </div>
            <el-dropdown @command="(cmd) => handleCommand(cmd, project)" trigger="click" @click.stop>
              <el-icon class="more-icon"><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item command="export" :disabled="project.status !== 'completed'">导出</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          
          <div class="card-content">
            <h3 class="project-title">{{ project.project_name }}</h3>
            <p class="project-info">
              <el-icon><Document /></el-icon>
              基于文件：{{ project.source_filename }}
            </p>
            <div class="project-progress" v-if="project.progress !== undefined">
              <el-progress 
                :percentage="project.progress" 
                :stroke-width="6"
                :show-text="false"
              />
              <span class="progress-text">{{ project.progress }}%</span>
            </div>
          </div>
          
          <div class="card-footer">
            <span class="create-time">
              {{ formatTime(project.created_at) }}
            </span>
            <div class="action-buttons">
              <el-button 
                v-if="project.status === 'completed'" 
                size="small" 
                type="success"
                @click.stop="downloadDocument(project.id)"
              >
                下载标书
              </el-button>
              <el-button 
                v-else 
                size="small" 
                type="primary"
                @click.stop="continueProject(project.id)"
              >
                继续编辑
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <el-empty v-else-if="!loading" description="暂无项目" :image-size="80" class="projects-empty" />
      <el-skeleton v-else :rows="6" animated style="margin:32px 0" />

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="params.page"
          v-model:page-size="params.pageSize"
          :total="total"
          :page-sizes="[12, 24, 48]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="onParamChange"
          @current-change="onParamChange"
        />
      </div>
    </div>

    <!-- 新建项目对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建招标项目" width="500px">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="100px">
        <el-form-item label="项目名称" prop="project_name">
          <el-input v-model="createForm.project_name" placeholder="请输入项目名称" />
        </el-form-item>
        
        <el-form-item label="招标文件" prop="source_file_id">
          <el-select 
            v-model="createForm.source_file_id" 
            placeholder="选择已上传的招标文件"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="file in availableFiles"
              :key="file.id"
              :label="file.filename"
              :value="file.id"
            />
          </el-select>
          <div class="form-tip">
            如果没有找到文件，请先到 
            <router-link to="/upload" style="color: #409eff;">文件上传</router-link> 
            页面上传招标文件
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createProject" :loading="creating">
          创建项目
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { Plus, Document, MoreFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { getUserId } from '@/utils/user'
import { wsService } from '@/services/websocket'

interface ProjectItem {
  id: string
  project_name: string
  source_filename: string
  status: 'analyzing' | 'analyzed' | 'outlining' | 'outlined' | 'generating' | 'generated' | 'exporting' | 'completed' | 'failed'
  progress?: number
  created_at: string
  updated_at: string
}

interface FileItem {
  id: number
  filename: string
  status: string
}

const router = useRouter()

const projects = ref<ProjectItem[]>([])
const total = ref(0)
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)
const availableFiles = ref<FileItem[]>([])

const params = reactive({
  page: 1,
  pageSize: 12,
  search: '',
  status: ''
})

const createForm = reactive({
  project_name: '',
  source_file_id: null as number | null
})

const createFormRef = ref()

const createRules = {
  project_name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' }
  ],
  source_file_id: [
    { required: true, message: '请选择招标文件', trigger: 'change' }
  ]
}

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

const getStatusType = (status: string) => {
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
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
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
  return map[status] || '未知状态'
}

const fetchProjects = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/tender/projects', {
      params: {
        page: params.page,
        page_size: params.pageSize,
        search: params.search,
        status: params.status
      },
      headers: { 'X-User-Id': getUserId() }
    })
    
    projects.value = res.data.projects || []
    total.value = res.data.total || 0
  } catch (e) {
    ElMessage.error('获取项目列表失败')
    projects.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const fetchAvailableFiles = async () => {
  try {
    const res = await axios.get('/api/files', {
      params: {
        page: 1,
        page_size: 100,
        status: 'parsed' // 只显示已解析的文件
      },
      headers: { 'X-User-Id': getUserId() }
    })
    
    availableFiles.value = res.data.files || []
  } catch (e) {
    console.error('获取可用文件列表失败:', e)
    availableFiles.value = []
  }
}

const createProject = async () => {
  if (!createFormRef.value) return
  
  try {
    await createFormRef.value.validate()
    creating.value = true
    
    const res = await axios.post('/api/tender/projects', createForm, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    ElMessage.success('项目创建成功')
    showCreateDialog.value = false
    
    // 重置表单
    createForm.project_name = ''
    createForm.source_file_id = null
    
    // 刷新项目列表
    await fetchProjects()
    
    // 跳转到项目详情页
    router.push(`/projects/${res.data.id}`)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '创建项目失败')
  } finally {
    creating.value = false
  }
}

const openProject = (projectId: string) => {
  router.push(`/projects/${projectId}`)
}

const continueProject = (projectId: string) => {
  router.push(`/projects/${projectId}`)
}

const downloadDocument = async (projectId: string) => {
  try {
    const res = await axios.get(`/api/tender/projects/${projectId}/documents`, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    if (res.data.documents && res.data.documents.length > 0) {
      const document = res.data.documents[0] // 获取最新的文档
      const downloadRes = await axios.get(`/api/tender/documents/${document.id}/download`, {
        headers: { 'X-User-Id': getUserId() }
      })
      
      // 下载文件
      window.open(downloadRes.data.download_url, '_blank')
    } else {
      ElMessage.warning('暂无可下载的文档')
    }
  } catch (e) {
    ElMessage.error('下载失败')
  }
}

const handleCommand = async (command: string, project: ProjectItem) => {
  switch (command) {
    case 'edit':
      router.push(`/projects/${project.id}`)
      break
    case 'export':
      await downloadDocument(project.id)
      break
    case 'delete':
      ElMessageBox.confirm(
        '确定要删除该项目吗？',
        '警告',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        try {
          await axios.delete(`/api/tender/projects/${project.id}`, {
            headers: { 'X-User-Id': getUserId() }
          })
          ElMessage.success('删除成功')
          fetchProjects()
        } catch (e) {
          ElMessage.error('删除失败')
        }
      }).catch(() => {})
      break
  }
}

const onParamChange = () => {
  fetchProjects()
}

// 监听对话框显示状态，获取可用文件
watch(showCreateDialog, (newVal) => {
  if (newVal) {
    fetchAvailableFiles()
  }
})

// 监听搜索和状态变化
watch([() => params.search, () => params.status], () => {
  params.page = 1
  fetchProjects()
})

// 监听分页变化
watch([() => params.page, () => params.pageSize], () => {
  fetchProjects()
})

onMounted(() => {
  fetchProjects()
  
  // 监听WebSocket项目更新
  wsService.on('project_update', (data: any) => {
    // 更新项目列表中的项目状态
    const projectIndex = projects.value.findIndex(p => p.id === data.project_id)
    if (projectIndex !== -1) {
      projects.value[projectIndex] = {
        ...projects.value[projectIndex],
        status: data.status,
        progress: data.progress
      }
    }
  })
})

onUnmounted(() => {
  // 清理WebSocket监听器
  wsService.off('project_update', () => {})
})
</script>

<style scoped>
.projects-root {
  width: 100%;
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
  padding: 24px 32px 0 32px;
  box-sizing: border-box;
  overflow-x: hidden;
}

.projects-card {
  width: 100%;
  max-width: none;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  box-sizing: border-box;
}

.projects-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  flex-direction: column;
}

.projects-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px 0;
}

.projects-subtitle {
  color: #6b7280;
  font-size: 0.875rem;
}

.create-btn {
  border-radius: 8px;
  font-size: 1.05rem;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.search-input {
  width: 300px;
}

.status-select {
  width: 140px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.project-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.2s ease;
}

.project-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.more-icon {
  color: #9ca3af;
  cursor: pointer;
  font-size: 18px;
}

.more-icon:hover {
  color: #6b7280;
}

.card-content {
  margin-bottom: 16px;
}

.project-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.project-info {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #6b7280;
  font-size: 0.875rem;
  margin-bottom: 12px;
}

.project-progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-text {
  font-size: 0.75rem;
  color: #6b7280;
  min-width: 32px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #f3f4f6;
}

.create-time {
  font-size: 0.75rem;
  color: #9ca3af;
}

.projects-empty {
  margin: 32px 0 0 0;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  margin-bottom: 10px;
}

.form-tip {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 4px;
}

:deep(.el-progress-bar__outer) {
  background-color: #f3f4f6;
}

:deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, #409eff 0%, #67c23a 100%);
}
</style>