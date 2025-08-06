import type { TenderProject } from '@/types/tender'

/**
 * 本地存储服务
 */
export class LocalStorageService {
  private static readonly PROJECTS_KEY = 'tender_projects'
  private static readonly SETTINGS_KEY = 'tender_settings'

  /**
   * 保存项目
   */
  static saveProject(project: TenderProject): void {
    const projects = this.getAllProjects()
    const existingIndex = projects.findIndex(p => p.id === project.id)
    
    if (existingIndex >= 0) {
      projects[existingIndex] = { ...project, lastModified: new Date().toISOString() }
    } else {
      projects.push({ ...project, lastModified: new Date().toISOString() })
    }
    
    this.saveProjects(projects)
  }

  /**
   * 获取项目
   */
  static getProject(id: string): TenderProject | null {
    const projects = this.getAllProjects()
    return projects.find(p => p.id === id) || null
  }

  /**
   * 获取所有项目
   */
  static getAllProjects(): TenderProject[] {
    try {
      const data = localStorage.getItem(this.PROJECTS_KEY)
      return data ? JSON.parse(data) : []
    } catch (error) {
      console.error('Failed to load projects from localStorage:', error)
      return []
    }
  }

  /**
   * 删除项目
   */
  static deleteProject(id: string): void {
    const projects = this.getAllProjects().filter(p => p.id !== id)
    this.saveProjects(projects)
  }

  /**
   * 更新项目
   */
  static updateProject(id: string, updates: Partial<TenderProject>): void {
    const projects = this.getAllProjects()
    const index = projects.findIndex(p => p.id === id)
    
    if (index >= 0) {
      projects[index] = { 
        ...projects[index], 
        ...updates, 
        lastModified: new Date().toISOString() 
      }
      this.saveProjects(projects)
    }
  }

  /**
   * 保存项目列表
   */
  private static saveProjects(projects: TenderProject[]): void {
    try {
      localStorage.setItem(this.PROJECTS_KEY, JSON.stringify(projects))
    } catch (error) {
      console.error('Failed to save projects to localStorage:', error)
    }
  }

  /**
   * 清空所有项目
   */
  static clearAllProjects(): void {
    localStorage.removeItem(this.PROJECTS_KEY)
  }

  /**
   * 保存应用设置
   */
  static saveSettings(settings: Record<string, any>): void {
    try {
      const existingSettings = this.getSettings()
      const newSettings = { ...existingSettings, ...settings }
      localStorage.setItem(this.SETTINGS_KEY, JSON.stringify(newSettings))
    } catch (error) {
      console.error('Failed to save settings to localStorage:', error)
    }
  }

  /**
   * 获取应用设置
   */
  static getSettings(): Record<string, any> {
    try {
      const data = localStorage.getItem(this.SETTINGS_KEY)
      return data ? JSON.parse(data) : {}
    } catch (error) {
      console.error('Failed to load settings from localStorage:', error)
      return {}
    }
  }

  /**
   * 获取特定设置
   */
  static getSetting<T>(key: string, defaultValue: T): T {
    const settings = this.getSettings()
    return settings[key] !== undefined ? settings[key] : defaultValue
  }

  /**
   * 导出项目数据
   */
  static exportProjects(): string {
    const projects = this.getAllProjects()
    const settings = this.getSettings()
    
    const exportData = {
      projects,
      settings,
      exportTime: new Date().toISOString(),
      version: '1.0.0'
    }
    
    return JSON.stringify(exportData, null, 2)
  }

  /**
   * 导入项目数据
   */
  static importProjects(jsonData: string): { success: boolean; message: string } {
    try {
      const importData = JSON.parse(jsonData)
      
      if (!importData.projects || !Array.isArray(importData.projects)) {
        return { success: false, message: '无效的数据格式' }
      }
      
      // 验证项目数据结构
      for (const project of importData.projects) {
        if (!project.id || !project.name || !project.fileName) {
          return { success: false, message: '项目数据结构不完整' }
        }
      }
      
      // 合并现有项目
      const existingProjects = this.getAllProjects()
      const existingIds = new Set(existingProjects.map(p => p.id))
      
      const newProjects = importData.projects.filter((p: TenderProject) => !existingIds.has(p.id))
      const allProjects = [...existingProjects, ...newProjects]
      
      this.saveProjects(allProjects)
      
      // 导入设置
      if (importData.settings) {
        this.saveSettings(importData.settings)
      }
      
      return { 
        success: true, 
        message: `成功导入 ${newProjects.length} 个项目` 
      }
    } catch (error) {
      console.error('Failed to import projects:', error)
      return { success: false, message: '导入失败：数据格式错误' }
    }
  }

  /**
   * 获取存储使用情况
   */
  static getStorageUsage(): { used: number; total: number; percentage: number } {
    try {
      let used = 0
      for (let key in localStorage) {
        if (localStorage.hasOwnProperty(key)) {
          used += localStorage[key].length + key.length
        }
      }
      
      // 大多数浏览器的localStorage限制是5MB
      const total = 5 * 1024 * 1024
      const percentage = Math.round((used / total) * 100)
      
      return { used, total, percentage }
    } catch (error) {
      console.error('Failed to get storage usage:', error)
      return { used: 0, total: 0, percentage: 0 }
    }
  }

  /**
   * 清理过期数据
   */
  static cleanupExpiredData(daysToKeep: number = 30): number {
    const projects = this.getAllProjects()
    const cutoffDate = new Date()
    cutoffDate.setDate(cutoffDate.getDate() - daysToKeep)
    
    const validProjects = projects.filter(project => {
      const lastModified = new Date(project.lastModified)
      return lastModified > cutoffDate
    })
    
    const removedCount = projects.length - validProjects.length
    
    if (removedCount > 0) {
      this.saveProjects(validProjects)
    }
    
    return removedCount
  }
}

export default LocalStorageService