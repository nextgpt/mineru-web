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

// 需求分析相关API
export interface RequirementAnalysis {
  id: number
  project_id: number
  user_id: string
  project_overview?: string
  client_info?: string
  budget_info?: string
  detailed_requirements?: string
  critical_requirements?: string
  important_requirements?: string
  general_requirements?: string
  created_at: string
}

export interface AnalysisResponse {
  status: string
  message: string
  analysis_id?: number
}

export interface AnalysisResultResponse {
  status: string
  message: string
  analysis?: RequirementAnalysis
}

export interface AnalysisStatus {
  project_status: string
  has_analysis: boolean
  analysis_created_at?: string
}

export const analysisApi = {
  // 开始需求分析
  startAnalysis(projectId: number): Promise<AnalysisResponse> {
    return api.post(`/projects/${projectId}/analyze`, {}, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 获取分析结果
  getAnalysisResult(projectId: number): Promise<AnalysisResultResponse> {
    return api.get(`/projects/${projectId}/analysis`, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 获取分析状态
  getAnalysisStatus(projectId: number): Promise<AnalysisStatus> {
    return api.get(`/projects/${projectId}/analysis/status`, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 更新分析结果
  updateAnalysisResult(projectId: number, analysisData: Partial<RequirementAnalysis>): Promise<RequirementAnalysis> {
    return api.put(`/projects/${projectId}/analysis`, analysisData, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  }
}

// 标书大纲相关API
export interface BidOutline {
  id: number
  project_id: number
  user_id: string
  title: string
  level: number
  sequence: string
  parent_id?: number
  order_index: number
  content?: string
  created_at: string
  children?: BidOutline[]
}

export interface OutlineGenerateResponse {
  status: string
  message: string
  outline_count?: number
}

export interface OutlineResponse {
  status: string
  message: string
  outline: BidOutline[]
}

export interface OutlineCreate {
  title: string
  level: number
  parent_id?: number
  content?: string
}

export interface OutlineUpdate {
  title?: string
  content?: string
  order_index?: number
}

export const outlineApi = {
  // 生成标书大纲
  generateOutline(projectId: number): Promise<OutlineGenerateResponse> {
    return api.post(`/projects/${projectId}/generate-outline`, {}, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 获取标书大纲
  getOutline(projectId: number): Promise<OutlineResponse> {
    return api.get(`/projects/${projectId}/outline`, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 创建大纲节点
  createOutlineNode(projectId: number, outlineData: OutlineCreate): Promise<BidOutline> {
    return api.post(`/projects/${projectId}/outline`, outlineData, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 更新大纲节点
  updateOutlineNode(projectId: number, outlineId: number, outlineData: OutlineUpdate): Promise<BidOutline> {
    return api.put(`/projects/${projectId}/outline/${outlineId}`, outlineData, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 删除大纲节点
  deleteOutlineNode(projectId: number, outlineId: number): Promise<void> {
    return api.delete(`/projects/${projectId}/outline/${outlineId}`, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 重新排序大纲
  reorderOutline(projectId: number, outlineOrders: Array<{id: number, order_index: number}>): Promise<void> {
    return api.put(`/projects/${projectId}/outline/reorder`, outlineOrders, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 移动大纲节点
  moveOutlineNode(projectId: number, outlineId: number, moveData: {new_parent_id?: number, new_position: number}): Promise<void> {
    return api.put(`/projects/${projectId}/outline/${outlineId}/move`, moveData, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 复制大纲节点
  copyOutlineNode(projectId: number, outlineId: number, copyData: {target_parent_id?: number}): Promise<{message: string, new_node: BidOutline}> {
    return api.post(`/projects/${projectId}/outline/${outlineId}/copy`, copyData, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 获取大纲统计信息
  getOutlineStatistics(projectId: number): Promise<any> {
    return api.get(`/projects/${projectId}/outline/statistics`, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  }
}

// 标书文档相关API
export interface BidDocument {
  id: number
  project_id: number
  user_id: string
  title: string
  content: string
  outline_id?: number
  status: 'draft' | 'generated' | 'edited' | 'finalized'
  version: number
  created_at: string
  updated_at: string
}

export interface DocumentCreate {
  title: string
  content: string
  outline_id?: number
}

export interface DocumentUpdate {
  title?: string
  content?: string
  status?: string
}

export interface DocumentGenerateRequest {
  outline_id?: number
  regenerate?: boolean
}

export interface DocumentGenerateResponse {
  status: string
  message: string
  document_id?: number
}

export interface DocumentListResponse {
  status: string
  message: string
  documents: BidDocument[]
}

export const documentApi = {
  // 生成标书文档
  generateDocument(projectId: number, generateData?: DocumentGenerateRequest): Promise<DocumentGenerateResponse> {
    return api.post(`/projects/${projectId}/generate-document`, generateData || {}, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 获取标书文档列表
  getDocuments(projectId: number): Promise<DocumentListResponse> {
    return api.get(`/projects/${projectId}/documents`, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 获取单个文档
  getDocument(projectId: number, documentId: number): Promise<BidDocument> {
    return api.get(`/projects/${projectId}/documents/${documentId}`, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 创建文档
  createDocument(projectId: number, documentData: DocumentCreate): Promise<BidDocument> {
    return api.post(`/projects/${projectId}/documents`, documentData, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 更新文档
  updateDocument(projectId: number, documentId: number, documentData: DocumentUpdate): Promise<BidDocument> {
    return api.put(`/projects/${projectId}/documents/${documentId}`, documentData, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 删除文档
  deleteDocument(projectId: number, documentId: number): Promise<void> {
    return api.delete(`/projects/${projectId}/documents/${documentId}`, {
      headers: { 'X-User-Id': getUserId() }
    }).then(response => response.data)
  },

  // 导出文档
  exportDocument(projectId: number, format: 'pdf' | 'docx' | 'md' = 'pdf'): Promise<Blob> {
    return api.get(`/projects/${projectId}/export`, {
      params: { format },
      headers: { 'X-User-Id': getUserId() },
      responseType: 'blob'
    }).then(response => response.data)
  }
}