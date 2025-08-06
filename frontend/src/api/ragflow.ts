import axios, { type AxiosInstance, AxiosError } from 'axios'
import { config } from '@/config'
import type {
  RAGFlowDataset,
  RAGFlowDocument,
  RAGFlowRetrievalResult,
  RAGFlowCreateDatasetRequest,
  RAGFlowRetrievalRequest,
  APIResponse,
  OutlineStage
} from '@/types/tender'

// 固定的数据集ID
const FIXED_DATASET_ID = '98b0d204727b11f0bf8eeed892cd7f54'

// 操作状态枚举
export enum OperationStatus {
  PENDING = 'pending',
  SUCCESS = 'success',
  ERROR = 'error',
  IN_PROGRESS = 'in_progress'
}

// 操作结果接口
export interface OperationResult<T = any> {
  status: OperationStatus
  message: string
  data?: T
  error?: string
}

// 文件上传进度回调
export interface UploadProgressCallback {
  (progress: number, message: string): void
}

// 解析进度回调
export interface ParseProgressCallback {
  (progress: number, message: string, stage?: string): void
}

class RAGFlowService {
  private client: AxiosInstance
  private retrievalCache: Map<string, { result: RAGFlowRetrievalResult; timestamp: number }> = new Map()
  private readonly CACHE_DURATION = 5 * 60 * 1000 // 5分钟缓存

  constructor() {
    this.client = axios.create({
      baseURL: config.ragflow.baseURL,
      timeout: config.ragflow.timeout,
      headers: {
        'Authorization': `Bearer ${config.ragflow.apiKey}`,
        'Content-Type': 'application/json'
      }
    })

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[RAGFLOW] ${config.method?.toUpperCase()} ${config.url}`)
        return config
      },
      (error) => {
        console.error('[RAGFLOW] Request error:', error)
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => {
        console.log(`[RAGFLOW] Response:`, response.data)
        return response
      },
      (error: AxiosError) => {
        console.error('[RAGFLOW] Response error:', error.response?.data || error.message)
        return Promise.reject(this.handleError(error))
      }
    )
  }

  private handleError(error: AxiosError): Error {
    if (error.response?.data) {
      const apiError = error.response.data as APIResponse
      return new Error(apiError.message || `API Error: ${error.response.status}`)
    }
    return new Error(error.message || 'Network error')
  }

  /**
   * 重试机制包装器
   */
  private async withRetry<T>(
    operation: () => Promise<T>,
    maxAttempts: number = config.app.retryAttempts,
    delay: number = config.app.retryDelay
  ): Promise<T> {
    let lastError: Error

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await operation()
      } catch (error) {
        lastError = error as Error
        console.warn(`[RAGFLOW] Attempt ${attempt}/${maxAttempts} failed:`, error)

        if (attempt === maxAttempts) {
          break
        }

        // 指数退避延迟
        const backoffDelay = delay * Math.pow(2, attempt - 1)
        await new Promise(resolve => setTimeout(resolve, backoffDelay))
      }
    }

    throw lastError!
  }

  /**
   * 完整的文件上传和解析流程
   * 包含所有用户状态反馈
   */
  async uploadAndParseDocument(
    file: File,
    onUploadProgress?: UploadProgressCallback,
    onParseProgress?: ParseProgressCallback
  ): Promise<OperationResult<{ documentId: string; fileName: string }>> {
    try {
      // 步骤1: 上传文件
      onUploadProgress?.(0, '开始上传文件...')

      const uploadResult = await this.uploadDocumentToDataset(file, onUploadProgress)
      if (uploadResult.status !== OperationStatus.SUCCESS) {
        return {
          status: uploadResult.status,
          message: uploadResult.message,
          error: uploadResult.error
        }
      }

      const documentId = uploadResult.data!.id
      const fileName = uploadResult.data!.name

      // 步骤2: 更新文档配置
      onUploadProgress?.(80, '配置文档解析参数...')

      const configResult = await this.updateDocumentConfiguration(documentId, fileName)
      if (configResult.status !== OperationStatus.SUCCESS) {
        return {
          status: OperationStatus.ERROR,
          message: '配置文档参数失败',
          error: configResult.error
        }
      }

      // 步骤3: 触发解析
      onUploadProgress?.(90, '启动文档解析...')
      onParseProgress?.(0, '开始解析文档内容...')

      const parseResult = await this.startDocumentParsing(documentId, onParseProgress)
      if (parseResult.status !== OperationStatus.SUCCESS) {
        return {
          status: parseResult.status,
          message: parseResult.message,
          error: parseResult.error
        }
      }

      onUploadProgress?.(100, '文件上传和解析完成')

      return {
        status: OperationStatus.SUCCESS,
        message: '文件上传和解析成功完成',
        data: { documentId, fileName }
      }

    } catch (error) {
      console.error('[RAGFLOW] Upload and parse failed:', error)
      return {
        status: OperationStatus.ERROR,
        message: '文件上传和解析过程中发生错误',
        error: (error as Error).message
      }
    }
  }

  /**
   * 上传文档到固定数据集
   */
  private async uploadDocumentToDataset(
    file: File,
    onProgress?: UploadProgressCallback
  ): Promise<OperationResult<RAGFlowDocument>> {
    try {
      onProgress?.(10, `正在上传文件: ${file.name}`)

      const formData = new FormData()
      formData.append('file', file)

      const response = await this.client.post<APIResponse<RAGFlowDocument[]>>(
        `/api/v1/datasets/${FIXED_DATASET_ID}/documents`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 120000, // 2分钟超时
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const progress = Math.round((progressEvent.loaded * 70) / progressEvent.total) + 10
              onProgress?.(progress, `上传进度: ${progress}%`)
            }
          }
        }
      )

      if (response.data.code !== 0) {
        return {
          status: OperationStatus.ERROR,
          message: '文件上传失败',
          error: response.data.message || 'Upload failed'
        }
      }

      if (!response.data.data || response.data.data.length === 0) {
        return {
          status: OperationStatus.ERROR,
          message: '上传响应数据异常',
          error: 'No document returned from upload'
        }
      }

      const document = response.data.data[0]
      onProgress?.(80, `文件上传成功: ${document.name}`)

      return {
        status: OperationStatus.SUCCESS,
        message: '文件上传成功',
        data: document
      }

    } catch (error) {
      console.error('[RAGFLOW] Upload failed:', error)
      return {
        status: OperationStatus.ERROR,
        message: '文件上传失败',
        error: (error as Error).message
      }
    }
  }

  /**
   * 更新文档配置
   */
  private async updateDocumentConfiguration(
    documentId: string,
    fileName: string
  ): Promise<OperationResult<void>> {
    try {
      const { chunkMethod, parserConfig } = this.getConfigForFile(fileName)

      const updateData = {
        chunk_method: chunkMethod,
        parser_config: parserConfig
      }

      console.log('[RAGFLOW] Updating document config for', fileName, ':', updateData)

      const response = await this.client.put<APIResponse>(
        `/api/v1/datasets/${FIXED_DATASET_ID}/documents/${documentId}`,
        updateData
      )

      if (response.data.code !== 0) {
        return {
          status: OperationStatus.ERROR,
          message: '更新文档配置失败',
          error: response.data.message || 'Failed to update document config'
        }
      }

      const configType = this.isPdfFile(fileName) ? 'PDF(DeepDoc+分页)' :
        this.isWordFile(fileName) ? 'Word(Book)' : 'Book'

      return {
        status: OperationStatus.SUCCESS,
        message: `文档配置更新成功: ${configType}`
      }

    } catch (error) {
      console.error('[RAGFLOW] Config update failed:', error)
      return {
        status: OperationStatus.ERROR,
        message: '更新文档配置失败',
        error: (error as Error).message
      }
    }
  }

  /**
   * 启动文档解析
   */
  private async startDocumentParsing(
    documentId: string,
    onProgress?: ParseProgressCallback
  ): Promise<OperationResult<void>> {
    try {
      // 启动解析
      const response = await this.client.post<APIResponse>(
        `/api/v1/datasets/${FIXED_DATASET_ID}/chunks`,
        { document_ids: [documentId] }
      )

      if (response.data.code !== 0) {
        return {
          status: OperationStatus.ERROR,
          message: '启动文档解析失败',
          error: response.data.message || 'Failed to start parsing'
        }
      }

      onProgress?.(10, '解析任务已提交，开始处理...')

      // 监控解析进度
      const monitorResult = await this.monitorParsingProgress(documentId, onProgress)
      return monitorResult

    } catch (error) {
      console.error('[RAGFLOW] Parse start failed:', error)
      return {
        status: OperationStatus.ERROR,
        message: '启动文档解析失败',
        error: (error as Error).message
      }
    }
  }

  /**
   * 监控解析进度
   */
  private async monitorParsingProgress(
    documentId: string,
    onProgress?: ParseProgressCallback
  ): Promise<OperationResult<void>> {
    const maxWaitTime = 300000 // 5分钟超时
    const checkInterval = 3000 // 3秒检查一次
    const startTime = Date.now()
    let lastProgress = 0

    while (Date.now() - startTime < maxWaitTime) {
      try {
        const status = await this.checkDocumentParsingStatus(documentId)

        // 更新进度
        if (status.progress > lastProgress) {
          lastProgress = status.progress
          const stage = this.getParsingStage(status.progress)
          onProgress?.(status.progress, `解析进度: ${Math.round(status.progress)}%`, stage)
        }

        // 检查完成状态
        if (status.status === 'DONE' || status.status === '1') {
          onProgress?.(100, `解析完成！共生成 ${status.chunkCount} 个文档片段`)
          return {
            status: OperationStatus.SUCCESS,
            message: `文档解析完成，生成 ${status.chunkCount} 个片段`
          }
        }

        // 检查失败状态
        if (status.status === 'FAIL' || status.status === '-1') {
          return {
            status: OperationStatus.ERROR,
            message: '文档解析失败',
            error: '解析过程中发生错误，请检查文档格式'
          }
        }

        // 等待下次检查
        await new Promise(resolve => setTimeout(resolve, checkInterval))

      } catch (error) {
        console.error('[RAGFLOW] Progress check failed:', error)
        return {
          status: OperationStatus.ERROR,
          message: '监控解析进度失败',
          error: (error as Error).message
        }
      }
    }

    return {
      status: OperationStatus.ERROR,
      message: '文档解析超时',
      error: '解析时间超过5分钟，请重试或联系管理员'
    }
  }

  /**
   * 根据进度获取解析阶段描述
   */
  private getParsingStage(progress: number): string {
    if (progress < 20) return 'OCR识别'
    if (progress < 40) return '布局分析'
    if (progress < 60) return '表格分析'
    if (progress < 80) return '文本提取'
    if (progress < 95) return '生成片段'
    return '索引构建'
  }

  /**
   * 检索内容（带缓存机制）
   */
  async retrieveContent(datasetId: string, question: string): Promise<RAGFlowRetrievalResult> {
    // 生成缓存键
    const cacheKey = `${datasetId}:${question}`
    const cached = this.retrievalCache.get(cacheKey)

    // 检查缓存是否有效
    if (cached && Date.now() - cached.timestamp < this.CACHE_DURATION) {
      console.log('[RAGFLOW] Using cached retrieval result')
      return cached.result
    }

    return this.withRetry(async () => {
      const request: RAGFlowRetrievalRequest = {
        question,
        dataset_ids: [datasetId],
        similarity_threshold: config.ragflow.defaultSimilarityThreshold,
        top_k: 10 // 增加检索结果数量
      }

      const response = await this.client.post<APIResponse<RAGFlowRetrievalResult>>(
        '/api/v1/retrieval',
        request
      )

      if (response.data.code !== 0) {
        throw new Error(response.data.message || 'Failed to retrieve content')
      }

      const result = response.data.data!

      // 缓存结果
      this.retrievalCache.set(cacheKey, {
        result,
        timestamp: Date.now()
      })

      return result
    })
  }

  /**
   * 五阶段大纲生成检索逻辑
   */
  async generateOutlineStages(
    datasetId: string,
    onStageProgress?: (stage: OutlineStage) => void
  ): Promise<OutlineStage[]> {
    const stages: OutlineStage[] = config.outlinePrompts.map(prompt => ({
      ...prompt,
      result: '',
      status: 'pending' as const
    }))

    for (let i = 0; i < stages.length; i++) {
      const stage = stages[i]

      try {
        // 更新阶段状态为处理中
        stage.status = 'processing'
        stage.startTime = Date.now()
        onStageProgress?.(stage)

        // 执行检索
        const retrievalResult = await this.retrieveContent(datasetId, stage.prompt)

        // 整合检索结果
        stage.result = this.formatRetrievalResult(retrievalResult)
        stage.status = 'completed'
        stage.endTime = Date.now()

        onStageProgress?.(stage)

        console.log(`[RAGFLOW] Stage ${stage.id} completed:`, stage.result.substring(0, 200) + '...')

      } catch (error) {
        stage.status = 'error'
        stage.error = (error as Error).message
        stage.endTime = Date.now()

        onStageProgress?.(stage)

        console.error(`[RAGFLOW] Stage ${stage.id} failed:`, error)
        throw error
      }
    }

    return stages
  }

  /**
   * 格式化检索结果
   */
  private formatRetrievalResult(result: RAGFlowRetrievalResult): string {
    if (!result.chunks || result.chunks.length === 0) {
      return '未找到相关内容'
    }

    return result.chunks
      .sort((a, b) => b.similarity - a.similarity) // 按相似度排序
      .slice(0, 5) // 取前5个最相关的结果
      .map((chunk, index) => `${index + 1}. ${chunk.content}`)
      .join('\n\n')
  }

  /**
   * 清除检索缓存
   */
  clearRetrievalCache(): void {
    this.retrievalCache.clear()
    console.log('[RAGFLOW] Retrieval cache cleared')
  }

  /**
   * 获取缓存统计信息
   */
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.retrievalCache.size,
      keys: Array.from(this.retrievalCache.keys())
    }
  }

  /**
   * 验证和修复RAGFLOW配置（用于数据集创建）
   */
  private validateParserConfig(config: any): any {
    // 数据集创建时使用book方法的基础配置
    const validConfig = {
      raptor: config.raptor ?? { use_raptor: false }
    }

    console.log('[RAGFLOW] Validated parser config for dataset creation (book method):', validConfig)
    return validConfig
  }

  /**
   * 创建带有验证配置的数据集
   */
  async createDatasetWithValidatedConfig(name: string, customConfig?: any): Promise<RAGFlowDataset> {
    return this.withRetry(async () => {
      const baseConfig = { ...config.ragflow.defaultParserConfig }
      const mergedConfig = customConfig ? { ...baseConfig, ...customConfig } : baseConfig
      const validatedConfig = this.validateParserConfig(mergedConfig)

      const request: RAGFlowCreateDatasetRequest = {
        name,
        chunk_method: 'book', // 统一使用book方法
        parser_config: validatedConfig
      }

      console.log('[RAGFLOW] Creating dataset with validated config:', request)

      const response = await this.client.post<APIResponse<RAGFlowDataset>>('/api/v1/datasets', request)

      if (response.data.code !== 0) {
        throw new Error(response.data.message || 'Failed to create dataset')
      }

      return response.data.data!
    })
  }

  /**
   * 检查文档解析状态
   */
  private async checkDocumentParsingStatus(documentId: string): Promise<{
    status: string;
    progress: number;
    chunkCount: number;
  }> {
    const response = await this.client.get<APIResponse<{ docs: RAGFlowDocument[], total: number }>>(
      `/api/v1/datasets/${FIXED_DATASET_ID}/documents?id=${documentId}`
    )

    if (response.data.code !== 0) {
      throw new Error(response.data.message || 'Failed to check document status')
    }

    const document = response.data.data!.docs[0]
    if (!document) {
      throw new Error('Document not found')
    }

    return {
      status: document.run || 'UNSTART',
      progress: (document as any).progress || 0,
      chunkCount: (document as any).chunk_count || 0
    }
  }





  /**
   * 检查是否为PDF文件
   */
  private isPdfFile(fileName: string): boolean {
    return fileName.toLowerCase().endsWith('.pdf')
  }

  /**
   * 检查是否为Word文档
   */
  private isWordFile(fileName: string): boolean {
    return /\.(doc|docx)$/i.test(fileName.toLowerCase())
  }

  /**
   * 根据文件类型获取解析配置和方法
   */
  private getConfigForFile(fileName: string): { chunkMethod: string; parserConfig: any } {
    if (this.isPdfFile(fileName)) {
      // PDF文件：使用book方法 + DeepDoc解析器 + 分页设置
      return {
        chunkMethod: 'book',
        parserConfig: {
          layout_recognize: 'DeepDoc', // PDF使用DeepDoc解析器
          task_page_size: 12, // PDF分页解析
          raptor: { use_raptor: false }
        }
      }
    } else if (this.isWordFile(fileName)) {
      // DOC/DOCX文件：使用book方法
      return {
        chunkMethod: 'book',
        parserConfig: {
          raptor: { use_raptor: false }
        }
      }
    } else {
      // 其他文件类型使用book方法
      return {
        chunkMethod: 'book',
        parserConfig: {
          raptor: { use_raptor: false }
        }
      }
    }
  }

  /**
   * 更新文档的parser_config配置
   */
  async updateDocumentParserConfig(datasetId: string, documentId: string, fileName: string): Promise<void> {
    return this.withRetry(async () => {
      // 根据文件类型获取相应的解析配置和方法
      const { chunkMethod, parserConfig } = this.getConfigForFile(fileName)

      const updateData = {
        chunk_method: chunkMethod,
        parser_config: parserConfig
      }

      console.log('[RAGFLOW] Updating document config for', fileName, ':', updateData)

      const response = await this.client.put<APIResponse>(
        `/api/v1/datasets/${datasetId}/documents/${documentId}`,
        updateData
      )

      if (response.data.code !== 0) {
        throw new Error(response.data.message || 'Failed to update document parser config')
      }

      if (this.isPdfFile(fileName)) {
        console.log('[RAGFLOW] PDF document updated: chunk_method=book, layout_recognize=DeepDoc, task_page_size=12')
      } else if (this.isWordFile(fileName)) {
        console.log('[RAGFLOW] Word document updated: chunk_method=book')
      } else {
        console.log('[RAGFLOW] Document updated with book method')
      }
    })
  }
  /**
   * 获取文档列表（用于调试和管理）
   */
  async getDocuments(page = 1, pageSize = 30): Promise<OperationResult<{ documents: RAGFlowDocument[], total: number }>> {
    try {
      const response = await this.client.get<APIResponse<{ docs: RAGFlowDocument[], total: number }>>(
        `/api/v1/datasets/${FIXED_DATASET_ID}/documents?page=${page}&page_size=${pageSize}`
      )

      if (response.data.code !== 0) {
        return {
          status: OperationStatus.ERROR,
          message: '获取文档列表失败',
          error: response.data.message || 'Failed to get documents'
        }
      }

      return {
        status: OperationStatus.SUCCESS,
        message: '获取文档列表成功',
        data: {
          documents: response.data.data!.docs,
          total: response.data.data!.total
        }
      }
    } catch (error) {
      return {
        status: OperationStatus.ERROR,
        message: '获取文档列表失败',
        error: (error as Error).message
      }
    }
  }

  /**
   * 删除文档
   */
  async deleteDocument(documentId: string): Promise<OperationResult<void>> {
    try {
      const response = await this.client.delete<APIResponse>(
        `/api/v1/datasets/${FIXED_DATASET_ID}/documents`,
        { data: { ids: [documentId] } }
      )

      if (response.data.code !== 0) {
        return {
          status: OperationStatus.ERROR,
          message: '删除文档失败',
          error: response.data.message || 'Failed to delete document'
        }
      }

      return {
        status: OperationStatus.SUCCESS,
        message: '文档删除成功'
      }
    } catch (error) {
      return {
        status: OperationStatus.ERROR,
        message: '删除文档失败',
        error: (error as Error).message
      }
    }
  }

  /**
   * 使用固定数据集进行内容检索
   */
  async retrieveFromFixedDataset(question: string): Promise<OperationResult<RAGFlowRetrievalResult>> {
    try {
      const result = await this.retrieveContent(FIXED_DATASET_ID, question)
      return {
        status: OperationStatus.SUCCESS,
        message: '内容检索成功',
        data: result
      }
    } catch (error) {
      return {
        status: OperationStatus.ERROR,
        message: '内容检索失败',
        error: (error as Error).message
      }
    }
  }

  /**
   * 获取固定数据集ID
   */
  getFixedDatasetId(): string {
    return FIXED_DATASET_ID
  }

  // 向后兼容的方法
  /**
   * @deprecated 使用 uploadAndParseDocument 替代
   */
  async createDataset(name: string): Promise<any> {
    console.warn('createDataset is deprecated, using fixed dataset instead')
    return { id: FIXED_DATASET_ID, name }
  }

  /**
   * @deprecated 使用 uploadAndParseDocument 替代
   */
  async uploadDocument(_datasetId: string, file: File): Promise<any> {
    console.warn('uploadDocument is deprecated, use uploadAndParseDocument instead')
    const result = await this.uploadDocumentToDataset(file)
    if (result.status === OperationStatus.SUCCESS) {
      return result.data
    }
    throw new Error(result.message)
  }

  /**
   * @deprecated 使用 uploadAndParseDocument 替代
   */
  async parseDocument(_datasetId: string, _documentIds: string[]): Promise<void> {
    console.warn('parseDocument is deprecated, parsing is handled automatically')
    // 空实现，因为解析现在是自动的
  }

  /**
   * @deprecated 使用新的架构替代
   */
  async getDatasets(_page = 1, _pageSize = 30): Promise<{ datasets: any[], total: number }> {
    console.warn('getDatasets is deprecated')
    return { datasets: [], total: 0 }
  }

  /**
   * @deprecated 使用新的架构替代
   */
  async deleteDataset(_datasetId: string): Promise<void> {
    console.warn('deleteDataset is deprecated')
  }

  /**
   * @deprecated 使用新的架构替代
   */
  async waitForDocumentParsing(
    _datasetId: string,
    _documentId: string,
    _onProgress?: (progress: number, details?: string) => void,
    _onStageChange?: (stage: number, stageName: string) => void
  ): Promise<void> {
    console.warn('waitForDocumentParsing is deprecated, use uploadAndParseDocument instead')
  }

  /**
   * @deprecated 使用新的架构替代
   */
  async retryDocumentParsing(_datasetId: string, _documentId: string): Promise<void> {
    console.warn('retryDocumentParsing is deprecated')
  }

  /**
   * @deprecated 使用新的架构替代
   */
  async getParsingNotification(_datasetId: string, _documentId: string): Promise<{
    isCompleted: boolean;
    progress: number;
    message: string;
    chunkCount?: number;
  }> {
    console.warn('getParsingNotification is deprecated')
    return {
      isCompleted: true,
      progress: 100,
      message: 'Deprecated method',
      chunkCount: 0
    }
  }
}

// 导出单例实例
export const ragflowService = new RAGFlowService()
export default ragflowService