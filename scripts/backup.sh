#!/bin/bash

# 招标系统备份脚本
# 用于备份数据库、MinIO数据和配置文件

set -e

# 配置
BACKUP_DIR="/backup/tender-system"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="tender_backup_${DATE}"
RETENTION_DAYS=30

# 创建备份目录
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

echo "开始备份招标系统数据..."
echo "备份时间: $(date)"
echo "备份目录: ${BACKUP_DIR}/${BACKUP_NAME}"

# 1. 备份数据库
echo "备份数据库..."
if [ -f "./mineru.db" ]; then
    cp "./mineru.db" "${BACKUP_DIR}/${BACKUP_NAME}/database.db"
    echo "SQLite数据库备份完成"
else
    echo "警告: 数据库文件不存在"
fi

# 2. 备份MinIO数据
echo "备份MinIO数据..."
if command -v docker &> /dev/null; then
    # 使用MinIO客户端备份
    docker exec tender-minio mc mirror /data "${BACKUP_DIR}/${BACKUP_NAME}/minio_data" || {
        echo "警告: MinIO数据备份失败，尝试直接复制数据卷"
        docker run --rm -v minio_data:/source -v "${BACKUP_DIR}/${BACKUP_NAME}":/backup alpine \
            sh -c "cp -r /source/* /backup/minio_data/ 2>/dev/null || echo '数据卷为空或不存在'"
    }
    echo "MinIO数据备份完成"
else
    echo "警告: Docker未安装，跳过MinIO备份"
fi

# 3. 备份Redis数据
echo "备份Redis数据..."
if command -v docker &> /dev/null; then
    docker exec tender-redis redis-cli BGSAVE
    sleep 5  # 等待备份完成
    docker cp tender-redis:/data/dump.rdb "${BACKUP_DIR}/${BACKUP_NAME}/redis_dump.rdb" || {
        echo "警告: Redis备份失败"
    }
    echo "Redis数据备份完成"
fi

# 4. 备份配置文件
echo "备份配置文件..."
CONFIG_FILES=(
    "docker-compose.yml"
    ".env"
    "nginx.conf"
    "backend/alembic.ini"
    "monitoring/"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -e "$file" ]; then
        if [ -d "$file" ]; then
            cp -r "$file" "${BACKUP_DIR}/${BACKUP_NAME}/"
        else
            cp "$file" "${BACKUP_DIR}/${BACKUP_NAME}/"
        fi
        echo "已备份: $file"
    else
        echo "警告: 配置文件不存在: $file"
    fi
done

# 5. 创建备份信息文件
cat > "${BACKUP_DIR}/${BACKUP_NAME}/backup_info.txt" << EOF
备份信息
========
备份时间: $(date)
备份版本: ${BACKUP_NAME}
系统版本: $(git rev-parse HEAD 2>/dev/null || echo "未知")
备份内容:
- 数据库文件
- MinIO对象存储数据
- Redis数据
- 系统配置文件
- 监控配置

恢复说明:
1. 停止所有服务: docker-compose down
2. 恢复数据库: cp database.db ./mineru.db
3. 恢复MinIO数据: docker run --rm -v minio_data:/target -v $(pwd)/minio_data:/source alpine cp -r /source/* /target/
4. 恢复Redis数据: docker cp redis_dump.rdb tender-redis:/data/dump.rdb
5. 恢复配置文件: cp -r 配置文件 到对应位置
6. 启动服务: docker-compose up -d
EOF

# 6. 压缩备份
echo "压缩备份文件..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
rm -rf "${BACKUP_NAME}"
echo "备份压缩完成: ${BACKUP_NAME}.tar.gz"

# 7. 清理旧备份
echo "清理旧备份文件..."
find "${BACKUP_DIR}" -name "tender_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete
echo "已删除 ${RETENTION_DAYS} 天前的备份文件"

# 8. 备份完成
BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)
echo "备份完成!"
echo "备份文件: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo "备份大小: ${BACKUP_SIZE}"
echo "完成时间: $(date)"

# 9. 发送通知（可选）
if [ -n "$BACKUP_WEBHOOK_URL" ]; then
    curl -X POST "$BACKUP_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{\"text\":\"招标系统备份完成\\n文件: ${BACKUP_NAME}.tar.gz\\n大小: ${BACKUP_SIZE}\"}" \
        2>/dev/null || echo "通知发送失败"
fi