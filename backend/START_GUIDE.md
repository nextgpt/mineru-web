# 标书生成系统后端启动指南

## 环境信息
- 开发机: 192.168.30.220 (已部署 MinIO、Redis、PostgreSQL)
- MinerU服务: http://192.168.30.54:8088
- 大模型服务: http://192.168.30.54:3000/v1
- 前端服务: http://192.168.30.220:5173

## 快速启动步骤

### 1. 安装Python依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 初始化数据库（首次运行）
```bash
python init_db.py
```

### 3. 启动后端服务
```bash
# 方式1: 使用简化启动脚本（推荐）
python start_simple.py

# 方式2: 直接使用uvicorn
python main.py

# 方式3: 使用uvicorn命令
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 服务地址
- 后端API: http://192.168.30.220:8000
- API文档: http://192.168.30.220:8000/docs
- 健康检查: http://192.168.30.220:8000/api/health

## 环境变量配置
已在 `.env` 文件中配置了以下环境变量：
- DATABASE_URL: PostgreSQL数据库连接
- REDIS_HOST/PORT: Redis连接配置
- MINIO_ENDPOINT: MinIO对象存储配置
- MINERU_API_URL: 文档解析服务地址
- LLM_API_URL: 大模型服务地址

## 测试连接
启动后可以访问以下端点测试：
1. http://192.168.30.220:8000/ping - 基础连通性测试
2. http://192.168.30.220:8000/api/health - 健康检查
3. http://192.168.30.220:8000/docs - API文档

## 常见问题

### 1. 数据库连接失败
- 确认PostgreSQL服务在192.168.30.220:5432上运行
- 确认数据库名为 `bidgen`，用户名 `postgres`，密码 `password`

### 2. Redis连接失败
- 确认Redis服务在192.168.30.220:6379上运行

### 3. MinIO连接失败
- 确认MinIO服务在192.168.30.220:9000上运行
- 确认访问密钥为 `minioadmin:minioadmin`

### 4. 依赖安装失败
```bash
# 如果遇到依赖冲突，可以创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## 开发调试
- 服务支持热重载，修改代码后会自动重启
- 日志级别设置为INFO，可以看到详细的请求日志
- 可以通过 http://192.168.30.220:8000/docs 查看和测试API

## 前后端联调
1. 确保前端运行在: http://192.168.30.220:5173
2. 确保后端运行在: http://192.168.30.220:8000
3. 前端会自动代理API请求到后端
4. 可以通过浏览器开发者工具查看网络请求