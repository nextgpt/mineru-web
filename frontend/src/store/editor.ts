import { defineStore } from 'pinia'
import { type ContentEditorState, type UserPreferences } from '@/types/tender'
import { LocalStorageService } from '@/utils/storage'

export const useEditorStore = defineStore('editor', {
  state: (): ContentEditorState => ({
    content: '',
    isDirty: false,
    autoSaveTimer: null,
    lastSaved: undefined
  }),

  getters: {
    // 是否有未保存的更改
    hasUnsavedChanges: (state) => state.isDirty,

    // 最后保存时间的格式化显示
    lastSavedText: (state) => {
      if (!state.lastSaved) return '从未保存'
      
      const now = Date.now()
      const diff = now - state.lastSaved
      
      if (diff < 60000) { // 小于1分钟
        return '刚刚保存'
      } else if (diff < 3600000) { // 小于1小时
        const minutes = Math.floor(diff / 60000)
        return `${minutes}分钟前保存`
      } else if (diff < 86400000) { // 小于1天
        const hours = Math.floor(diff / 3600000)
        return `${hours}小时前保存`
      } else {
        return new Date(state.lastSaved).toLocaleString()
      }
    },

    // 内容字数统计
    contentStats: (state) => {
      const content = state.content || ''
      const characters = content.length
      const charactersNoSpaces = content.replace(/\s/g, '').length
      const words = content.trim() ? content.trim().split(/\s+/).length : 0
      const lines = content.split('\n').length
      const paragraphs = content.split(/\n\s*\n/).filter(p => p.trim()).length

      return {
        characters,
        charactersNoSpaces,
        words,
        lines,
        paragraphs
      }
    }
  },

  actions: {
    // 设置内容
    setContent(content: string, markDirty: boolean = true) {
      this.content = content
      if (markDirty) {
        this.markDirty()
      }
    },

    // 标记为已修改
    markDirty() {
      this.isDirty = true
      this.scheduleAutoSave()
    },

    // 标记为已保存
    markSaved() {
      this.isDirty = false
      this.lastSaved = Date.now()
      this.clearAutoSaveTimer()
    },

    // 手动保存
    async save(projectId?: string): Promise<{ success: boolean; message: string }> {
      try {
        // 如果提供了项目ID，保存到对应项目
        if (projectId) {
          LocalStorageService.updateProject(projectId, {
            content: this.content
          })
        }

        // 保存到临时存储（用于恢复未保存的内容）
        LocalStorageService.saveSettings({
          editorContent: {
            content: this.content,
            timestamp: Date.now(),
            projectId
          }
        })

        this.markSaved()
        return { success: true, message: '保存成功' }
      } catch (error) {
        console.error('Save failed:', error)
        return { 
          success: false, 
          message: error instanceof Error ? error.message : '保存失败' 
        }
      }
    },

    // 自动保存
    async autoSave(projectId?: string) {
      if (!this.isDirty) return

      try {
        await this.save(projectId)
      } catch (error) {
        console.error('Auto save failed:', error)
      }
    },

    // 安排自动保存
    scheduleAutoSave(projectId?: string) {
      this.clearAutoSaveTimer()
      
      // 获取自动保存间隔设置
      const preferences = LocalStorageService.getSetting<UserPreferences>('userPreferences', {
        viewMode: 'card',
        autoSave: true,
        autoSaveInterval: 30,
        theme: 'light'
      })

      if (preferences.autoSave) {
        this.autoSaveTimer = window.setTimeout(() => {
          this.autoSave(projectId)
        }, preferences.autoSaveInterval * 1000)
      }
    },

    // 清除自动保存定时器
    clearAutoSaveTimer() {
      if (this.autoSaveTimer) {
        clearTimeout(this.autoSaveTimer)
        this.autoSaveTimer = null
      }
    },

    // 插入文本到光标位置
    insertText(text: string, cursorPosition?: number) {
      const content = this.content
      const position = cursorPosition ?? content.length
      
      const newContent = content.slice(0, position) + text + content.slice(position)
      this.setContent(newContent)
      
      return position + text.length // 返回新的光标位置
    },

    // 替换选中的文本
    replaceSelection(newText: string, startPosition: number, endPosition: number) {
      const content = this.content
      const newContent = content.slice(0, startPosition) + newText + content.slice(endPosition)
      this.setContent(newContent)
      
      return startPosition + newText.length // 返回新的光标位置
    },

    // 查找文本
    findText(searchText: string, caseSensitive: boolean = false): number[] {
      const content = caseSensitive ? this.content : this.content.toLowerCase()
      const search = caseSensitive ? searchText : searchText.toLowerCase()
      
      const positions: number[] = []
      let index = content.indexOf(search)
      
      while (index !== -1) {
        positions.push(index)
        index = content.indexOf(search, index + 1)
      }
      
      return positions
    },

    // 替换文本
    replaceText(searchText: string, replaceText: string, replaceAll: boolean = false, caseSensitive: boolean = false): number {
      let content = this.content
      const search = caseSensitive ? searchText : searchText.toLowerCase()
      let replaceCount = 0

      if (replaceAll) {
        // 全部替换
        const regex = new RegExp(
          searchText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 
          caseSensitive ? 'g' : 'gi'
        )
        content = content.replace(regex, () => {
          replaceCount++
          return replaceText
        })
      } else {
        // 替换第一个
        const searchContent = caseSensitive ? content : content.toLowerCase()
        const index = searchContent.indexOf(search)
        if (index !== -1) {
          content = content.slice(0, index) + replaceText + content.slice(index + searchText.length)
          replaceCount = 1
        }
      }

      if (replaceCount > 0) {
        this.setContent(content)
      }

      return replaceCount
    },

    // 加载项目内容
    loadProjectContent(projectId: string) {
      const project = LocalStorageService.getProject(projectId)
      if (project && project.content) {
        this.setContent(project.content, false) // 不标记为脏数据
        this.markSaved()
      } else {
        this.setContent('', false)
      }
    },

    // 恢复未保存的内容
    restoreUnsavedContent(): boolean {
      const settings = LocalStorageService.getSettings()
      const editorContent = settings.editorContent
      
      if (editorContent && editorContent.content) {
        // 检查是否是最近的内容（24小时内）
        const now = Date.now()
        const contentAge = now - (editorContent.timestamp || 0)
        
        if (contentAge < 24 * 60 * 60 * 1000) { // 24小时
          this.setContent(editorContent.content, true)
          return true
        }
      }
      
      return false
    },

    // 清除临时保存的内容
    clearTempContent() {
      const settings = LocalStorageService.getSettings()
      delete settings.editorContent
      LocalStorageService.saveSettings(settings)
    },

    // 重置编辑器状态
    reset() {
      this.clearAutoSaveTimer()
      this.content = ''
      this.isDirty = false
      this.lastSaved = undefined
    },

    // 导出内容
    exportContent(format: 'txt' | 'md' | 'html' = 'txt'): string {
      switch (format) {
        case 'md':
          return this.content // Markdown格式直接返回
        case 'html':
          // 简单的Markdown到HTML转换（实际项目中可能需要使用专门的库）
          return this.content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
        case 'txt':
        default:
          return this.content
      }
    },

    // 导入内容
    importContent(content: string, format: 'txt' | 'md' | 'html' = 'txt') {
      let processedContent = content

      if (format === 'html') {
        // 简单的HTML到文本转换
        processedContent = content
          .replace(/<br\s*\/?>/gi, '\n')
          .replace(/<strong>(.*?)<\/strong>/gi, '**$1**')
          .replace(/<em>(.*?)<\/em>/gi, '*$1*')
          .replace(/<[^>]*>/g, '') // 移除其他HTML标签
      }

      this.setContent(processedContent)
    },

    // 获取编辑历史统计
    getEditingStats() {
      return {
        contentStats: this.contentStats,
        lastSaved: this.lastSaved,
        isDirty: this.isDirty,
        hasAutoSave: this.autoSaveTimer !== null
      }
    }
  }
})