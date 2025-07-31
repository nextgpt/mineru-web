# 招标文件智能生成标书系统部署指南

## 系统要求

### 硬件要求
- CPU: 4核心以上
- 内存: 8GB以上
- 存储: 50GB以上可用空间
- GPU: NVIDIA GPU（可选，用于AI模型加速）

### 软件要求
- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker（如果使用GPU）

## 快速部署

### 1. 克隆项目
```bash
git clone <repository-url>
cd tender-document-generator
```

### 2. 配置环境变量
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下关键参数：
- `OPENAI_API_KEY`: OpenAI API密钥
- `OPENAI_BASE_URL`: OpenAI API基础URL
- `AI_MODEL_NAME`: 使用的AI模型名称

### 3. 启动服务
```bash
docker-compose up -d
```

### 4. 验证部署
访问 http://localhost:8088 查看前端界面

## 详细配置

### 环境变量说明

#### AI模型配置
- `OPENAI_API_KEY`: OpenAI API密钥（必需）
- `OPENAI_BASE_URL`: API基础URL，默认为官方API
- `AI_MODEL_NAME`: 模型名称，推荐使用 gpt-4

#### 系统配置
- `ENABLE_WEBSOCKET`: 是否启用WebSocket实时通信
- `TASK_TIMEOUT`: 任务超时时间（秒）
- `MAX_CONCURRENT_TASKS`: 最大并发任务数

#### 数据库配置
- `DATABASE_URL`: 数据库连接URL
- `REDIS_HOST`: Redis服务器地址

#### 存储配置
- `MINIO_ENDPOINT`: MinIO服务端点
- `MINIO_ROOT_USER`: MinIO管理员用户名
- `MINIO_ROOT_PASSWORD`: MinIO管理员密码

### 服务说明

#### 前端服务 (frontend)
- 端口: 8088
- 基于Vue.js的用户界面
- 提供项目管理、文件上传、进度监控等功能

#### 后端服务 (backend)
- 端口: 8000
- 基于FastAPI的API服务
- 提供RESTful API和WebSocket接口

#### 工作进程 (worker)
- 异步任务处理
- 处理文件分析、大纲生成、内容生成等任务

#### AI服务 (mineru-sglang)
- 端口: 30000
- AI模型推理服务
- 支持GPU加速

#### Redis
- 端口: 6379
- 任务队列和缓存

#### MinIO
- 端口: 9000 (API), 9001 (控制台)
- 对象存储服务
- 存储文件和生成的文档

## 生产环境部署

### 1. 安全配置
```bash
# 生成安全密钥
export SECRET_KEY=$(openssl rand -hex 32)

# 配置CORS
export CORS_ORIGINS="https://yourdomain.com"
```

### 2. 数据持久化
确保以下目录有适当的备份策略：
- MinIO数据: `minio_data` volume
- Redis数据: `redis_data` volume
- SQLite数据库: `./mineru.db`

### 3. 监控和日志
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
docker-compose logs -f worker
```

### 4. 性能优化
- 根据硬件配置调整 `MAX_CONCURRENT_TASKS`
- 使用GPU加速AI推理
- 配置适当的内存限制

## 故障排除

### 常见问题

#### 1. AI服务连接失败
检查 `SERVER_URL` 配置和网络连接：
```bash
docker-compose logs mineru-sglang
```

#### 2. 数据库迁移失败
手动运行数据库初始化：
```bash
docker-compose exec backend python scripts/init_db.py
```

#### 3. 文件上传失败
检查MinIO服务状态和存储空间：
```bash
docker-compose logs minio
```

#### 4. 任务处理缓慢
检查Redis连接和工作进程状态：
```bash
docker-compose logs worker
docker-compose logs redis
```

### 日志查看
```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs backend
docker-compose logs worker
docker-compose logs frontend

# 实时查看日志
docker-compose logs -f backend
```

### 性能监控
```bash
# 查看资源使用情况
docker stats

# 查看服务健康状态
docker-compose ps
```

## 升级指南

### 1. 备份数据
```bash
# 备份数据库
cp mineru.db mineru.db.backup

# 备份MinIO数据
docker-compose exec minio mc mirror /data /backup
```

### 2. 更新代码
```bash
git pull origin main
```

### 3. 重新构建和部署
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### 4. 运行数据库迁移
```bash
docker-compose exec backend alembic upgrade head
```

## 开发环境设置

### 1. 本地开发
```bash
# 启动依赖服务
docker-compose up -d redis minio

# 本地运行后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 本地运行前端
cd frontend
npm install
npm run dev
```

### 2. 测试
```bash
# 运行后端测试
cd backend
pytest

# 运行前端测试
cd frontend
npm run test
```

## 支持和维护

### 定期维护任务
- 清理过期的临时文件
- 备份重要数据
- 更新依赖包
- 监控系统性能

### 联系支持
如遇到问题，请提供以下信息：
- 系统版本
- 错误日志
- 配置信息（隐藏敏感信息）
- 重现步骤