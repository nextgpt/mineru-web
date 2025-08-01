import axios from 'axios'
import { getUserId } from '@/utils/user'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

export interface Project {
  id: number
  user_id: string
  name: string
  description?: string
  status: 'created' | 'parsing' | 'analyzing' | 'outline_generated' | 'document_generating' | 'completed' | 'failed'
  original_file_id?: number
  created_at: string
  updated_at: string
  original_file?: {
    id: number
    filename: string
    size: number
    status: string
  }
}

export interface CreateProjectRequest {
  name: string
  description?: string
}

export interface ProjectListResponse {
  projects: Project[]
  total: number
  page: number
  page_size: number
}

export const projectsApi = {
  // 获取项目列表
  getProjects(page: number = 1, pageSize: number = 10, search?: string): Promise<ProjectListResponse> {
    const params: any = { page, page_size: pageSize }
    if (search) {
      params.search = search
    }
    return api.get('/projects', {
      params,
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 创建项目
  createProject(data: CreateProjectRequest): Promise<Project> {
    return api.post('/projects', data, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 获取项目详情
  getProject(id: number): Promise<Project> {
    return api.get(`/projects/${id}`, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 更新项目
  updateProject(id: number, data: Partial<CreateProjectRequest>): Promise<Project> {
    return api.put(`/projects/${id}`, data, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 删除项目
  deleteProject(id: number): Promise<void> {
    return api.delete(`/projects/${id}`, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 上传招标文件到项目
  uploadTenderFile(projectId: number, file: File, onProgress?: (progress: number) => void): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    
    return api.post(`/projects/${projectId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'X-User-Id': getUserId()
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    }).then(response => response.data)
  }
}