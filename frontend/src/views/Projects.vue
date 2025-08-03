<template>
  <div class="projects-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">文档列表</h1>
        <p class="page-subtitle">共{{ total }}个文档数据</p>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchQuery"
          placeholder="请输入查询名称"
          clearable
          @input="handleSearch"
          style="width: 240px; margin-right: 12px"
        >
          <template #suffix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <!-- 视图切换按钮 -->
        <div class="view-toggle">
          <el-button-group>
            <el-button 
              :type="viewMode === 'list' ? 'primary' : 'default'"
              @click="viewMode = 'list'"
              size="small"
            >
              列表模式
            </el-button>
            <el-button 
              :type="viewMode === 'card' ? 'primary' : 'default'"
              @click="viewMode = 'card'"
              size="small"
            >
              卡片模式
            </el-button>
          </el-button-group>
        </div>
      </div>
    </div>

    <!-- 卡片模式 -->
    <div v-if="viewMode === 'card'" class="card-view">
      <div class="projects-grid">
        <!-- 新建标书卡片 - 永远第一个 -->
        <div class="project-card create-card" @click="showCreateDialog = true">
          <div class="create-card-content">
            <div class="create-icon">
              <div class="file-icons">
                <div class="file-icon doc"></div>
                <div class="file-icon docx"></div>
                <div class="file-icon pdf"></div>
              </div>
            </div>
            <div class="create-text">
              <h3>新建标书</h3>
              <p>支持(.doc/.docx/.pdf)格式文件一次性上传多个文件</p>
              <el-button type="primary" class="upload-btn">
                选择上传招标文件
              </el-button>
            </div>
          </div>
        </div>

        <!-- 项目卡片 -->
        <div 
          v-for="project in projects" 
          :key="project.id" 
          class="project-card"
          @click="viewProject(project)"
        >
          <div class="card-header">
            <el-tag 
              :type="getStatusType(project.status)" 
              size="small"
              class="status-tag"
            >
              {{ getStatusText(project.status) }}
            </el-tag>
            <el-dropdown @command="handleCardAction" trigger="click">
              <el-icon class="more-icon"><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="{action: 'view', project}">查看</el-dropdown-item>
                  <el-dropdown-item :command="{action: 'edit', project}">编辑</el-dropdown-item>
                  <el-dropdown-item :command="{action: 'delete', project}">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          
          <div class="card-content">
            <h3 class="project-title">{{ project.name }}</h3>
            <p v-if="project.description" class="project-description">{{ project.description }}</p>
            
            <div class="project-meta">
              <div class="meta-item">
                <span class="meta-label">创建时间:</span>
                <span class="meta-value">{{ formatDate(project.created_at) }}</span>
              </div>
              <div v-if="project.original_file" class="meta-item">
                <span class="meta-label">文件:</span>
                <span class="meta-value">{{ project.original_file.filename }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="projects.length === 0 && !loading" class="empty-state">
        <p>- 数据到底了 -</p>
      </div>
    </div>

    <!-- 列表模式 -->
    <div v-else class="list-view">
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
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[12, 24, 48]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
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
import { Upload, Document, Setting, Search, MoreFilled } from '@element-plus/icons-vue'
import { projectsApi, type Project, type CreateProjectRequest } from '@/api/projects'

const router = useRouter()

// 响应式数据
const projects = ref<Project[]>([])
const loading = ref(false)
const creating = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)
const viewMode = ref<'card' | 'list'>('card')

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

// 卡片操作处理
const handleCardAction = (command: {action: string, project: Project}) => {
  const { action, project } = command
  switch (action) {
    case 'view':
      viewProject(project)
      break
    case 'edit':
      editProject(project)
      break
    case 'delete':
      deleteProject(project)
      break
  }
}

// 生命周期
onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.projects-page {
  padding: 0 27px; /* 与导航栏间距保持一致 */
  background: #f7f8fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
  margin-bottom: 20px;
  height: 64px; /* 与logo区域高度一致 */
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-toggle {
  margin-left: 12px;
}

/* 卡片视图 */
.card-view {
  margin-bottom: 24px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr); /* 每行固定5个卡片 */
  gap: 20px;
  margin-bottom: 20px;
}

.project-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.2s ease;
  overflow: hidden;
  aspect-ratio: 1; /* 保持正方形比例 */
  display: flex;
  flex-direction: column;
}

.project-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

/* 新建标书卡片 */
.create-card {
  border: 2px dashed #d1d5db;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.create-card:hover {
  border-color: #3b82f6;
  background: #f8faff;
}

.create-card-content {
  text-align: center;
  padding: 16px;
  width: 100%;
}

.create-icon {
  margin-bottom: 16px;
}

.file-icons {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
}

.file-icon {
  width: 24px;
  height: 30px;
  border-radius: 3px;
  position: relative;
}

.file-icon.doc {
  background: #4285f4;
}

.file-icon.docx {
  background: #0078d4;
}

.file-icon.pdf {
  background: #ff5722;
}

.create-text h3 {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 6px 0;
}

.create-text p {
  font-size: 11px;
  color: #6b7280;
  margin: 0 0 12px 0;
  line-height: 1.3;
}

.upload-btn {
  font-size: 12px;
  padding: 6px 12px;
}

/* 项目卡片 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 12px 0 12px;
  flex-shrink: 0;
}

.status-tag {
  font-size: 10px;
}

.more-icon {
  color: #9ca3af;
  cursor: pointer;
  padding: 2px;
  border-radius: 3px;
  transition: all 0.2s;
  font-size: 14px;
}

.more-icon:hover {
  color: #374151;
  background: #f3f4f6;
}

.card-content {
  padding: 8px 12px 12px 12px;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.project-title {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px 0;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.project-description {
  font-size: 11px;
  color: #6b7280;
  margin: 0 0 8px 0;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.project-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: auto;
}

.meta-item {
  display: flex;
  align-items: center;
  font-size: 10px;
}

.meta-label {
  color: #9ca3af;
  margin-right: 4px;
  min-width: 50px;
}

.meta-value {
  color: #374151;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 列表视图 */
.list-view {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.project-name {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.name-text {
  font-weight: 500;
  color: #1f2937;
}

.description-text {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.file-name {
  font-size: 13px;
  color: #374151;
}

.no-file {
  color: #9ca3af;
  font-size: 13px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #9ca3af;
  font-size: 14px;
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .projects-grid {
    grid-template-columns: repeat(4, 1fr); /* 中等屏幕4列 */
  }
}

@media (max-width: 1100px) {
  .projects-grid {
    grid-template-columns: repeat(3, 1fr); /* 小屏幕3列 */
  }
}

@media (max-width: 768px) {
  .projects-page {
    padding: 0 16px; /* 移动端减少边距 */
  }
  
  .projects-grid {
    grid-template-columns: repeat(2, 1fr); /* 移动端2列 */
    gap: 12px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
    height: auto;
    padding: 16px 0;
  }
  
  .header-right {
    flex-direction: column;
    gap: 8px;
  }
  
  .header-right .el-input {
    width: 100% !important;
  }
}

@media (max-width: 480px) {
  .projects-grid {
    grid-template-columns: 1fr; /* 超小屏幕1列 */
  }
}
</style>