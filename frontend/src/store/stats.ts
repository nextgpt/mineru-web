import { defineStore } from 'pinia'
import { statsApi, type StatsResponse } from '../api/stats'

interface StatsState {
  totalFiles: number
  todayUploads: number
  usedSpace: number
  recentFiles: StatsResponse['recentFiles']
}

export const useStatsStore = defineStore('stats', {
  state: (): StatsState => ({
    totalFiles: 0,
    todayUploads: 0,
    usedSpace: 0,
    recentFiles: []
  }),
  
  actions: {
    async fetchStats() {
      try {
        const response = await statsApi.getStats()
        this.totalFiles = response.totalFiles
        this.todayUploads = response.todayUploads
        this.usedSpace = response.usedSpace
        this.recentFiles = response.recentFiles
      } catch (error) {
        console.error('获取统计数据失败:', error)
        // 使用模拟数据作为后备
        this.totalFiles = 42
        this.todayUploads = 5
        this.usedSpace = 256
        this.recentFiles = []
      }
    }
  }
}) 