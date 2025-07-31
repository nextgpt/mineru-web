# 招标文件智能生成标书系统 API 文档

## 概述

本文档描述了招标文件智能生成标书系统的RESTful API接口。系统提供完整的招标项目管理、文件分析、大纲生成、内容生成和文档导出功能。

## 基础信息

- **基础URL**: `http://localhost:8000/api`
- **认证方式**: 通过HTTP头部 `X-User-Id` 传递用户ID
- **数据格式**: JSON
- **字符编码**: UTF-8

## 通用响应格式

### 成功响应
```json
{
  "status": "success",
  "data": {...},
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "status": "error",
  "error_code": "ERROR_CODE",
  "detail": "错误详细信息",
  "message": "用户友好的错误信息"
}
```

## 项目管理 API

### 1. 创建项目

**POST** `/tender/projects`

创建新的招标项目。

#### 请求参数
```json
{
  "project_name": "项目名称",
  "source_file_id": 123
}
```

#### 响应示例
```json
{
  "id": "project-uuid",
  "project_name": "项目名称",
  "source_filename": "招标文件.pdf",
  "status": "created",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 2. 获取项目列表

**GET** `/tender/projects`

获取用户的项目列表，支持分页和筛选。

#### 查询参数
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认10）
- `search`: 搜索关键词
- `status`: 项目状态筛选

#### 响应示例
```json
{
  "projects": [
    {
      "id": "project-uuid",
      "project_name": "项目名称",
      "source_filename": "招标文件.pdf",
      "status": "completed",
      "progress": 100,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

### 3. 获取项目详情

**GET** `/tender/projects/{project_id}`

获取指定项目的详细信息。

#### 响应示例
```json
{
  "id": "project-uuid",
  "project_name": "项目名称",
  "source_filename": "招标文件.pdf",
  "status": "completed",
  "progress": 100,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 4. 删除项目

**DELETE** `/tender/projects/{project_id}`

删除指定项目及其相关数据。

#### 响应示例
```json
{
  "message": "项目删除成功"
}
```

## 文件分析 API

### 1. 启动分析

**POST** `/tender/projects/{project_id}/analyze`

启动招标文件分析任务。

#### 响应示例
```json
{
  "message": "分析任务已启动",
  "task_id": "analysis-task-uuid"
}
```

### 2. 获取分析结果

**GET** `/tender/projects/{project_id}/analysis`

获取文件分析结果。

#### 响应示例
```json
{
  "project_info": {
    "project_name": "项目名称",
    "budget": "100万元",
    "duration": "6个月",
    "location": "北京市",
    "contact_info": "联系方式",
    "deadline": "2024-12-31"
  },
  "technical_requirements": {
    "functional_requirements": [
      "功能需求1",
      "功能需求2"
    ],
    "performance_requirements": "性能要求描述",
    "technical_specifications": "技术规格说明"
  },
  "evaluation_criteria": {
    "technical_score": "技术分评分标准",
    "commercial_score": "商务分评分标准",
    "evaluation_method": "评标方法"
  },
  "submission_requirements": {
    "document_format": "文档格式要求",
    "submission_method": "提交方式",
    "required_documents": "必需文档清单",
    "document_structure": "文档结构要求"
  }
}
```

### 3. 更新分析结果

**PUT** `/tender/projects/{project_id}/analysis`

更新文件分析结果。

#### 请求参数
与获取分析结果的响应格式相同。

#### 响应示例
```json
{
  "message": "分析结果已更新"
}
```

## 大纲生成 API

### 1. 生成大纲

**POST** `/tender/projects/{project_id}/outline/generate`

基于分析结果生成标书大纲。

#### 请求参数
```json
{
  "regenerate": false
}
```

#### 响应示例
```json
{
  "message": "大纲生成任务已启动",
  "task_id": "outline-task-uuid"
}
```

### 2. 获取大纲

**GET** `/tender/projects/{project_id}/outline`

获取项目大纲。

#### 响应示例
```json
{
  "chapters": [
    {
      "chapter_id": "1",
      "title": "项目概述",
      "description": "项目基本信息介绍",
      "subsections": [
        {
          "id": "1.1",
          "title": "项目背景"
        },
        {
          "id": "1.2",
          "title": "项目目标"
        }
      ]
    },
    {
      "chapter_id": "2",
      "title": "技术方案",
      "description": "详细技术实施方案",
      "subsections": [
        {
          "id": "2.1",
          "title": "技术架构"
        },
        {
          "id": "2.2",
          "title": "实施计划"
        }
      ]
    }
  ]
}
```

### 3. 更新大纲

**PUT** `/tender/projects/{project_id}/outline`

更新项目大纲。

#### 请求参数
与获取大纲的响应格式相同。

#### 响应示例
```json
{
  "message": "大纲已更新"
}
```

## 内容生成 API

### 1. 生成所有内容

**POST** `/tender/projects/{project_id}/content/generate-all`

生成所有章节的内容。

#### 请求参数
```json
{
  "regenerate": false
}
```

#### 响应示例
```json
{
  "message": "内容生成任务已启动",
  "task_id": "content-task-uuid"
}
```

### 2. 生成单章节内容

**POST** `/tender/projects/{project_id}/content/generate-chapter`

生成指定章节的内容。

#### 请求参数
```json
{
  "chapter_id": "1"
}
```

#### 响应示例
```json
{
  "message": "章节内容生成任务已启动",
  "task_id": "chapter-task-uuid"
}
```

### 3. 获取内容

**GET** `/tender/projects/{project_id}/content`

获取项目的所有内容。

#### 响应示例
```json
{
  "chapters": [
    {
      "chapter_id": "1",
      "title": "项目概述",
      "content": "这是项目概述的详细内容...",
      "word_count": 500,
      "generated_at": "2024-01-01T00:00:00Z"
    },
    {
      "chapter_id": "2",
      "title": "技术方案",
      "content": "这是技术方案的详细内容...",
      "word_count": 800,
      "generated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 4. 更新章节内容

**PUT** `/tender/projects/{project_id}/content/{chapter_id}`

更新指定章节的内容。

#### 请求参数
```json
{
  "content": "更新后的章节内容..."
}
```

#### 响应示例
```json
{
  "message": "章节内容已更新"
}
```

### 5. 获取生成进度

**GET** `/tender/projects/{project_id}/content/progress`

获取内容生成进度。

#### 响应示例
```json
{
  "percentage": 75,
  "current_chapter": "第3章：技术方案",
  "completed_chapters": 2,
  "total_chapters": 4,
  "estimated_remaining": 300
}
```

## 文档导出 API

### 1. 导出文档

**POST** `/tender/projects/{project_id}/export`

导出标书文档。

#### 请求参数
```json
{
  "format": "pdf",
  "options": {
    "title": "标书标题",
    "company_name": "公司名称",
    "include_cover": true,
    "include_toc": true
  }
}
```

#### 响应示例
```json
{
  "message": "导出任务已启动",
  "task_id": "export-task-uuid"
}
```

### 2. 获取导出历史

**GET** `/tender/projects/{project_id}/documents`

获取项目的导出文档列表。

#### 响应示例
```json
{
  "documents": [
    {
      "id": "document-uuid",
      "filename": "标书_v1.0.pdf",
      "format": "pdf",
      "file_size": 2048576,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 3. 下载文档

**GET** `/tender/documents/{document_id}/download`

获取文档下载链接。

#### 响应示例
```json
{
  "download_url": "https://minio.example.com/bucket/document.pdf?expires=...",
  "filename": "标书_v1.0.pdf",
  "expires_at": "2024-01-01T01:00:00Z"
}
```

### 4. 预览文档

**GET** `/tender/documents/{document_id}/preview`

获取文档预览链接。

#### 响应示例
```json
{
  "preview_url": "https://minio.example.com/bucket/document.pdf",
  "filename": "标书_v1.0.pdf"
}
```

## WebSocket API

### 连接端点
`ws://localhost:8000/ws`

### 消息格式

#### 客户端消息

##### 认证
```json
{
  "type": "auth",
  "data": {
    "user_id": "user-uuid"
  }
}
```

##### 订阅项目更新
```json
{
  "type": "subscribe",
  "data": {
    "project_id": "project-uuid"
  }
}
```

##### 取消订阅
```json
{
  "type": "unsubscribe",
  "data": {
    "project_id": "project-uuid"
  }
}
```

#### 服务器消息

##### 项目状态更新
```json
{
  "type": "project_update",
  "data": {
    "project_id": "project-uuid",
    "status": "analyzing",
    "progress": 50,
    "message": "正在分析招标文件..."
  },
  "project_id": "project-uuid"
}
```

##### 任务进度更新
```json
{
  "type": "task_progress",
  "data": {
    "project_id": "project-uuid",
    "task_id": "task-uuid",
    "progress": 75,
    "current_step": "生成第3章内容",
    "estimated_remaining": 300
  }
}
```

##### 错误通知
```json
{
  "type": "error",
  "data": {
    "message": "分析任务失败",
    "error_code": "ANALYSIS_FAILED",
    "details": "文件格式不支持"
  }
}
```

##### 通知消息
```json
{
  "type": "notification",
  "data": {
    "message": "项目创建成功",
    "level": "success"
  }
}
```

## 状态码说明

### 项目状态
- `created`: 已创建
- `analyzing`: 分析中
- `analyzed`: 已分析
- `outlining`: 大纲生成中
- `outlined`: 大纲已生成
- `generating`: 内容生成中
- `generated`: 内容已生成
- `exporting`: 导出中
- `completed`: 已完成
- `failed`: 失败

### HTTP状态码
- `200`: 成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 未认证
- `403`: 权限不足
- `404`: 资源不存在
- `422`: 数据验证失败
- `500`: 服务器内部错误

## 错误码说明

### 通用错误
- `INVALID_REQUEST`: 无效请求
- `UNAUTHORIZED`: 未授权访问
- `FORBIDDEN`: 禁止访问
- `NOT_FOUND`: 资源不存在
- `VALIDATION_ERROR`: 数据验证错误

### 业务错误
- `PROJECT_NOT_FOUND`: 项目不存在
- `FILE_NOT_FOUND`: 文件不存在
- `ANALYSIS_FAILED`: 分析失败
- `OUTLINE_GENERATION_FAILED`: 大纲生成失败
- `CONTENT_GENERATION_FAILED`: 内容生成失败
- `EXPORT_FAILED`: 导出失败
- `TASK_TIMEOUT`: 任务超时
- `CONCURRENT_LIMIT_EXCEEDED`: 并发限制超出

## 使用示例

### Python示例
```python
import requests
import json

# 基础配置
BASE_URL = "http://localhost:8000/api"
HEADERS = {
    "Content-Type": "application/json",
    "X-User-Id": "user-123"
}

# 创建项目
def create_project(name, file_id):
    url = f"{BASE_URL}/tender/projects"
    data = {
        "project_name": name,
        "source_file_id": file_id
    }
    response = requests.post(url, json=data, headers=HEADERS)
    return response.json()

# 启动分析
def start_analysis(project_id):
    url = f"{BASE_URL}/tender/projects/{project_id}/analyze"
    response = requests.post(url, headers=HEADERS)
    return response.json()

# 获取项目状态
def get_project_status(project_id):
    url = f"{BASE_URL}/tender/projects/{project_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

# 使用示例
project = create_project("测试项目", 123)
project_id = project["id"]

start_analysis(project_id)

# 轮询检查状态
import time
while True:
    status = get_project_status(project_id)
    print(f"项目状态: {status['status']}")
    if status["status"] in ["completed", "failed"]:
        break
    time.sleep(5)
```

### JavaScript示例
```javascript
const BASE_URL = "http://localhost:8000/api";
const HEADERS = {
    "Content-Type": "application/json",
    "X-User-Id": "user-123"
};

// 创建项目
async function createProject(name, fileId) {
    const response = await fetch(`${BASE_URL}/tender/projects`, {
        method: "POST",
        headers: HEADERS,
        body: JSON.stringify({
            project_name: name,
            source_file_id: fileId
        })
    });
    return response.json();
}

// WebSocket连接
function connectWebSocket(userId) {
    const ws = new WebSocket(`ws://localhost:8000/ws`);
    
    ws.onopen = () => {
        // 认证
        ws.send(JSON.stringify({
            type: "auth",
            data: { user_id: userId }
        }));
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log("收到消息:", message);
        
        if (message.type === "project_update") {
            console.log(`项目 ${message.data.project_id} 状态更新: ${message.data.status}`);
        }
    };
    
    return ws;
}

// 使用示例
const ws = connectWebSocket("user-123");

createProject("测试项目", 123).then(project => {
    console.log("项目创建成功:", project);
    
    // 订阅项目更新
    ws.send(JSON.stringify({
        type: "subscribe",
        data: { project_id: project.id }
    }));
});
```

## 限制和配额

### 请求限制
- API请求频率: 100次/分钟/用户
- 文件上传大小: 100MB
- 并发任务数: 5个/用户

### 数据限制
- 项目名称长度: 1-100字符
- 章节内容长度: 最大50,000字符
- 项目数量: 100个/用户

## 版本信息

- **当前版本**: v1.0.0
- **API版本**: v1
- **最后更新**: 2024-01-01

## 支持和反馈

如有问题或建议，请联系技术支持团队。