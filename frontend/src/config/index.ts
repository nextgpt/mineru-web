// 应用配置文件

export const config = {
  // RAGFLOW API 配置
  ragflow: {
    baseURL: import.meta.env.VITE_RAGFLOW_BASE_URL || 'http://192.168.30.220',
    apiKey: import.meta.env.VITE_RAGFLOW_API_KEY || 'ragflow-FmYTZmNmYyMDNmYzExZjA4OGFjZGU3Nm',
    timeout: 30000,
    defaultChunkMethod: 'book' as const,
    defaultSimilarityThreshold: 0.2,
    // 默认解析器配置，使用book方法
    defaultParserConfig: {
      raptor: {
        use_raptor: false
      }
    }
  },

  // DeepSeek API 配置
  deepseek: {
    baseURL: import.meta.env.VITE_DEEPSEEK_BASE_URL || 'https://api.deepseek.com',
    apiKey: import.meta.env.VITE_DEEPSEEK_API_KEY || '',
    model: 'deepseek-chat',
    maxTokens: 4096,
    temperature: 0.7,
    timeout: 60000
  },

  // 应用配置
  app: {
    name: '招标文件智能生成标书系统',
    version: '1.0.0',
    maxFileSize: 200 * 1024 * 1024, // 200MB
    supportedFileTypes: ['.pdf', '.doc', '.docx'],
    autoSaveInterval: 5000, // 5秒自动保存
    retryAttempts: 3,
    retryDelay: 1000
  },

  // 大纲生成五阶段提示词
  outlinePrompts: [
    {
      id: 1,
      title: '项目需求概况生成',
      prompt: '请深入理解项目的技术/服务需求并总结成概况概要，不超过300字'
    },
    {
      id: 2,
      title: '需求重要性分析',
      prompt: '请通过行业理解和项目的技术/服务需求分析，根据甲方需求的关注程度将技术/服务需求分为：关键需求、重要需求、一般需求。特别注意请忽略商务需求内容'
    },
    {
      id: 3,
      title: '评分项内容分析',
      prompt: '逐行分析和锁定具体的评分项内容，分点输出得分点、得分分数，内容要求（内容要求必须原文输出，不能伪造数字或要求'
    },
    {
      id: 4,
      title: '评分策略分析',
      prompt: '输出客观评分项、主观评分项、主观评分项整体应答策略逻辑、技术方案重点应答评分项及原因'
    },
    {
      id: 5,
      title: '最终大纲整合',
      prompt: '根据前四个阶段的内容整合输出技术/服务方案大纲'
    }
  ]
}

// 验证配置
export const validateConfig = () => {
  const errors: string[] = []

  if (!config.ragflow.baseURL) {
    errors.push('RAGFLOW base URL is required')
  }

  if (!config.ragflow.apiKey) {
    errors.push('RAGFLOW API key is required')
  }

  if (!config.deepseek.apiKey) {
    console.warn('DeepSeek API key is not configured')
  }

  if (errors.length > 0) {
    throw new Error(`Configuration errors: ${errors.join(', ')}`)
  }
}

export default config