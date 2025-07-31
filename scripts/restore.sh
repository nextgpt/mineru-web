#!/bin/bash

# 招标系统恢复脚本
# 用于从备份文件恢复系统数据

set -e

# 检查参数
if [ $# -ne 1 ]; then
    echo "用法: $0 <备份文件路径>"
    echo "示例: $0 /backup/tender-system/tender_backup_20240101_120000.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"
RESTORE_DIR="/tmp/tender_restore_$(date +%s)"

# 检查备份文件是否存在
if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

echo "开始恢复招标系统数据..."
echo "恢复时间: $(date)"
echo "备份文件: $BACKUP_FILE"

# 1. 解压备份文件
echo "解压备份文件..."
mkdir -p "$RESTORE_DIR"
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"
BACKUP_NAME=$(ls "$RESTORE_DIR")
BACKUP_PATH="$RESTORE_DIR/$BACKUP_NAME"

echo "备份内容:"
ls -la "$BACKUP_PATH"

# 2. 显示备份信息
if [ -f "$BACKUP_PATH/backup_info.txt" ]; then
    echo "备份信息:"
    cat "$BACKUP_PATH/backup_info.txt"
    echo ""
fi

# 3. 确认恢复操作
read -p "确认要恢复此备份吗？这将覆盖现有数据 (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "恢复操作已取消"
    rm -rf "$RESTORE_DIR"
    exit 0
fi

# 4. 停止服务
echo "停止服务..."
if command -v docker-compose &> /dev/null; then
    docker-compose down || echo "警告: 服务停止失败或服务未运行"
else
    echo "警告: docker-compose未安装，请手动停止服务"
fi

# 5. 备份当前数据（以防恢复失败）
echo "备份当前数据..."
CURRENT_BACKUP_DIR="/tmp/current_backup_$(date +%s)"
mkdir -p "$CURRENT_BACKUP_DIR"

if [ -f "./mineru.db" ]; then
    cp "./mineru.db" "$CURRENT_BACKUP_DIR/mineru.db.backup"
    echo "当前数据库已备份到: $CURRENT_BACKUP_DIR/mineru.db.backup"
fi

# 6. 恢复数据库
echo "恢复数据库..."
if [ -f "$BACKUP_PATH/database.db" ]; then
    cp "$BACKUP_PATH/database.db" "./mineru.db"
    echo "数据库恢复完成"
else
    echo "警告: 备份中未找到数据库文件"
fi

# 7. 恢复MinIO数据
echo "恢复MinIO数据..."
if [ -d "$BACKUP_PATH/minio_data" ] && command -v docker &> /dev/null; then
    # 创建临时容器恢复数据
    docker run --rm -v minio_data:/target -v "$BACKUP_PATH/minio_data":/source alpine \
        sh -c "rm -rf /target/* && cp -r /source/* /target/" || {
        echo "警告: MinIO数据恢复失败"
    }
    echo "MinIO数据恢复完成"
else
    echo "警告: 未找到MinIO备份数据或Docker未安装"
fi

# 8. 恢复Redis数据
echo "恢复Redis数据..."
if [ -f "$BACKUP_PATH/redis_dump.rdb" ]; then
    # 启动Redis容器（如果未运行）
    docker-compose up -d redis || echo "警告: Redis启动失败"
    sleep 5
    
    # 停止Redis以安全恢复数据
    docker-compose stop redis
    docker cp "$BACKUP_PATH/redis_dump.rdb" tender-redis:/data/dump.rdb || {
        echo "警告: Redis数据恢复失败"
    }
    echo "Redis数据恢复完成"
else
    echo "警告: 未找到Redis备份数据"
fi

# 9. 恢复配置文件
echo "恢复配置文件..."
CONFIG_FILES=(
    "docker-compose.yml"
    ".env"
    "nginx.conf"
    "backend/alembic.ini"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$BACKUP_PATH/$file" ]; then
        # 备份当前配置
        if [ -f "$file" ]; then
            cp "$file" "$CURRENT_BACKUP_DIR/$(basename $file).backup"
        fi
        
        # 恢复配置
        mkdir -p "$(dirname $file)"
        cp "$BACKUP_PATH/$file" "$file"
        echo "已恢复配置文件: $file"
    else
        echo "警告: 备份中未找到配置文件: $file"
    fi
done

# 恢复监控配置
if [ -d "$BACKUP_PATH/monitoring" ]; then
    cp -r "$BACKUP_PATH/monitoring" ./
    echo "监控配置恢复完成"
fi

# 10. 启动服务
echo "启动服务..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
    echo "服务启动完成"
    
    # 等待服务启动
    echo "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    echo "检查服务状态:"
    docker-compose ps
else
    echo "请手动启动服务: docker-compose up -d"
fi

# 11. 验证恢复
echo "验证恢复结果..."
HEALTH_CHECK_URL="http://localhost:8000/health"
if command -v curl &> /dev/null; then
    if curl -f "$HEALTH_CHECK_URL" >/dev/null 2>&1; then
        echo "✓ 后端服务健康检查通过"
    else
        echo "✗ 后端服务健康检查失败"
    fi
else
    echo "请手动验证服务状态"
fi

# 12. 清理临时文件
echo "清理临时文件..."
rm -rf "$RESTORE_DIR"

# 13. 恢复完成
echo "恢复完成!"
echo "完成时间: $(date)"
echo ""
echo "当前数据备份位置: $CURRENT_BACKUP_DIR"
echo "如果恢复有问题，可以使用以下命令回滚:"
echo "  cp $CURRENT_BACKUP_DIR/mineru.db.backup ./mineru.db"
echo "  docker-compose restart"
echo ""
echo "建议在确认系统正常运行后删除临时备份:"
echo "  rm -rf $CURRENT_BACKUP_DIR"