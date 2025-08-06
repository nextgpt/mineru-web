import { defineStore } from 'pinia'
import { 
  type TenderProject, 
  type ProjectManagerState, 
  type ViewMode, 
  type UserPreferences
} from '@/types/tender'
import { LocalStorageService } from '@/utils/storage'

export const useProjectStore = defineStore('project', {
  state: (): ProjectManagerState => ({
    projects: [],
    viewMode: 'card',
    loading: false,
    pagination: {
      page: 1,
      pageSize: 20,
      total: 0
    },
    searchKeyword: '',
    selectedProject: undefined
  }),

  getters: {
    // 过滤后的项目列表
    filteredProjects(): TenderProject[] {
      if (!this.searchKeyword) {
        return this.projects
      }
      const keyword = this.searchKeyword.toLowerCase()
      return this.projects.filter(project => 
        project.name.toLowerCase().includes(keyword) ||
        project.fileName.toLowerCase().includes(keyword)
      )
    },

    // 分页后的项目列表
    paginatedProjects(): TenderProject[] {
      const filtered = this.filteredProjects
      const start = (this.pagination.page - 1) * this.pagination.pageSize
      const end = start + this.pagination.pageSize
      return filtered.slice(start, end)
    },

    // 按状态分组的项目
    projectsByStatus(): Record<string, TenderProject[]> {
      return this.projects.reduce((acc, project) => {
        if (!acc[project.status]) {
          acc[project.status] = []
        }
        acc[project.status].push(project)
        return acc
      }, {} as Record<string, TenderProject[]>)
    },

    // 最近修改的项目
    recentProjects(): TenderProject[] {
      return [...this.projects]
        .sort((a, b) => new Date(b.lastModified).getTime() - new Date(a.lastModified).getTime())
        .slice(0, 5)
    }
  },

  actions: {
    // 加载所有项目
    async loadProjects() {
      this.loading = true
      try {
        this.projects = LocalStorageService.getAllProjects()
        this.updatePagination()
      } catch (error) {
        console.error('Failed to load projects:', error)
      } finally {
        this.loading = false
      }
    },

    // 添加项目
    addProject(project: TenderProject) {
      this.projects.unshift(project)
      LocalStorageService.saveProject(project)
      this.updatePagination()
    },

    // 更新项目
    updateProject(id: string, updates: Partial<TenderProject>) {
      const index = this.projects.findIndex(p => p.id === id)
      if (index >= 0) {
        this.projects[index] = { ...this.projects[index], ...updates }
        LocalStorageService.updateProject(id, updates)
        
        // 如果更新的是当前选中的项目，也更新选中状态
        if (this.selectedProject?.id === id) {
          this.selectedProject = this.projects[index]
        }
      }
    },

    // 删除项目
    deleteProject(id: string) {
      this.projects = this.projects.filter(p => p.id !== id)
      LocalStorageService.deleteProject(id)
      this.updatePagination()
      
      // 如果删除的是当前选中的项目，清除选中状态
      if (this.selectedProject?.id === id) {
        this.selectedProject = undefined
      }
    },

    // 选择项目
    selectProject(project: TenderProject) {
      this.selectedProject = project
    },

    // 清除选择
    clearSelection() {
      this.selectedProject = undefined
    },

    // 设置视图模式
    setViewMode(mode: ViewMode) {
      this.viewMode = mode
      this.saveUserPreferences()
    },

    // 设置搜索关键词
    setSearchKeyword(keyword: string) {
      this.searchKeyword = keyword
      this.pagination.page = 1 // 重置到第一页
      this.updatePagination()
    },

    // 设置分页
    setPagination(page: number, pageSize?: number) {
      this.pagination.page = page
      if (pageSize) {
        this.pagination.pageSize = pageSize
      }
      this.updatePagination()
    },

    // 更新分页信息
    updatePagination() {
      this.pagination.total = this.filteredProjects.length
    },

    // 批量删除项目
    deleteMultipleProjects(ids: string[]) {
      this.projects = this.projects.filter(p => !ids.includes(p.id))
      ids.forEach(id => LocalStorageService.deleteProject(id))
      this.updatePagination()
      
      // 如果删除的项目中包含当前选中的项目，清除选中状态
      if (this.selectedProject && ids.includes(this.selectedProject.id)) {
        this.selectedProject = undefined
      }
    },

    // 导出项目数据
    exportProjects(): string {
      return LocalStorageService.exportProjects()
    },

    // 导入项目数据
    async importProjects(jsonData: string): Promise<{ success: boolean; message: string }> {
      const result = LocalStorageService.importProjects(jsonData)
      if (result.success) {
        await this.loadProjects()
      }
      return result
    },

    // 清理过期项目
    cleanupExpiredProjects(daysToKeep: number = 30): number {
      const removedCount = LocalStorageService.cleanupExpiredData(daysToKeep)
      if (removedCount > 0) {
        this.loadProjects()
      }
      return removedCount
    },

    // 保存用户偏好设置
    saveUserPreferences() {
      const preferences: Partial<UserPreferences> = {
        viewMode: this.viewMode
      }
      LocalStorageService.saveSettings({ userPreferences: preferences })
    },

    // 加载用户偏好设置
    loadUserPreferences() {
      const settings = LocalStorageService.getSettings()
      const preferences = settings.userPreferences as UserPreferences
      
      if (preferences) {
        if (preferences.viewMode) {
          this.viewMode = preferences.viewMode
        }
      }
    },

    // 获取项目统计信息
    getProjectStats() {
      const total = this.projects.length
      const byStatus = this.projectsByStatus
      
      return {
        total,
        uploading: byStatus.uploading?.length || 0,
        parsing: byStatus.parsing?.length || 0,
        ready: byStatus.ready?.length || 0,
        generating: byStatus.generating?.length || 0,
        completed: byStatus.completed?.length || 0,
        error: byStatus.error?.length || 0
      }
    }
  }
})