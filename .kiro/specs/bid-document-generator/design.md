# 设计文档

## 概述

基于现有的mineru-web文档解析系统，设计并实现一个智能招标文件生成标书的系统。该系统将在现有架构基础上扩展，增加项目管理、AI分析、标书生成等核心功能。系统采用前后端分离架构，后端使用FastAPI，前端使用Vue3 + Element Plus，数据库使用PostgreSQL，文件存储使用MinIO。

## 架构

### 系统架构图

```mermaid
graph TB
    subgraph "前端层"
        A[Vue3 + Element Plus]
        A1[项目管理页面]
        A2[标书生成页面]
        A3[文件上传组件]
    end
    
    subgraph "后端API层"
        B[FastAPI Backend]
        B1[项目管理API]
        B2[AI分析API]
        B3[标书生成API]
        B4[文件管理API - 现有]
    end
    
    subgraph "服务层"
        C[业务服务层]
        C1[项目服务]
        C2[AI分析服务]
        C3[标书生成服务]
        C4[文档解析服务 - 现有]
    end
    
    subgraph "外部服务"
        D[MinerU文档解析API]
        E[VLLM大模型API]
        F[MinIO存储]
        G[Redis缓存]
        H[PostgreSQL数据库]
    end
    
    A --> B
    B --> C
    C --> D
    C --> E
    C --> F
    C --> G
    C --> H
```

### 数据流架构

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端
    participant B as 后端API
    participant M as MinerU服务
    participant L as 大模型API
    participant DB as 数据库
    
    U->>F: 上传招标文件
    F->>B: 创建项目并上传文件
    B->>DB: 保存项目信息
    B->>M: 调用文档解析API
    M-->>B: 返回解析结果
    B->>DB: 保存解析内容
    B->>L: 调用AI分析需求
    L-->>B: 返回需求分析结果
    B->>DB: 保存分析结果
    B->>L: 生成标书大纲
    L-->>B: 返回大纲结构
    B->>L: 生成完整标书内容
    L-->>B: 返回标书内容
    B->>DB: 保存标书内容
    B-->>F: 返回生成结果
    F-->>U: 展示标书内容
```

## 组件和接口

### 数据模型扩展

#### 1. 项目模型 (Project)
```python
class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), nullable=False, index=True)
    name = Column(String(256), nullable=False)  # 项目名称
    description = Column(Text)  # 项目描述
    status = Column(Enum(ProjectStatus), default=ProjectStatus.CREATED)
    original_file_id = Column(Integer, ForeignKey('files.id'))  # 关联原始招标文件
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # 关系
    original_file = relationship("File", back_populates="projects")
    requirements = relationship("RequirementAnalysis", back_populates="project")
    outlines = relationship("BidOutline", back_populates="project")
    documents = relationship("BidDocument", back_populates="project")

class ProjectStatus(enum.Enum):
    CREATED = 'created'  # 已创建
    PARSING = 'parsing'  # 文档解析中
    ANALYZING = 'analyzing'  # AI分析中
    OUTLINE_GENERATED = 'outline_generated'  # 大纲已生成
    DOCUMENT_GENERATING = 'document_generating'  # 标书生成中
    COMPLETED = 'completed'  # 已完成
    FAILED = 'failed'  # 失败
```

#### 2. 需求分析模型 (RequirementAnalysis)
```python
class RequirementAnalysis(Base):
    __tablename__ = 'requirement_analysis'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    user_id = Column(String(64), nullable=False)
    
    # 需求理解概况
    project_overview = Column(Text)  # 项目概览
    client_info = Column(Text)  # 甲方信息
    budget_info = Column(Text)  # 预算信息
    detailed_requirements = Column(Text)  # 详细需求
    
    # 需求分级
    critical_requirements = Column(Text)  # 关键需求
    important_requirements = Column(Text)  # 重要需求
    general_requirements = Column(Text)  # 一般需求
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="requirements")
```

#### 3. 标书大纲模型 (BidOutline)
```python
class BidOutline(Base):
    __tablename__ = 'bid_outlines'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    user_id = Column(String(64), nullable=False)
    title = Column(String(512), nullable=False)  # 大纲标题
    level = Column(Integer, nullable=False)  # 层级 (1,2,3)
    sequence = Column(String(32), nullable=False)  # 序号 (1, 1.1, 1.1.1)
    parent_id = Column(Integer, ForeignKey('bid_outlines.id'))  # 父级大纲
    order_index = Column(Integer, default=0)  # 排序索引
    content = Column(Text)  # 大纲内容描述
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="outlines")
    parent = relationship("BidOutline", remote_side=[id])
    children = relationship("BidOutline")
```

#### 4. 标书文档模型 (BidDocument)
```python
class BidDocument(Base):
    __tablename__ = 'bid_documents'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    user_id = Column(String(64), nullable=False)
    title = Column(String(512), nullable=False)  # 文档标题
    content = Column(Text, nullable=False)  # 文档内容
    outline_id = Column(Integer, ForeignKey('bid_outlines.id'))  # 关联大纲
    status = Column(Enum(DocumentStatus), default=DocumentStatus.DRAFT)
    version = Column(Integer, default=1)  # 版本号
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="documents")
    outline = relationship("BidOutline")

class DocumentStatus(enum.Enum):
    DRAFT = 'draft'  # 草稿
    GENERATED = 'generated'  # 已生成
    EDITED = 'edited'  # 已编辑
    FINALIZED = 'finalized'  # 已定稿
```

### API接口设计

#### 1. 项目管理API
```python
# 项目列表
GET /api/projects
# 创建项目
POST /api/projects
# 项目详情
GET /api/projects/{project_id}
# 更新项目
PUT /api/projects/{project_id}
# 删除项目
DELETE /api/projects/{project_id}
# 上传招标文件到项目
POST /api/projects/{project_id}/upload
```

#### 2. AI分析API
```python
# 开始需求分析
POST /api/projects/{project_id}/analyze
# 获取分析结果
GET /api/projects/{project_id}/analysis
# 更新分析结果
PUT /api/projects/{project_id}/analysis
```

#### 3. 标书生成API
```python
# 生成标书大纲
POST /api/projects/{project_id}/generate-outline
# 获取标书大纲
GET /api/projects/{project_id}/outline
# 更新标书大纲
PUT /api/projects/{project_id}/outline
# 生成标书内容
POST /api/projects/{project_id}/generate-document
# 获取标书文档
GET /api/projects/{project_id}/documents
# 导出标书
GET /api/projects/{project_id}/export
```

### 服务层设计

#### 1. 项目服务 (ProjectService)
```python
class ProjectService:
    def create_project(self, user_id: str, name: str, description: str = None) -> Project
    def upload_tender_file(self, project_id: int, file: UploadFile) -> File
    def get_project_list(self, user_id: str, page: int, page_size: int) -> List[Project]
    def get_project_detail(self, project_id: int, user_id: str) -> Project
    def update_project_status(self, project_id: int, status: ProjectStatus) -> Project
    def delete_project(self, project_id: int, user_id: str) -> bool
```

#### 2. AI分析服务 (AIAnalysisService)
```python
class AIAnalysisService:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def analyze_tender_document(self, project_id: int, parsed_content: str) -> RequirementAnalysis
    def extract_project_overview(self, content: str) -> str
    def extract_client_info(self, content: str) -> str
    def extract_budget_info(self, content: str) -> str
    def classify_requirements(self, content: str) -> Dict[str, str]
    def generate_requirement_summary(self, analysis: RequirementAnalysis) -> str
```

#### 3. 标书生成服务 (BidGenerationService)
```python
class BidGenerationService:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def generate_outline(self, project_id: int, analysis: RequirementAnalysis) -> List[BidOutline]
    def generate_document_content(self, project_id: int, outline: BidOutline) -> BidDocument
    def generate_full_document(self, project_id: int) -> str
    def export_document(self, project_id: int, format: str) -> bytes
```

#### 4. 大模型客户端 (LLMClient)
```python
class LLMClient:
    def __init__(self, api_url: str, api_key: str, model_name: str):
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name
    
    def chat_completion(self, messages: List[Dict], temperature: float = 0.7) -> str
    def analyze_document(self, content: str, prompt_template: str) -> str
    def generate_content(self, prompt: str, max_tokens: int = 2000) -> str
```

#### 5. 文档解析客户端 (MinerUClient)
```python
class MinerUClient:
    def __init__(self, api_url: str):
        self.api_url = api_url
    
    def parse_document(self, file_path: str) -> Dict
    def get_parse_result(self, task_id: str) -> Dict
    def check_parse_status(self, task_id: str) -> str
```

### 前端组件设计

#### 1. 项目管理组件
```vue
<!-- ProjectList.vue - 项目列表 -->
<template>
  <div class="project-list">
    <div class="project-header">
      <h2>项目管理</h2>
      <el-button @click="createProject">新建项目</el-button>
    </div>
    <el-table :data="projects">
      <el-table-column prop="name" label="项目名称" />
      <el-table-column prop="status" label="状态" />
      <el-table-column prop="created_at" label="创建时间" />
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button @click="viewProject(row)">查看</el-button>
          <el-button @click="deleteProject(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<!-- ProjectDetail.vue - 项目详情 -->
<template>
  <div class="project-detail">
    <div class="project-info">
      <h2>{{ project.name }}</h2>
      <el-tag :type="getStatusType(project.status)">
        {{ getStatusText(project.status) }}
      </el-tag>
    </div>
    
    <el-tabs v-model="activeTab">
      <el-tab-pane label="基本信息" name="info">
        <ProjectInfo :project="project" />
      </el-tab-pane>
      <el-tab-pane label="需求分析" name="analysis">
        <RequirementAnalysis :project-id="project.id" />
      </el-tab-pane>
      <el-tab-pane label="标书大纲" name="outline">
        <BidOutline :project-id="project.id" />
      </el-tab-pane>
      <el-tab-pane label="标书内容" name="document">
        <BidDocument :project-id="project.id" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
```

#### 2. 需求分析组件
```vue
<!-- RequirementAnalysis.vue -->
<template>
  <div class="requirement-analysis">
    <div class="analysis-header">
      <h3>需求分析</h3>
      <el-button 
        v-if="!analysis" 
        @click="startAnalysis" 
        :loading="analyzing"
        type="primary"
      >
        开始分析
      </el-button>
    </div>
    
    <div v-if="analysis" class="analysis-content">
      <el-card title="项目概览">
        <p>{{ analysis.project_overview }}</p>
      </el-card>
      
      <el-card title="甲方信息">
        <p>{{ analysis.client_info }}</p>
      </el-card>
      
      <el-card title="需求分级">
        <el-tabs>
          <el-tab-pane label="关键需求" name="critical">
            <div v-html="analysis.critical_requirements"></div>
          </el-tab-pane>
          <el-tab-pane label="重要需求" name="important">
            <div v-html="analysis.important_requirements"></div>
          </el-tab-pane>
          <el-tab-pane label="一般需求" name="general">
            <div v-html="analysis.general_requirements"></div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>
```

#### 3. 标书生成组件
```vue
<!-- BidOutline.vue -->
<template>
  <div class="bid-outline">
    <div class="outline-header">
      <h3>标书大纲</h3>
      <el-button 
        v-if="!outline.length" 
        @click="generateOutline"
        :loading="generating"
        type="primary"
      >
        生成大纲
      </el-button>
    </div>
    
    <div v-if="outline.length" class="outline-tree">
      <el-tree
        :data="outlineTree"
        :props="{ children: 'children', label: 'title' }"
        node-key="id"
        default-expand-all
      >
        <template #default="{ node, data }">
          <div class="outline-node">
            <span>{{ data.sequence }} {{ data.title }}</span>
            <div class="node-actions">
              <el-button size="small" @click="editOutline(data)">编辑</el-button>
              <el-button size="small" @click="generateContent(data)">生成内容</el-button>
            </div>
          </div>
        </template>
      </el-tree>
    </div>
  </div>
</template>

<!-- BidDocument.vue -->
<template>
  <div class="bid-document">
    <div class="document-header">
      <h3>标书内容</h3>
      <div class="document-actions">
        <el-button @click="generateFullDocument" type="primary">
          生成完整标书
        </el-button>
        <el-button @click="exportDocument">导出文档</el-button>
      </div>
    </div>
    
    <div class="document-content">
      <div class="document-editor">
        <el-input
          v-model="documentContent"
          type="textarea"
          :rows="20"
          placeholder="标书内容将在这里显示..."
        />
      </div>
    </div>
  </div>
</template>
```

## 数据模型

### 数据库表结构

```sql
-- 项目表
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    name VARCHAR(256) NOT NULL,
    description TEXT,
    status VARCHAR(32) DEFAULT 'created',
    original_file_id INTEGER REFERENCES files(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 需求分析表
CREATE TABLE requirement_analysis (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL,
    project_overview TEXT,
    client_info TEXT,
    budget_info TEXT,
    detailed_requirements TEXT,
    critical_requirements TEXT,
    important_requirements TEXT,
    general_requirements TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 标书大纲表
CREATE TABLE bid_outlines (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL,
    title VARCHAR(512) NOT NULL,
    level INTEGER NOT NULL,
    sequence VARCHAR(32) NOT NULL,
    parent_id INTEGER REFERENCES bid_outlines(id),
    order_index INTEGER DEFAULT 0,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 标书文档表
CREATE TABLE bid_documents (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL,
    title VARCHAR(512) NOT NULL,
    content TEXT NOT NULL,
    outline_id INTEGER REFERENCES bid_outlines(id),
    status VARCHAR(32) DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_requirement_analysis_project_id ON requirement_analysis(project_id);
CREATE INDEX idx_bid_outlines_project_id ON bid_outlines(project_id);
CREATE INDEX idx_bid_documents_project_id ON bid_documents(project_id);
```

### 数据关系图

```mermaid
erDiagram
    PROJECTS ||--o{ REQUIREMENT_ANALYSIS : has
    PROJECTS ||--o{ BID_OUTLINES : has
    PROJECTS ||--o{ BID_DOCUMENTS : has
    PROJECTS ||--|| FILES : references
    BID_OUTLINES ||--o{ BID_OUTLINES : parent_child
    BID_OUTLINES ||--o{ BID_DOCUMENTS : generates
    
    PROJECTS {
        int id PK
        string user_id
        string name
        text description
        string status
        int original_file_id FK
        datetime created_at
        datetime updated_at
    }
    
    REQUIREMENT_ANALYSIS {
        int id PK
        int project_id FK
        string user_id
        text project_overview
        text client_info
        text budget_info
        text detailed_requirements
        text critical_requirements
        text important_requirements
        text general_requirements
        datetime created_at
    }
    
    BID_OUTLINES {
        int id PK
        int project_id FK
        string user_id
        string title
        int level
        string sequence
        int parent_id FK
        int order_index
        text content
        datetime created_at
    }
    
    BID_DOCUMENTS {
        int id PK
        int project_id FK
        string user_id
        string title
        text content
        int outline_id FK
        string status
        int version
        datetime created_at
        datetime updated_at
    }
    
    FILES {
        int id PK
        string user_id
        string filename
        int size
        string status
        datetime upload_time
        string minio_path
    }
```

## 错误处理

### 错误类型定义
```python
class BidGeneratorException(Exception):
    """标书生成系统基础异常"""
    pass

class ProjectNotFoundException(BidGeneratorException):
    """项目不存在异常"""
    pass

class DocumentParseException(BidGeneratorException):
    """文档解析异常"""
    pass

class AIAnalysisException(BidGeneratorException):
    """AI分析异常"""
    pass

class DocumentGenerationException(BidGeneratorException):
    """文档生成异常"""
    pass

class ExternalServiceException(BidGeneratorException):
    """外部服务调用异常"""
    pass
```

### 错误处理策略
1. **API层错误处理**: 统一异常处理中间件，返回标准化错误响应
2. **服务层错误处理**: 业务逻辑异常捕获和转换
3. **外部服务错误处理**: 网络超时、服务不可用的重试机制
4. **前端错误处理**: 全局错误拦截器，用户友好的错误提示

### 重试机制
```python
from tenacity import retry, stop_after_attempt, wait_exponential

class ExternalServiceClient:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def call_external_api(self, url: str, data: dict) -> dict:
        # 外部API调用逻辑
        pass
```

## 测试策略

### 单元测试
- 模型层测试：数据模型的CRUD操作
- 服务层测试：业务逻辑的正确性
- API层测试：接口的输入输出验证

### 集成测试
- 数据库集成测试：数据持久化和查询
- 外部服务集成测试：MinerU和大模型API调用
- 端到端测试：完整的标书生成流程

### 测试工具
- 后端：pytest + pytest-asyncio + httpx
- 前端：Vitest + Vue Test Utils
- API测试：Postman/Newman
- 性能测试：Locust

### 测试数据
- 准备多种类型的招标文件样本
- 模拟不同复杂度的需求分析场景
- 创建标准的测试用例和预期结果

## 部署配置

### Docker Compose配置更新
```yaml
version: '3.8'

services:
  frontend:
    image: lpdswing/mineru-web-frontend:v2.0.0
    ports:
      - "8088:80"
    depends_on:
      - backend
      - minio
    networks:
      - mineru-network

  backend:
    image: lpdswing/mineru-web-backend:v2.1.9
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=16379
      - MINIO_ENDPOINT=minio:19000
      - DATABASE_URL=postgresql://postgres:password@postgres:15432/bidgen
      - MINERU_API_URL=http://192.168.30.54:8088
      - LLM_API_URL=http://192.168.30.54:3000/v1
      - LLM_API_KEY=token-abc123
      - LLM_MODEL_NAME=Qwen3-30B-A3B-FP8
    depends_on:
      - redis
      - minio
      - postgres
    networks:
      - mineru-network

  redis:
    image: redis:latest
    ports:
      - "16379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    networks:
      - mineru-network

  minio:
    image: minio:latest
    ports:
      - "19000:9000"
      - "19001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    networks:
      - mineru-network

  postgres:
    image: postgres:17
    ports:
      - "15432:5432"
    environment:
      POSTGRES_DB: bidgen
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - mineru-network

volumes:
  minio_data:
  redis_data:
  postgres_data:

networks:
  mineru-network:
    driver: bridge
```

### 环境变量配置
```bash
# 数据库配置
DATABASE_URL=postgresql://postgres:password@192.168.30.220:15432/bidgen

# Redis配置
REDIS_HOST=192.168.30.220
REDIS_PORT=16379

# MinIO配置
MINIO_ENDPOINT=192.168.30.220:19000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# 外部服务配置
MINERU_API_URL=http://192.168.30.54:8088
LLM_API_URL=http://192.168.30.54:3000/v1
LLM_API_KEY=token-abc123
LLM_MODEL_NAME=Qwen3-30B-A3B-FP8

# 应用配置
DEBUG=false
LOG_LEVEL=INFO
MAX_FILE_SIZE=100MB
ALLOWED_FILE_TYPES=pdf,doc,docx
```

## 性能优化

### 后端优化
1. **数据库优化**: 合理的索引设计，查询优化
2. **缓存策略**: Redis缓存热点数据，减少数据库查询
3. **异步处理**: 文档解析和AI分析使用异步任务队列
4. **连接池**: 数据库和外部服务连接池管理

### 前端优化
1. **组件懒加载**: 路由级别的代码分割
2. **数据缓存**: Vuex/Pinia状态管理和本地缓存
3. **虚拟滚动**: 大量数据列表的性能优化
4. **防抖节流**: 搜索和API调用的优化

### 系统监控
1. **日志系统**: 结构化日志记录和分析
2. **性能监控**: API响应时间和系统资源监控
3. **错误追踪**: 异常信息收集和告警
4. **业务指标**: 项目创建、标书生成成功率等关键指标