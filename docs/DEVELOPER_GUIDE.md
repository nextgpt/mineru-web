# 招标文件智能生成标书系统开发者文档

## 系统架构

### 整体架构
系统采用前后端分离的微服务架构，主要包括以下组件：

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 (Vue.js)  │    │  后端 (FastAPI)  │    │   AI服务 (SGLang) │
│                 │    │                 │    │                 │
│ - 用户界面      │◄──►│ - RESTful API   │◄──►│ - 模型推理      │
│ - 状态管理      │    │ - WebSocket     │    │ - 文本生成      │
│ - 实时通信      │    │ - 任务调度      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx (代理)   │    │  Redis (队列)    │    │  MinIO (存储)    │
│                 │    │                 │    │                 │
│ - 静态文件服务  │    │ - 任务队列      │    │ - 文件存储      │
│ - 反向代理      │    │ - 缓存          │    │ - 对象存储      │
│ - 负载均衡      │    │ - 会话存储      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 技术栈

#### 前端技术栈
- **框架**: Vue.js 3.x
- **构建工具**: Vite
- **UI组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP客户端**: Axios
- **WebSocket**: 原生WebSocket API
- **类型检查**: TypeScript

#### 后端技术栈
- **框架**: FastAPI
- **异步运行时**: Uvicorn
- **数据库ORM**: SQLAlchemy
- **数据库迁移**: Alembic
- **任务队列**: Redis + Celery
- **文件存储**: MinIO
- **AI集成**: OpenAI API / SGLang
- **文档生成**: ReportLab (PDF) + python-docx (Word)

#### 基础设施
- **容器化**: Docker + Docker Compose
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **缓存**: Redis
- **对象存储**: MinIO
- **反向代理**: Nginx

## 项目结构

### 后端结构
```
backend/
├── app/
│   ├── api/                    # API路由
│   │   ├── __init__.py
│   │   ├── tender.py          # 招标相关API
│   │   └── websocket.py       # WebSocket API
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   └── tender.py          # 招标数据模型
│   ├── services/               # 业务服务
│   │   ├── __init__.py
│   │   ├── tender_analysis.py      # 文件分析服务
│   │   ├── outline_generation.py   # 大纲生成服务
│   │   ├── content_generation.py   # 内容生成服务
│   │   ├── document_export.py      # 文档导出服务
│   │   ├── tender_storage.py       # 存储服务
│   │   ├── content_management.py   # 内容管理服务
│   │   ├── document_management.py  # 文档管理服务
│   │   ├── task_manager.py         # 任务管理服务
│   │   └── ai_client.py            # AI客户端服务
│   ├── utils/                  # 工具模块
│   │   ├── __init__.py
│   │   ├── tenant_manager.py       # 多租户管理
│   │   ├── database.py             # 数据库工具
│   │   └── minio_client.py         # MinIO客户端
│   ├── middleware/             # 中间件
│   │   ├── __init__.py
│   │   └── tenant_middleware.py    # 租户中间件
│   └── __init__.py
├── tests/                      # 测试文件
├── scripts/                    # 脚本文件
├── alembic/                    # 数据库迁移
├── requirements.txt            # Python依赖
├── Dockerfile                  # Docker配置
├── entrypoint.sh              # 启动脚本
└── main.py                    # 应用入口
```

### 前端结构
```
frontend/
├── src/
│   ├── api/                    # API接口
│   ├── assets/                 # 静态资源
│   ├── components/             # Vue组件
│   │   ├── AnalysisStep.vue        # 分析步骤组件
│   │   ├── OutlineStep.vue         # 大纲步骤组件
│   │   ├── ContentStep.vue         # 内容步骤组件
│   │   ├── ExportStep.vue          # 导出步骤组件
│   │   ├── ProgressIndicator.vue   # 进度指示器
│   │   └── ConnectionStatus.vue    # 连接状态
│   ├── router/                 # 路由配置
│   ├── services/               # 服务层
│   │   └── websocket.ts           # WebSocket服务
│   ├── store/                  # 状态管理
│   ├── utils/                  # 工具函数
│   ├── views/                  # 页面组件
│   │   ├── Projects.vue           # 项目列表页
│   │   ├── ProjectDetail.vue      # 项目详情页
│   │   ├── Files.vue              # 文件管理页
│   │   ├── Upload.vue             # 文件上传页
│   │   └── Home.vue               # 首页
│   ├── test/                   # 测试文件
│   ├── App.vue                 # 根组件
│   └── main.ts                 # 应用入口
├── public/                     # 公共资源
├── package.json               # 依赖配置
├── vite.config.ts            # Vite配置
├── vitest.config.ts          # 测试配置
└── Dockerfile                # Docker配置
```

## 核心模块详解

### 1. 多租户架构

#### TenantManager
负责多租户隔离和权限管理：

```python
class TenantManager:
    def __init__(self):
        self.tenant_contexts = {}
    
    def get_tenant_path(self, tenant_id: str, path: str = "") -> str:
        """获取租户专用路径"""
        return f"tenants/{tenant_id}/{path}".rstrip("/")
    
    def validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """验证租户访问权限"""
        # 实现租户权限验证逻辑
        pass
```

#### TenantMiddleware
FastAPI中间件，实现请求级别的租户隔离：

```python
class TenantMiddleware:
    async def __call__(self, request: Request, call_next):
        # 从请求头获取用户ID
        user_id = request.headers.get("X-User-Id")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"detail": "用户ID缺失"}
            )
        
        # 设置租户上下文
        tenant_id = self.get_tenant_id(user_id)
        request.state.tenant_id = tenant_id
        request.state.user_id = user_id
        
        return await call_next(request)
```

### 2. 数据存储架构

#### 数据库模型
使用SQLAlchemy定义数据模型：

```python
class TenderProject(Base):
    __tablename__ = "tender_projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    project_name = Column(String, nullable=False)
    source_file_id = Column(Integer, nullable=True)
    source_filename = Column(String, nullable=True)
    status = Column(Enum(TenderStatus), nullable=False, default=TenderStatus.CREATED)
    progress = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### MinIO存储结构
```
bucket/
├── tenants/
│   └── {tenant_id}/
│       └── projects/
│           └── {project_id}/
│               ├── analysis/
│               │   └── result.json
│               ├── outline/
│               │   └── structure.json
│               ├── content/
│               │   ├── chapter_1.json
│               │   ├── chapter_2.json
│               │   └── ...
│               ├── documents/
│               │   ├── tender_v1.pdf
│               │   └── tender_v1.docx
│               ├── versions/
│               │   └── {chapter_id}/
│               │       ├── v_20240101_120000.json
│               │       └── current.json
│               └── history/
│                   └── edit_20240101_120000.json
```

### 3. AI服务集成

#### AI客户端抽象
```python
class AIClient(ABC):
    @abstractmethod
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """生成文本"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查服务可用性"""
        pass

class OpenAIClient(AIClient):
    def __init__(self, api_key: str, base_url: str = None, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": request.prompt}],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return AIResponse(
            text=response.choices[0].message.content,
            usage=response.usage.dict()
        )
```

### 4. 任务管理系统

#### 异步任务处理
```python
class TaskManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.running_tasks = {}
    
    async def submit_task(self, task_id: str, task_func, *args, **kwargs):
        """提交异步任务"""
        task = asyncio.create_task(task_func(*args, **kwargs))
        self.running_tasks[task_id] = task
        
        # 设置任务状态
        await self.set_task_status(task_id, "running")
        
        try:
            result = await task
            await self.set_task_status(task_id, "completed", result)
            return result
        except Exception as e:
            await self.set_task_status(task_id, "failed", str(e))
            raise
        finally:
            self.running_tasks.pop(task_id, None)
    
    async def cancel_task(self, task_id: str):
        """取消任务"""
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            await self.set_task_status(task_id, "cancelled")
```

### 5. WebSocket实时通信

#### 连接管理
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}
        self.project_subscribers: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)
    
    async def send_project_update(self, project_id: str, data: dict):
        """发送项目更新消息"""
        if project_id in self.project_subscribers:
            message = {
                "type": "project_update",
                "data": data,
                "project_id": project_id
            }
            
            for user_id in self.project_subscribers[project_id]:
                await self.send_personal_message(message, user_id)
```

## 开发环境设置

### 1. 环境要求
- Python 3.9+
- Node.js 16+
- Docker 20.10+
- Redis 6.0+
- MinIO (或兼容的S3存储)

### 2. 后端开发环境
```bash
# 克隆项目
git clone <repository-url>
cd tender-document-generator/backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export DATABASE_URL="sqlite:///./dev.db"
export REDIS_HOST="localhost"
export MINIO_ENDPOINT="localhost:9000"
export OPENAI_API_KEY="your-api-key"

# 初始化数据库
python scripts/init_db.py

# 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端开发环境
```bash
# 进入前端目录
cd tender-document-generator/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 使用Docker开发
```bash
# 启动依赖服务
docker-compose up -d redis minio

# 本地开发后端和前端
# 按照上述步骤启动
```

## 测试指南

### 1. 后端测试
```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_tender_analysis.py

# 运行测试并生成覆盖率报告
pytest --cov=app tests/

# 运行性能测试
pytest tests/test_performance.py -v -s
```

### 2. 前端测试
```bash
cd frontend

# 运行单元测试
npm run test

# 运行测试并监听文件变化
npm run test:watch

# 生成测试覆盖率报告
npm run test:coverage
```

### 3. 集成测试
```bash
# 启动完整环境
docker-compose up -d

# 运行集成测试
pytest tests/test_integration_workflow.py -v -s
```

## 部署指南

### 1. 开发环境部署
```bash
# 使用Docker Compose
docker-compose up -d
```

### 2. 生产环境部署
```bash
# 设置环境变量
export OPENAI_API_KEY="your-production-api-key"
export DATABASE_URL="postgresql://user:pass@host:port/db"

# 使用生产配置
docker-compose -f docker-compose.prod.yml up -d
```

### 3. 监控和日志
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 监控资源使用
docker stats
```

## API开发规范

### 1. 路由设计
- 使用RESTful风格
- 统一的URL前缀：`/api`
- 版本控制：`/api/v1`
- 资源命名使用复数形式

### 2. 请求/响应格式
```python
# 请求模型
class CreateProjectRequest(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=100)
    source_file_id: int = Field(..., gt=0)

# 响应模型
class ProjectResponse(BaseModel):
    id: str
    project_name: str
    status: TenderStatus
    created_at: datetime
    updated_at: datetime
```

### 3. 错误处理
```python
class TenderException(Exception):
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)

@app.exception_handler(TenderException)
async def tender_exception_handler(request: Request, exc: TenderException):
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "error_code": exc.error_code,
            "detail": exc.message
        }
    )
```

## 前端开发规范

### 1. 组件设计原则
- 单一职责原则
- 可复用性
- 响应式设计
- 无障碍访问

### 2. 状态管理
```typescript
// 使用Pinia进行状态管理
export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  
  const fetchProjects = async () => {
    const response = await api.get('/tender/projects')
    projects.value = response.data.projects
  }
  
  return {
    projects,
    currentProject,
    fetchProjects
  }
})
```

### 3. 错误处理
```typescript
// 统一错误处理
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // 处理认证错误
      router.push('/login')
    } else {
      // 显示错误消息
      ElMessage.error(error.response?.data?.detail || '操作失败')
    }
    return Promise.reject(error)
  }
)
```

## 性能优化

### 1. 后端优化
- 使用异步处理长时间任务
- 实现请求缓存
- 数据库查询优化
- 连接池管理

### 2. 前端优化
- 组件懒加载
- 图片懒加载
- 虚拟滚动
- 防抖和节流

### 3. 系统优化
- Redis缓存策略
- MinIO存储优化
- Docker镜像优化
- 负载均衡配置

## 安全考虑

### 1. 认证和授权
- 用户身份验证
- 多租户隔离
- API访问控制
- 敏感数据保护

### 2. 数据安全
- 输入验证
- SQL注入防护
- XSS防护
- CSRF防护

### 3. 网络安全
- HTTPS加密
- CORS配置
- 请求频率限制
- 安全头设置

## 扩展开发

### 1. 添加新的AI模型
```python
class CustomAIClient(AIClient):
    def __init__(self, config):
        self.config = config
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        # 实现自定义AI模型调用
        pass
```

### 2. 添加新的导出格式
```python
class PowerPointExporter(DocumentExporter):
    async def export(self, project: TenderProject, **options) -> str:
        # 实现PowerPoint导出逻辑
        pass
```

### 3. 添加新的前端页面
```vue
<template>
  <div class="new-feature">
    <!-- 新功能界面 -->
  </div>
</template>

<script setup lang="ts">
// 新功能逻辑
</script>
```

## 贡献指南

### 1. 代码规范
- 遵循PEP 8 (Python)
- 遵循ESLint规则 (JavaScript/TypeScript)
- 编写清晰的注释
- 保持代码简洁

### 2. 提交规范
```
feat: 添加新功能
fix: 修复bug
docs: 更新文档
style: 代码格式调整
refactor: 代码重构
test: 添加测试
chore: 构建过程或辅助工具的变动
```

### 3. 开发流程
1. Fork项目
2. 创建功能分支
3. 编写代码和测试
4. 提交Pull Request
5. 代码审查
6. 合并代码

## 常见问题

### 1. 开发环境问题
**Q: 数据库连接失败**
A: 检查DATABASE_URL环境变量和数据库服务状态

**Q: Redis连接失败**
A: 确认Redis服务运行并检查REDIS_HOST配置

### 2. 部署问题
**Q: Docker容器启动失败**
A: 检查Docker日志和环境变量配置

**Q: AI服务调用失败**
A: 验证API密钥和网络连接

### 3. 性能问题
**Q: 任务处理缓慢**
A: 检查系统资源使用情况和并发配置

**Q: 前端加载慢**
A: 启用生产构建和CDN加速

---

*本开发者文档将持续更新，欢迎贡献和反馈。*