<template>
  <div class="projects-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">项目管理</h1>
        <p class="page-subtitle">管理您的招标项目和生成的标书</p>
      </div>
      <div class="header-right">
        <el-button @click="goToHome" class="home-button">
          <el-icon><HomeFilled /></el-icon>
          返回首页
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Upload /></el-icon>
          新建项目
        </el-button>
      </div>
    </div>

    <div class="page-content">
      <!-- 搜索和筛选 -->
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索项目名称..."
          clearable
          @input="handleSearch"
          style="width: 300px"
        >
          <template #prefix>
            <el-icon><Setting /></el-icon>
          </template>
        </el-input>
        
        <el-select
          v-model="statusFilter"
          placeholder="筛选状态"
          clearable
          @change="handleStatusFilter"
          style="width: 150px; margin-left: 16px"
        >
          <el-option label="全部状态" value="" />
          <el-option label="已创建" value="created" />
          <el-option label="解析中" value="parsing" />
          <el-option label="分析中" value="analyzing" />
          <el-option label="大纲已生成" value="outline_generated" />
          <el-option label="生成中" value="document_generating" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>
      </div>

      <!-- 项目列表 -->
      <div class="projects-table">
        <el-table
          :data="projects"
          v-loading="loading"
          empty-text="暂无项目数据"
          @row-click="handleRowClick"
          style="width: 100%"
        >
          <el-table-column prop="name" label="项目名称" min-width="200">
            <template #default="{ row }">
              <div class="project-name">
                <span class="name-text">{{ row.name }}</span>
                <span v-if="row.description" class="description-text">{{ row.description }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="status" label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="original_file" label="招标文件" width="200">
            <template #default="{ row }">
              <div v-if="row.original_file" class="file-info">
                <el-icon><Document /></el-icon>
                <span class="file-name">{{ row.original_file.filename }}</span>
              </div>
              <span v-else class="no-file">未上传</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click.stop="viewProject(row)">
                查看
              </el-button>
              <el-button size="small" type="primary" @click.stop="editProject(row)">
                编辑
              </el-button>
              <el-button 
                size="small" 
                type="danger" 
                @click.stop="deleteProject(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </div>

    <!-- 创建项目对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="新建项目"
      width="500px"
      :before-close="handleCreateDialogClose"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createFormRules"
        label-width="80px"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input
            v-model="createForm.name"
            placeholder="请输入项目名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="createForm.description"
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
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="handleCreateProject" :loading="creating">
            创建
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Upload, Document, Setting, HomeFilled } from '@element-plus/icons-vue'
import { projectsApi, type Project, type CreateProjectRequest } from '@/api/projects'

const router = useRouter()

// 响应式数据
const projects = ref<Project[]>([])
const loading = ref(false)
const creating = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 创建项目对话框
const showCreateDialog = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive<CreateProjectRequest>({
  name: '',
  description: ''
})

const createFormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 100, message: '项目名称长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

// 计算属性和方法
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

// 加载项目列表
const loadProjects = async () => {
  try {
    loading.value = true
    const response = await projectsApi.getProjects(
      currentPage.value,
      pageSize.value,
      searchQuery.value || undefined
    )
    projects.value = response.projects
    total.value = response.total
  } catch (error) {
    console.error('加载项目列表失败:', error)
    ElMessage.error('加载项目列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
let searchTimer: NodeJS.Timeout
const handleSearch = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadProjects()
  }, 500)
}

// 状态筛选处理
const handleStatusFilter = () => {
  currentPage.value = 1
  loadProjects()
}

// 分页处理
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadProjects()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadProjects()
}

// 行点击处理
const handleRowClick = (row: Project) => {
  viewProject(row)
}

// 查看项目
const viewProject = (project: Project) => {
  router.push(`/projects/${project.id}`)
}

// 编辑项目
const editProject = (_project: Project) => {
  // TODO: 实现编辑功能
  ElMessage.info('编辑功能开发中...')
}

// 删除项目
const deleteProject = async (project: Project) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目"${project.name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await projectsApi.deleteProject(project.id)
    ElMessage.success('项目删除成功')
    loadProjects()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除项目失败:', error)
      ElMessage.error('删除项目失败')
    }
  }
}

// 创建项目对话框处理
const handleCreateDialogClose = (done: () => void) => {
  if (creating.value) {
    ElMessage.warning('正在创建项目，请稍候...')
    return
  }
  
  createForm.name = ''
  createForm.description = ''
  createFormRef.value?.clearValidate()
  done()
}

// 创建项目
const handleCreateProject = async () => {
  if (!createFormRef.value) return
  
  try {
    const valid = await createFormRef.value.validate()
    if (!valid) return
    
    creating.value = true
    const project = await projectsApi.createProject(createForm)
    
    ElMessage.success('项目创建成功')
    showCreateDialog.value = false
    
    // 跳转到项目详情页
    router.push(`/projects/${project.id}`)
  } catch (error) {
    console.error('创建项目失败:', error)
    ElMessage.error('创建项目失败')
  } finally {
    creating.value = false
  }
}

// 返回首页
const goToHome = () => {
  router.push('/')
}

// 生命周期
onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.projects-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 40px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: white;
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

.header-right {
  display: flex;
  gap: 12px;
}

.header-right .el-button {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(45deg, #6366f1, #8b5cf6);
  border: none;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  transition: all 0.3s ease;
}

.header-right .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
}

.home-button {
  background: rgba(255, 255, 255, 0.2) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: white !important;
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.1) !important;
}

.home-button:hover {
  background: rgba(255, 255, 255, 0.3) !important;
  box-shadow: 0 8px 20px rgba(255, 255, 255, 0.2) !important;
}

.page-content {
  margin: 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.search-bar {
  padding: 24px 32px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.5);
}

.search-bar .el-input {
  border-radius: 12px;
}

.search-bar .el-input :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.search-bar .el-select {
  border-radius: 12px;
}

.search-bar .el-select :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.projects-table {
  padding: 0 32px 32px 32px;
}

.projects-table :deep(.el-table) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.projects-table :deep(.el-table__header) {
  background: linear-gradient(45deg, #f8faff, #f0f4ff);
}

.projects-table :deep(.el-table__header th) {
  background: transparent;
  border-bottom: 2px solid #e5e7eb;
  font-weight: 600;
  color: #374151;
}

.projects-table :deep(.el-table__body tr:hover) {
  background: rgba(99, 102, 241, 0.05);
}

.projects-table :deep(.el-table__body td) {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.project-name {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.name-text {
  font-weight: 600;
  color: #1f2937;
  font-size: 15px;
}

.description-text {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.4;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 8px;
  color: #6366f1;
  font-size: 13px;
  font-weight: 500;
}

.file-name {
  font-size: 13px;
  color: #6366f1;
}

.no-file {
  color: #9ca3af;
  font-size: 13px;
  font-style: italic;
}

.projects-table :deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.projects-table :deep(.el-button--small) {
  padding: 6px 12px;
}

.projects-table :deep(.el-button:hover) {
  transform: translateY(-1px);
}

.projects-table :deep(.el-tag) {
  border-radius: 8px;
  font-weight: 500;
  border: none;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.pagination-wrapper :deep(.el-pagination) {
  background: transparent;
}

.pagination-wrapper :deep(.el-pager li) {
  border-radius: 8px;
  margin: 0 2px;
  transition: all 0.3s ease;
}

.pagination-wrapper :deep(.el-pager li:hover) {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

.pagination-wrapper :deep(.el-pager li.is-active) {
  background: linear-gradient(45deg, #6366f1, #8b5cf6);
  color: white;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    padding: 24px 20px;
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .page-title {
    font-size: 28px;
  }
  
  .page-content {
    margin: 20px;
  }
  
  .search-bar {
    padding: 20px;
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .search-bar .el-input,
  .search-bar .el-select {
    width: 100% !important;
    margin-left: 0 !important;
  }
  
  .projects-table {
    padding: 0 20px 20px 20px;
  }
}

@media (max-width: 480px) {
  .page-header {
    padding: 20px 16px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .page-content {
    margin: 16px;
  }
  
  .search-bar {
    padding: 16px;
  }
  
  .projects-table {
    padding: 0 16px 16px 16px;
  }
}
</style>