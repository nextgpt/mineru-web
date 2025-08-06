// 招标文件智能生成标书系统类型定义

// 项目状态枚举
export type ProjectStatus = 'uploading' | 'parsing' | 'ready' | 'generating' | 'completed' | 'error'

// 视图模式枚举
export type ViewMode = 'card' | 'list'

// 右侧面板模式枚举
export type RightPanelMode = 'settings' | 'outline' | 'content'

// 生成设置
export interface GenerationSettings {
  length: 'short' | 'medium' | 'medium-long' | 'long' | 'extra-long'
  quality: 'expert' | 'standard'
  includeImages: boolean
  imageQuality: 'standard' | 'high'
  includeTables: boolean
  tableStyle: 'simple' | 'professional'
}

// 分页信息
export interface PaginationInfo {
  page: number
  pageSize: number
  total: number
}

// 招标项目数据模型
export interface TenderProject {
  id: string
  name: string
  fileName: string
  fileSize: number
  uploadTime: string
  status: ProjectStatus
  datasetId?: string
  documentId?: string
  settings?: GenerationSettings
  outline?: string
  content?: string
  lastModified: string
}

// RAGFLOW API 相关类型定义
export interface RAGFlowDataset {
  id: string
  name: string
  chunk_method: string
  status: string
  create_time: number
  chunk_count: number
  document_count: number
  embedding_model: string
  parser_config: {
    chunk_token_num: number
    delimiter: string
    html4excel: boolean
    layout_recognize: string
    raptor: {
      use_raptor: boolean
    }
  }
}

export interface RAGFlowDocument {
  id: string
  name: string
  dataset_id: string
  size: number
  run: string
  chunk_method: string
  parser_config: {
    chunk_token_num: number
    delimiter: string
    layout_recognize: boolean
    task_page_size: number
  }
  type: string
  location: string
  created_by: string
}

export interface RAGFlowChunk {
  content: string
  similarity: number
  document_id: string
}

export interface RAGFlowRetrievalResult {
  chunks: RAGFlowChunk[]
  total: number
}

export interface RAGFlowCreateDatasetRequest {
  name: string
  chunk_method: 'naive' | 'book'
  parser_config?: {
    raptor: {
      use_raptor: boolean
    }
    filename_embd_weight?: number
    auto_keywords?: number
    chunk_token_num?: number
    delimiter?: string
    html4excel?: boolean
    layout_recognize?: string
    task_page_size?: number
  }
}

export interface RAGFlowUploadDocumentRequest {
  dataset_id: string
  file: File
}

export interface RAGFlowParseDocumentRequest {
  dataset_id: string
  document_ids: string[]
}

export interface RAGFlowRetrievalRequest {
  question: string
  dataset_ids: string[]
  similarity_threshold: number
  top_k?: number
}

// RAGFLOW API 响应包装类型
export interface RAGFlowAPIResponse<T = any> {
  code: number
  data?: T
  message?: string
}

// DeepSeek API 相关类型定义
export interface DeepSeekChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface DeepSeekChatRequest {
  model: string
  messages: DeepSeekChatMessage[]
  max_tokens: number
  temperature: number
  stream?: boolean
  top_p?: number
  frequency_penalty?: number
  presence_penalty?: number
}

export interface DeepSeekChatResponse {
  id: string
  object: string
  created: number
  model: string
  choices: Array<{
    index: number
    message: {
      role: string
      content: string
    }
    finish_reason: string
  }>
  usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}

// DeepSeek 流式响应类型
export interface DeepSeekStreamChunk {
  id: string
  object: string
  created: number
  model: string
  choices: Array<{
    index: number
    delta: {
      role?: string
      content?: string
    }
    finish_reason?: string
  }>
}

// 大纲生成阶段
export interface OutlineStage {
  id: number
  title: string
  prompt: string
  result: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  startTime?: number
  endTime?: number
  error?: string
}

// 大纲生成状态
export interface OutlineGenerationState {
  currentStage: number
  stages: OutlineStage[]
  isGenerating: boolean
  finalOutline: string
  error?: string
}

// API 响应基础类型
export interface APIResponse<T = any> {
  code: number
  data?: T
  message?: string
}

// 错误类型
export interface APIError {
  code: number
  message: string
  details?: any
}

// 文件上传状态
export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
}

// 内容生成进度
export interface GenerationProgress {
  currentChunk: number
  totalChunks: number
  percentage: number
  currentContent: string
}

// 系统信息
export interface SystemInfo {
  title: string
  description: string
  features: string[]
}

// 项目管理状态
export interface ProjectManagerState {
  projects: TenderProject[]
  viewMode: ViewMode
  loading: boolean
  pagination: PaginationInfo
  searchKeyword: string
  selectedProject?: TenderProject
}

// 文档预览状态
export interface DocumentPreviewState {
  currentProject: TenderProject
  originalContent: string
  rightPanelMode: RightPanelMode
  settings: GenerationSettings
  loading: boolean
}

// 内容编辑状态
export interface ContentEditorState {
  content: string
  isDirty: boolean
  autoSaveTimer: number | null
  lastSaved?: number
}

// 本地存储键名常量
export const STORAGE_KEYS = {
  PROJECTS: 'tender_projects',
  SETTINGS: 'tender_settings',
  USER_PREFERENCES: 'user_preferences'
} as const

// 用户偏好设置
export interface UserPreferences {
  viewMode: ViewMode
  autoSave: boolean
  autoSaveInterval: number // 秒
  theme: 'light' | 'dark'
}

// 操作结果类型
export interface OperationResult<T = any> {
  success: boolean
  data?: T
  error?: string
}

// 文件验证结果
export interface FileValidationResult {
  valid: boolean
  error?: string
  warnings?: string[]
}