<template>
  <div class="project-manager">
    <!-- 搜索和筛选区域 -->
    <div class="search-filter-section">
      <div class="search-box">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索项目名称或文件名..."
          clearable
          @input="handleSearch"
          @clear="handleSearchClear"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      
      <div class="filter-controls">
        <el-select
          v-model="statusFilter"
          placeholder="筛选状态"
          clearable
          @change="handleStatusFilter"
          style="width: 140px"
        >
          <el-option label="全部状态" value="" />
          <el-option label="上传中" value="uploading" />
          <el-option label="解析中" value="parsing" />
          <el-option label="就绪" value="ready" />
          <el-option label="生成中" value="generating" />
          <el-option label="已完成" value="completed" />
          <el-option label="错误" value="error" />
        </el-select>
        
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="handleDateFilter"
          style="width: 240px"
        />
      </div>
    </div>

    <!-- 视图模式切换 -->
    <div class="view-controls">
      <div class="view-toggle">
        <el-button-group>
          <el-button 
            :type="viewMode === 'card' ? 'primary' : 'default'" 
            @click="setViewMode('card')"
            size="small"
          >
            <el-icon><Grid /></el-icon>
            卡片
          </el-button>
          <el-button 
            :type="viewMode === 'list' ? 'primary' : 'default'" 
            @click="setViewMode('list')"
            size="small"
          >
            <el-icon><List /></el-icon>
            列表
          </el-button>
        </el-button-group>
      </div>
      
      <div class="results-info">
        <span class="results-count">
          共 {{ pagination.total }} 个项目
          <span v-if="hasFilters">（已筛选）</span>
        </span>
      </div>
    </div>

    <!-- 项目列表 -->
    <div class="project-list-container" v-loading="loading">
      <div v-if="paginatedProjects.length > 0" class="projects-content">
        <!-- 卡片视图 -->
        <div v-if="viewMode === 'card'" class="projects-grid">
          <!-- 新建标书卡片 -->
          <div class="new-project-card" @click="$emit('upload-file')">
            <div class="new-card-content">
              <div class="new-card-icon">
                <el-icon><Plus /></el-icon>
              </div>
              <h3 class="new-card-title">新建标书</h3>
              <p class="new-card-desc">
                支持 PDF、DOC、DOCX 格式文件上传
              </p>
              <div class="new-card-button">
                <el-button type="primary" size="large">
                  上传招标文件
                </el-button>
              </div>
            </div>
          </div>
          
          <!-- 项目卡片 -->
          <ProjectCard
            v-for="project in paginatedProjects"
            :key="project.id"
            :project="project"
            :show-actions="showActions"
            @click="handleProjectClick"
            @view="handleProjectClick"
            @edit="handleEditProject"
            @delete="handleDeleteProject"
          />
        </div>
        
        <!-- 列表视图 -->
        <div v-if="viewMode === 'list'" class="projects-table">
          <ProjectList
            :projects="paginatedProjects"
            :show-actions="showActions"
            @row-click="handleProjectClick"
            @view="handleProjectClick"
            @edit="handleEditProject"
            @delete="handleDeleteProject"
          />
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-else-if="!loading" class="empty-state">
        <el-empty 
          :description="hasFilters ? '没有找到匹配的项目' : '暂无项目'"
          :image-size="120"
        >
          <el-button 
            v-if="!hasFilters" 
            type="primary" 
            @click="$emit('upload-file')"
          >
            上传第一个文件
          </el-button>
          <el-button 
            v-else 
            @click="clearAllFilters"
          >
            清除筛选条件
          </el-button>
        </el-empty>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="pagination.total > 0" class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { 
  Search, 
  Grid,
  List,
  Plus
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProjectStore } from '@/store/project'
import { storeToRefs } from 'pinia'
import ProjectCard from './ProjectCard.vue'
import ProjectList from './ProjectList.vue'
import type { TenderProject, ViewMode } from '@/types/tender'

// Props 和 Emits
interface Props {
  showActions?: boolean
}

interface Emits {
  (e: 'project-click', project: TenderProject): void
  (e: 'project-edit', project: TenderProject): void
  (e: 'project-delete', project: TenderProject): void
  (e: 'upload-file'): void
}

withDefaults(defineProps<Props>(), {
  showActions: true
})

const emit = defineEmits<Emits>()

// Store
const projectStore = useProjectStore()
const { projects, loading, pagination, viewMode } = storeToRefs(projectStore)

// 搜索和筛选状态
const searchKeyword = ref('')
const statusFilter = ref('')
const dateRange = ref<[string, string] | null>(null)

// 计算属性
const filteredProjects = computed(() => {
  let result = [...projects.value]
  
  // 按时间倒序排列（最新的在前）
  result.sort((a, b) => new Date(b.uploadTime).getTime() - new Date(a.uploadTime).getTime())
  
  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(project => 
      project.name.toLowerCase().includes(keyword) ||
      project.fileName.toLowerCase().includes(keyword)
    )
  }
  
  // 状态筛选
  if (statusFilter.value) {
    result = result.filter(project => project.status === statusFilter.value)
  }
  
  // 日期范围筛选
  if (dateRange.value && dateRange.value.length === 2) {
    const [startDate, endDate] = dateRange.value
    result = result.filter(project => {
      const uploadDate = new Date(project.uploadTime).toISOString().split('T')[0]
      return uploadDate >= startDate && uploadDate <= endDate
    })
  }
  
  return result
})

const paginatedProjects = computed(() => {
  const start = (pagination.value.page - 1) * pagination.value.pageSize
  const end = start + pagination.value.pageSize
  return filteredProjects.value.slice(start, end)
})

const hasFilters = computed(() => {
  return !!(searchKeyword.value || statusFilter.value || dateRange.value)
})

// 方法
const handleSearch = () => {
  pagination.value.page = 1
  updatePagination()
}

const handleSearchClear = () => {
  searchKeyword.value = ''
  pagination.value.page = 1
  updatePagination()
}

const handleStatusFilter = () => {
  pagination.value.page = 1
  updatePagination()
}

const handleDateFilter = () => {
  pagination.value.page = 1
  updatePagination()
}

const clearAllFilters = () => {
  searchKeyword.value = ''
  statusFilter.value = ''
  dateRange.value = null
  pagination.value.page = 1
  updatePagination()
}

const setViewMode = (mode: ViewMode) => {
  projectStore.setViewMode(mode)
}

const updatePagination = () => {
  pagination.value.total = filteredProjects.value.length
}

const handleSizeChange = (size: number) => {
  pagination.value.pageSize = size
  pagination.value.page = 1
  updatePagination()
}

const handleCurrentChange = (page: number) => {
  pagination.value.page = page
}

const handleProjectClick = (project: TenderProject) => {
  emit('project-click', project)
}

const handleEditProject = (project: TenderProject) => {
  emit('project-edit', project)
}

const handleDeleteProject = async (project: TenderProject) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目 "${project.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    projectStore.deleteProject(project.id)
    ElMessage.success('项目删除成功')
    emit('project-delete', project)
    
    // 更新分页
    updatePagination()
    
    // 如果当前页没有数据了，回到上一页
    if (paginatedProjects.value.length === 0 && pagination.value.page > 1) {
      pagination.value.page -= 1
    }
  } catch {
    // 用户取消删除
  }
}



// 监听筛选条件变化，更新分页
watch([searchKeyword, statusFilter, dateRange], () => {
  updatePagination()
}, { deep: true })

// 组件挂载时加载项目数据
onMounted(() => {
  projectStore.loadProjects()
  updatePagination()
})
</script>

<style scoped>
.project-manager {
  width: 100%;
}

.search-filter-section {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  align-items: center;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 300px;
}

.filter-controls {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.view-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.view-toggle {
  display: flex;
  align-items: center;
}

.results-info {
  display: flex;
  align-items: center;
}

.results-count {
  font-size: 14px;
  color: #666;
}

.project-list-container {
  min-height: 400px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 280px));
  gap: 20px;
  margin-bottom: 24px;
  align-items: start;
  justify-content: start;
}

.new-project-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s;
  height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  color: white;
  position: relative;
  overflow: hidden;
}

.new-project-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.1);
  opacity: 0;
  transition: opacity 0.3s;
}

.new-project-card:hover::before {
  opacity: 1;
}

.new-project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.3);
}

.new-card-content {
  position: relative;
  z-index: 1;
}

.new-card-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.9;
}

.new-card-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: white;
}

.new-card-desc {
  font-size: 14px;
  margin: 0 0 20px 0;
  opacity: 0.8;
  line-height: 1.4;
}

.new-card-button {
  margin-top: auto;
}

.new-card-button .el-button {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(10px);
}

.new-card-button .el-button:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.projects-table {
  margin-bottom: 24px;
}



.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-filter-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-box {
    min-width: auto;
  }
  
  .filter-controls {
    justify-content: space-between;
  }
  
  .view-controls {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .view-toggle {
    justify-content: center;
  }
  
  .results-info {
    justify-content: center;
  }
  
  .projects-grid {
    grid-template-columns: 1fr;
    justify-items: start;
  }
  
  .new-project-card {
    width: 100%;
    max-width: 280px;
  }
}
</style>