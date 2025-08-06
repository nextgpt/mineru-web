// API服务统一导出

export { default as ragflowService } from './ragflow'
export { default as deepseekService } from './deepseek'
export { statsApi } from './stats'

// 重新导出类型
export type {
  RAGFlowDataset,
  RAGFlowDocument,
  RAGFlowRetrievalResult,
  RAGFlowCreateDatasetRequest,
  RAGFlowRetrievalRequest,
  DeepSeekChatMessage,
  DeepSeekChatRequest,
  DeepSeekChatResponse,
  TenderProject,
  GenerationSettings,
  ProjectStatus,
  OutlineStage,
  APIResponse,
  APIError
} from '@/types/tender'

// 导出工具函数
export {
  APIErrorHandler,
  UploadErrorHandler,
  RetryHandler,
  debounce,
  throttle,
  formatFileSize,
  formatTime,
  generateId,
  deepClone
} from '@/utils/api'

// 导出存储服务
export { default as LocalStorageService } from '@/utils/storage'