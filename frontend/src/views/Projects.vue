<template>
  <div class="projects-content">
    <div class="projects-header">
      <h1 class="projects-title">项目管理</h1>
      <div class="projects-actions">
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
        <el-button type="primary" @click="$router.push('/upload')">
          <el-icon><Plus /></el-icon>
          上传文件
        </el-button>
      </div>
    </div>

    <!-- 项目管理组件 -->
    <ProjectManager
      @project-click="handleProjectClick"
      @project-edit="handleProjectEdit"
      @project-delete="handleProjectDelete"
      @upload-file="handleUploadFile"
    />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Plus, Grid, List } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '@/store/project'
import { storeToRefs } from 'pinia'
import ProjectManager from '@/components/ProjectManager.vue'
import type { TenderProject, ViewMode } from '@/types/tender'

const router = useRouter()
const projectStore = useProjectStore()
const { viewMode } = storeToRefs(projectStore)

const setViewMode = (mode: ViewMode) => {
  projectStore.setViewMode(mode)
}

const handleProjectClick = (project: TenderProject) => {
  router.push(`/files/preview/${project.id}`)
}

const handleProjectEdit = (_project: TenderProject) => {
  // TODO: 实现项目编辑功能
  ElMessage.info('项目编辑功能开发中...')
}

const handleProjectDelete = (project: TenderProject) => {
  ElMessage.success(`项目 "${project.name}" 已删除`)
}

const handleUploadFile = () => {
  router.push('/upload')
}
</script>

<style scoped>
.projects-content {
  height: 100%;
  padding-left: 27px; /* 导航栏80px的1/3约27px */
  padding-right: 20px;
}

.projects-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.projects-title {
  font-size: 24px;
  font-weight: 600;
  color: #222;
  margin: 0;
}

.projects-actions {
  display: flex;
  gap: 16px;
  align-items: center;
}

.view-toggle {
  display: flex;
  align-items: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .projects-content {
    padding-left: 16px;
    padding-right: 16px;
  }
  
  .projects-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .projects-actions {
    justify-content: space-between;
  }
}
</style>