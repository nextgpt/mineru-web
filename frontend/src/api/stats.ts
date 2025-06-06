import axios from 'axios'
import { getUserId } from '@/utils/user'

const api = axios.create({
  baseURL: '/api',
  timeout: 5000
})

export interface StatsResponse {
  totalFiles: number
  todayUploads: number
  usedSpace: number
  recentFiles: Array<{
    id: string
    name: string
    size: number
    uploadTime: string
    status: string
  }>
}



export const statsApi = {
  getStats(): Promise<StatsResponse> {
    return api.get('/stats', {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  }
} 