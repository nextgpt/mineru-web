# API服务文档

本目录包含招标文件智能生成标书系统的所有API服务。

## 文件结构

```
api/
├── index.ts          # 统一导出文件
├── ragflow.ts        # RAGFLOW API服务
├── deepseek.ts       # DeepSeek API服务
├── stats.ts          # 统计API服务（原有）
└── README.md         # 本文档
```

## 环境配置

在 `.env` 文件中配置以下环境变量：

```bash
# RAGFLOW API 配置
VITE_RAGFLOW_BASE_URL=http://192.168.30.220
VITE_RAGFLOW_API_KEY=ragflow-FmYTZmNmYyMDNmYzExZjA4OGFjZGU3Nm

# DeepSeek API 配置
VITE_DEEPSEEK_API_KEY=your_deepseek_api_key_here
VITE_DEEPSEEK_BASE_URL=https://api.deepseek.com
```

## RAGFLOW API服务

### 主要功能

- 创建数据集（使用book切片方式）
- 上传文档到数据集
- 解析文档内容
- 检索知识库内容
- 管理数据集和文档

### 使用示例

```typescript
import { ragflowService } from '@/api'

// 创建数据集
const dataset = await ragflowService.createDataset('项目名称')

// 上传文档
const document = await ragflowService.uploadDocument(dataset.id, file)

// 解析文档
await ragflowService.parseDocument(dataset.id, [document.id])

// 检索内容
const result = await ragflowService.retrieveContent(dataset.id, '查询问题')
```

## DeepSeek API服务

### 主要功能

- 聊天完成API调用
- 标书内容生成
- 分段处理大纲内容
- 流式内容生成

### 使用示例

```typescript
import { deepseekService } from '@/api'

// 生成标书内容
const content = await deepseekService.generateContent(outline, {
  length: 'medium',
  quality: 'expert'
})

// 聊天完成
const response = await deepseekService.createChatCompletion([
  { role: 'user', content: '你好' }
])
```

## 错误处理

所有API服务都包含统一的错误处理机制：

- 自动重试（可配置）
- 错误消息提示
- 日志记录
- 超时处理

## 测试工具

使用 `test-api.ts` 中的工具函数测试API连接：

```typescript
import { testAllConnections } from '@/utils/test-api'

const results = await testAllConnections()
console.log('API连接状态:', results)
```

## 注意事项

1. 确保RAGFLOW服务器可访问
2. DeepSeek API密钥需要有效
3. 网络连接稳定
4. 文件大小限制：200MB
5. 支持的文件格式：PDF, DOC, DOCX