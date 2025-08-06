import axios, { type AxiosInstance, AxiosError } from 'axios'
import { config } from '@/config'
import type {
  DeepSeekChatMessage,
  DeepSeekChatRequest,
  DeepSeekChatResponse,
  GenerationSettings
} from '@/types/tender'

class DeepSeekService {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: config.deepseek.baseURL,
      timeout: config.deepseek.timeout,
      headers: {
        'Authorization': `Bearer ${config.deepseek.apiKey}`,
        'Content-Type': 'application/json'
      }
    })

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[DeepSeek] ${config.method?.toUpperCase()} ${config.url}`)
        return config
      },
      (error) => {
        console.error('[DeepSeek] Request error:', error)
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => {
        console.log(`[DeepSeek] Response received`)
        return response
      },
      (error: AxiosError) => {
        console.error('[DeepSeek] Response error:', error.response?.data || error.message)
        return Promise.reject(this.handleError(error))
      }
    )
  }

  private handleError(error: AxiosError): Error {
    if (error.response?.data) {
      const apiError = error.response.data as any
      return new Error(apiError.error?.message || apiError.message || `API Error: ${error.response.status}`)
    }
    return new Error(error.message || 'Network error')
  }

  /**
   * 生成聊天完成
   */
  async createChatCompletion(messages: DeepSeekChatMessage[], options?: {
    maxTokens?: number
    temperature?: number
    stream?: boolean
  }): Promise<DeepSeekChatResponse> {
    const request: DeepSeekChatRequest = {
      model: config.deepseek.model,
      messages,
      max_tokens: options?.maxTokens || config.deepseek.maxTokens,
      temperature: options?.temperature || config.deepseek.temperature,
      stream: options?.stream || false
    }

    const response = await this.client.post<DeepSeekChatResponse>('/v1/chat/completions', request)
    return response.data
  }

  /**
   * 生成标书内容
   */
  async generateContent(outline: string, settings: GenerationSettings): Promise<string> {
    // 根据设置调整生成参数
    const maxTokens = this.getMaxTokensByLength(settings.length)
    const temperature = settings.quality === 'expert' ? 0.3 : 0.7

    // 构建系统提示词
    const systemPrompt = this.buildSystemPrompt(settings)
    
    // 分段处理大纲内容
    const chunks = this.splitOutline(outline)
    const generatedChunks: string[] = []

    for (const chunk of chunks) {
      const messages: DeepSeekChatMessage[] = [
        {
          role: 'system',
          content: systemPrompt
        },
        {
          role: 'user',
          content: `请根据以下大纲内容生成详细的标书内容：\n\n${chunk}`
        }
      ]

      const response = await this.createChatCompletion(messages, {
        maxTokens,
        temperature
      })

      if (response.choices && response.choices.length > 0) {
        generatedChunks.push(response.choices[0].message.content)
      }
    }

    return generatedChunks.join('\n\n')
  }

  /**
   * 根据篇幅设置获取最大token数
   */
  private getMaxTokensByLength(length: 'short' | 'medium' | 'medium-long' | 'long' | 'extra-long'): number {
    switch (length) {
      case 'short':
        return 2048
      case 'medium':
        return 3072
      case 'medium-long':
        return 3584
      case 'long':
        return 4096
      case 'extra-long':
        return 4096
      default:
        return 3072
    }
  }

  /**
   * 构建系统提示词
   */
  private buildSystemPrompt(settings: GenerationSettings): string {
    const qualityPrompt = settings.quality === 'expert' 
      ? '你是一位资深的投标专家，具有丰富的标书撰写经验。请以专业、严谨的语言风格撰写标书内容。'
      : '你是一位标书撰写助手，请以清晰、规范的语言风格撰写标书内容。'

    const lengthPrompt = {
      short: '请生成简洁明了的标书内容，重点突出核心要点。',
      medium: '请生成详细完整的标书内容，包含必要的说明和论证。',
      'medium-long': '请生成较为详细的标书内容，包含充分的分析和论证。',
      long: '请生成全面深入的标书内容，包含详细的分析、论证和实施方案。',
      'extra-long': '请生成极其详细的标书内容，包含全面的分析、深入的论证和完整的实施方案。'
    }[settings.length]

    return `${qualityPrompt}\n\n${lengthPrompt}\n\n请确保生成的内容：
1. 结构清晰，逻辑严密
2. 语言专业，表达准确
3. 符合招标文件要求
4. 突出技术优势和服务特色
5. 格式规范，便于阅读`
  }

  /**
   * 分割大纲内容以适应token限制
   */
  private splitOutline(outline: string): string[] {
    const maxChunkSize = 2000 // 预留空间给系统提示词
    const chunks: string[] = []
    
    // 按段落分割
    const paragraphs = outline.split('\n\n')
    let currentChunk = ''
    
    for (const paragraph of paragraphs) {
      if ((currentChunk + paragraph).length > maxChunkSize && currentChunk) {
        chunks.push(currentChunk.trim())
        currentChunk = paragraph
      } else {
        currentChunk += (currentChunk ? '\n\n' : '') + paragraph
      }
    }
    
    if (currentChunk) {
      chunks.push(currentChunk.trim())
    }
    
    return chunks.length > 0 ? chunks : [outline]
  }



  /**
   * 流式生成内容（用于实时显示生成进度）
   */
  async generateContentStream(
    outline: string, 
    settings: GenerationSettings,
    onChunk: (chunk: string) => void
  ): Promise<string> {
    const maxTokens = this.getMaxTokensByLength(settings.length)
    const temperature = settings.quality === 'expert' ? 0.3 : 0.7
    const systemPrompt = this.buildSystemPrompt(settings)

    const messages: DeepSeekChatMessage[] = [
      {
        role: 'system',
        content: systemPrompt
      },
      {
        role: 'user',
        content: `请根据以下大纲内容生成详细的标书内容：\n\n${outline}`
      }
    ]

    // 注意：这里需要实现流式处理，当前为简化版本
    const response = await this.createChatCompletion(messages, {
      maxTokens,
      temperature,
      stream: false
    })

    const content = response.choices?.[0]?.message?.content || ''
    onChunk(content)
    return content
  }
}

// 导出单例实例
export const deepseekService = new DeepSeekService()
export default deepseekService