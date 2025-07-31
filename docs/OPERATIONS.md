# 招标文件智能生成标书系统运维指南

## 概述

本文档提供招标文件智能生成标书系统的运维指南，包括监控、备份、故障排除、性能优化等内容。

## 监控体系

### 1. 监控架构

系统采用Prometheus + Grafana + AlertManager的监控方案：

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Prometheus  │◄──►│   Grafana   │    │AlertManager │
│   (指标)    │    │  (可视化)   │    │  (告警)     │
└─────────────┘    └─────────────┘    └─────────────┘
       ▲                                      │
       │                                      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│应用指标导出  │    │系统指标导出  │    │  通知渠道   │
│   (API)     │    │(Node Exp.)  │    │(邮件/Webhook)│
└─────────────┘    └─────────────┘    └─────────────┘
```

### 2. 启动监控服务

```bash
# 启动监控栈
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# 检查服务状态
docker-compose -f docker-compose.monitoring.yml ps
```

### 3. 访问监控界面

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **AlertManager**: http://localhost:9093

### 4. 关键监控指标

#### 系统指标
- CPU使用率
- 内存使用率
- 磁盘使用率
- 网络I/O
- 负载平均值

#### 应用指标
- HTTP请求数量和响应时间
- 错误率
- 活跃连接数
- 任务队列长度
- AI服务调用次数和延迟

#### 业务指标
- 项目创建数量
- 文件分析成功率
- 内容生成完成率
- 用户活跃度

## 日志管理

### 1. 日志架构

使用Loki + Promtail进行日志收集和管理：

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  应用日志   │    │  Promtail   │    │    Loki     │
│             │───►│  (收集)     │───►│  (存储)     │
└─────────────┘    └─────────────┘    └─────────────┘
                                             │
                                             ▼
                                    ┌─────────────┐
                                    │   Grafana   │
                                    │  (查询)     │
                                    └─────────────┘
```

### 2. 日志查看

```bash
# 查看实时日志
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f frontend

# 查看特定时间段日志
docker-compose logs --since="2024-01-01T00:00:00" backend

# 在Grafana中查询日志
# 访问 http://localhost:3000，选择Loki数据源
```

### 3. 日志级别配置

在环境变量中设置日志级别：
```bash
export LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 备份和恢复

### 1. 自动备份

设置定时备份任务：

```bash
# 添加到crontab
crontab -e

# 每天凌晨2点执行备份
0 2 * * * /path/to/tender-system/scripts/backup.sh

# 每周日凌晨1点执行完整备份
0 1 * * 0 /path/to/tender-system/scripts/backup.sh --full
```

### 2. 手动备份

```bash
# 执行备份
./scripts/backup.sh

# 备份到指定目录
BACKUP_DIR=/custom/backup ./scripts/backup.sh
```

### 3. 数据恢复

```bash
# 从备份恢复
./scripts/restore.sh /backup/tender-system/tender_backup_20240101_120000.tar.gz

# 验证恢复结果
./scripts/health_check.sh
```

### 4. 备份策略

- **每日备份**: 保留30天
- **每周备份**: 保留12周
- **每月备份**: 保留12个月
- **异地备份**: 定期同步到远程存储

## 健康检查

### 1. 自动健康检查

```bash
# 运行健康检查
./scripts/health_check.sh

# 设置定时检查
*/5 * * * * /path/to/tender-system/scripts/health_check.sh
```

### 2. 健康检查项目

- 前端服务可访问性
- 后端API响应
- 数据库连接
- Redis连接
- MinIO服务状态
- 系统资源使用情况

### 3. 健康检查结果

```bash
# 检查通过
echo $?  # 返回0

# 检查失败
echo $?  # 返回1
```

## 故障排除

### 1. 常见问题诊断

#### 服务无法启动
```bash
# 检查Docker服务
systemctl status docker

# 检查容器状态
docker-compose ps

# 查看容器日志
docker-compose logs <service_name>

# 检查端口占用
netstat -tlnp | grep <port>
```

#### 数据库连接失败
```bash
# 检查数据库文件
ls -la mineru.db

# 检查数据库权限
sqlite3 mineru.db ".tables"

# 重建数据库
python scripts/init_db.py
```

#### Redis连接失败
```bash
# 检查Redis服务
docker-compose logs redis

# 测试Redis连接
redis-cli -h localhost -p 6379 ping

# 重启Redis
docker-compose restart redis
```

#### MinIO存储问题
```bash
# 检查MinIO服务
docker-compose logs minio

# 检查存储空间
df -h

# 访问MinIO控制台
# http://localhost:9001 (minioadmin/minioadmin)
```

### 2. 性能问题诊断

#### 响应时间慢
```bash
# 检查系统负载
top
htop

# 检查内存使用
free -h

# 检查磁盘I/O
iostat -x 1

# 检查网络连接
netstat -an | grep ESTABLISHED | wc -l
```

#### 任务处理缓慢
```bash
# 检查任务队列
redis-cli llen task_queue

# 检查工作进程
docker-compose logs worker

# 检查AI服务响应
curl -f http://localhost:30000/health
```

### 3. 错误日志分析

#### 后端错误
```bash
# 查看错误日志
docker-compose logs backend | grep ERROR

# 分析错误模式
docker-compose logs backend | grep ERROR | awk '{print $4}' | sort | uniq -c
```

#### 前端错误
```bash
# 查看Nginx错误日志
docker-compose logs frontend | grep error

# 检查JavaScript错误
# 在浏览器开发者工具中查看控制台
```

## 性能优化

### 1. 系统级优化

#### 内核参数调优
```bash
# 编辑 /etc/sysctl.conf
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
vm.swappiness = 10

# 应用配置
sysctl -p
```

#### 文件描述符限制
```bash
# 编辑 /etc/security/limits.conf
* soft nofile 65535
* hard nofile 65535

# 重启生效
```

### 2. 应用级优化

#### 数据库优化
```bash
# SQLite优化
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = memory;
```

#### Redis优化
```bash
# Redis配置优化
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### MinIO优化
```bash
# 设置环境变量
MINIO_CACHE_DRIVES="/tmp/cache"
MINIO_CACHE_EXCLUDE="*.pdf"
MINIO_CACHE_QUOTA=80
```

### 3. 容器优化

#### Docker配置
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

#### 镜像优化
```dockerfile
# 使用多阶段构建
FROM python:3.9-slim as builder
# 构建阶段

FROM python:3.9-slim
# 运行阶段
COPY --from=builder /app /app
```

## 安全管理

### 1. 访问控制

#### 网络安全
```bash
# 防火墙配置
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 8000/tcp  # 仅内部访问
ufw enable
```

#### SSL/TLS配置
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
}
```

### 2. 数据安全

#### 敏感数据加密
```bash
# 使用环境变量存储敏感信息
export OPENAI_API_KEY="$(cat /secure/openai_key)"
export DATABASE_PASSWORD="$(cat /secure/db_password)"
```

#### 定期安全更新
```bash
# 更新系统包
apt update && apt upgrade -y

# 更新Docker镜像
docker-compose pull
docker-compose up -d
```

## 容量规划

### 1. 存储容量

#### 数据增长预估
- 数据库: 每个项目约1MB
- MinIO存储: 每个项目约10-50MB
- 日志文件: 每天约100MB

#### 存储扩展
```bash
# 监控存储使用
df -h
du -sh /var/lib/docker/volumes/

# 扩展存储
# 1. 添加新磁盘
# 2. 扩展文件系统
# 3. 迁移数据
```

### 2. 计算资源

#### 资源需求评估
- CPU: 每100并发用户需要2核心
- 内存: 每100并发用户需要4GB
- 网络: 每100并发用户需要100Mbps

#### 水平扩展
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
  worker:
    deploy:
      replicas: 5
```

## 升级和维护

### 1. 系统升级

#### 升级前准备
```bash
# 1. 备份数据
./scripts/backup.sh

# 2. 检查系统状态
./scripts/health_check.sh

# 3. 通知用户维护窗口
```

#### 升级流程
```bash
# 1. 拉取最新代码
git pull origin main

# 2. 更新Docker镜像
docker-compose pull

# 3. 停止服务
docker-compose down

# 4. 运行数据库迁移
docker-compose run --rm backend alembic upgrade head

# 5. 启动服务
docker-compose up -d

# 6. 验证升级
./scripts/health_check.sh
```

### 2. 定期维护

#### 每日维护
- 检查系统状态
- 查看错误日志
- 监控资源使用

#### 每周维护
- 清理临时文件
- 检查备份完整性
- 更新安全补丁

#### 每月维护
- 性能分析和优化
- 容量规划评估
- 安全审计

## 应急响应

### 1. 应急预案

#### 服务中断
1. 立即检查系统状态
2. 查看错误日志
3. 尝试重启服务
4. 如无法恢复，启用备用方案
5. 通知相关人员

#### 数据丢失
1. 停止所有写操作
2. 评估数据丢失范围
3. 从最近备份恢复
4. 验证数据完整性
5. 恢复服务

#### 安全事件
1. 立即隔离受影响系统
2. 收集证据和日志
3. 评估影响范围
4. 修复安全漏洞
5. 恢复正常服务

### 2. 联系信息

#### 技术支持
- 系统管理员: admin@company.com
- 开发团队: dev@company.com
- 安全团队: security@company.com

#### 外部支持
- 云服务商支持
- 第三方服务支持
- 硬件厂商支持

## 文档和培训

### 1. 运维文档

- 系统架构文档
- 操作手册
- 故障排除指南
- 应急响应预案

### 2. 培训计划

- 新员工培训
- 定期技能更新
- 应急演练
- 最佳实践分享

---

*本运维指南将根据系统演进持续更新，请定期查看最新版本。*