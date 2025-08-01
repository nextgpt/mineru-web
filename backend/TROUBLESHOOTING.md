# 故障排除指南

## 常见问题及解决方案

### 1. NumPy 模块缺失警告

**错误信息：**
```
Failed to initialize NumPy: No module named 'numpy'
```

**解决方案：**

1. **安装 NumPy：**
   ```bash
   pip install numpy>=1.21.0
   ```

2. **或者重新安装所有依赖：**
   ```bash
   pip install -r requirements.txt
   ```

3. **使用启动脚本（推荐）：**
   ```bash
   python start_local.py
   ```

### 2. Redis 连接错误

**错误信息：**
```
Could not connect to Redis: Authentication required.
```

**解决方案：**

#### 对于 Docker 环境（推荐）：

1. **检查 Docker 容器状态：**
   ```bash
   docker ps | grep redis
   ```

2. **使用 Docker 环境启动脚本：**
   ```bash
   python start_docker.py
   ```

3. **手动设置环境变量：**
   ```bash
   export REDIS_HOST=localhost
   export REDIS_PORT=16379  # Docker 映射端口
   export REDIS_DB=0
   export REDIS_PASSWORD=
   ```

#### 对于本地环境：

1. **检查 Redis 服务是否运行：**
   ```bash
   redis-cli ping
   ```

2. **如果 Redis 需要密码，设置环境变量：**
   ```bash
   export REDIS_PASSWORD=your_password
   ```

3. **或者使用无密码的 Redis：**
   ```bash
   # 停止当前 Redis
   sudo systemctl stop redis
   
   # 启动无密码 Redis
   redis-server --port 6379
   ```

4. **使用 Docker 启动 Redis：**
   ```bash
   docker run -d -p 6379:6379 redis:latest
   ```

### 3. 环境变量配置

**创建 .env 文件：**
```bash
cp env.example .env
```

**编辑 .env 文件：**
```env
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 其他配置...
```

### 4. 完整启动流程

#### 对于 Docker 环境（推荐）：

1. **安装依赖：**
   ```bash
   pip install -r requirements.txt
   ```

2. **确保 Docker 容器运行：**
   ```bash
   docker-compose up -d
   # 或检查现有容器
   docker ps | grep mineru
   ```

3. **启动应用：**
   ```bash
   # 使用 Docker 环境启动脚本（推荐）
   python start_docker.py
   
   # 或直接启动
   uvicorn main:app --host 0.0.0.0 --port 8088 --reload
   ```

#### 对于本地环境：

1. **安装依赖：**
   ```bash
   pip install -r requirements.txt
   ```

2. **启动 Redis：**
   ```bash
   # 使用 Docker
   docker run -d -p 6379:6379 redis:latest
   
   # 或使用系统服务
   sudo systemctl start redis
   ```

3. **启动应用：**
   ```bash
   # 使用启动脚本（推荐）
   python start_local.py
   
   # 或直接启动
   uvicorn main:app --host 0.0.0.0 --port 8088 --reload
   ```

### 5. 使用 Docker Compose（推荐）

如果使用 Docker Compose，所有服务都会自动配置：

```bash
docker-compose up -d
```

### 6. 检查服务状态

```bash
# 检查 Redis
redis-cli ping

# 检查应用
curl http://localhost:8088/ping

# 检查端口
netstat -tlnp | grep 8088
```

## 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看 Redis 日志
tail -f /var/log/redis/redis-server.log
``` 