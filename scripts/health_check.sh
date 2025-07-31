#!/bin/bash

# 招标系统健康检查脚本
# 用于检查系统各组件的运行状态

set -e

# 配置
FRONTEND_URL="http://localhost:8088"
BACKEND_URL="http://localhost:8000"
REDIS_HOST="localhost"
REDIS_PORT="6379"
MINIO_URL="http://localhost:9000"
PROMETHEUS_URL="http://localhost:9090"
GRAFANA_URL="http://localhost:3000"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查结果
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# 打印函数
print_header() {
    echo "========================================"
    echo "招标系统健康检查"
    echo "检查时间: $(date)"
    echo "========================================"
}

print_check() {
    local service="$1"
    local status="$2"
    local message="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✓${NC} $service: $message"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    elif [ "$status" = "WARNING" ]; then
        echo -e "${YELLOW}⚠${NC} $service: $message"
    else
        echo -e "${RED}✗${NC} $service: $message"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

print_summary() {
    echo "========================================"
    echo "检查摘要:"
    echo "总检查项: $TOTAL_CHECKS"
    echo -e "通过: ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "失败: ${RED}$FAILED_CHECKS${NC}"
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}系统状态: 健康${NC}"
        exit 0
    else
        echo -e "${RED}系统状态: 异常${NC}"
        exit 1
    fi
}

# 检查HTTP服务
check_http_service() {
    local name="$1"
    local url="$2"
    local timeout="${3:-10}"
    
    if command -v curl &> /dev/null; then
        if curl -f -s --max-time "$timeout" "$url" >/dev/null 2>&1; then
            print_check "$name" "OK" "服务正常响应"
        else
            print_check "$name" "FAIL" "服务无响应或返回错误"
        fi
    else
        print_check "$name" "WARNING" "curl未安装，无法检查HTTP服务"
    fi
}

# 检查TCP端口
check_tcp_port() {
    local name="$1"
    local host="$2"
    local port="$3"
    local timeout="${4:-5}"
    
    if command -v nc &> /dev/null; then
        if nc -z -w "$timeout" "$host" "$port" 2>/dev/null; then
            print_check "$name" "OK" "端口 $port 可访问"
        else
            print_check "$name" "FAIL" "端口 $port 不可访问"
        fi
    elif command -v telnet &> /dev/null; then
        if timeout "$timeout" telnet "$host" "$port" </dev/null 2>/dev/null | grep -q "Connected"; then
            print_check "$name" "OK" "端口 $port 可访问"
        else
            print_check "$name" "FAIL" "端口 $port 不可访问"
        fi
    else
        print_check "$name" "WARNING" "nc或telnet未安装，无法检查TCP端口"
    fi
}

# 检查Docker容器
check_docker_container() {
    local name="$1"
    local container_name="$2"
    
    if command -v docker &> /dev/null; then
        if docker ps --format "table {{.Names}}" | grep -q "^$container_name$"; then
            local status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "unknown")
            if [ "$status" = "healthy" ]; then
                print_check "$name" "OK" "容器运行正常且健康"
            elif [ "$status" = "unknown" ]; then
                print_check "$name" "OK" "容器运行正常（无健康检查）"
            else
                print_check "$name" "WARNING" "容器运行但健康状态: $status"
            fi
        else
            print_check "$name" "FAIL" "容器未运行"
        fi
    else
        print_check "$name" "WARNING" "Docker未安装，无法检查容器状态"
    fi
}

# 检查磁盘空间
check_disk_space() {
    local threshold="${1:-85}"
    
    if command -v df &> /dev/null; then
        local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
        if [ "$usage" -lt "$threshold" ]; then
            print_check "磁盘空间" "OK" "使用率 ${usage}% (< ${threshold}%)"
        else
            print_check "磁盘空间" "FAIL" "使用率 ${usage}% (>= ${threshold}%)"
        fi
    else
        print_check "磁盘空间" "WARNING" "df命令不可用"
    fi
}

# 检查内存使用
check_memory_usage() {
    local threshold="${1:-90}"
    
    if command -v free &> /dev/null; then
        local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
        if [ "$usage" -lt "$threshold" ]; then
            print_check "内存使用" "OK" "使用率 ${usage}% (< ${threshold}%)"
        else
            print_check "内存使用" "WARNING" "使用率 ${usage}% (>= ${threshold}%)"
        fi
    else
        print_check "内存使用" "WARNING" "free命令不可用"
    fi
}

# 检查Redis连接
check_redis() {
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null | grep -q "PONG"; then
            print_check "Redis" "OK" "连接正常"
        else
            print_check "Redis" "FAIL" "连接失败"
        fi
    else
        check_tcp_port "Redis" "$REDIS_HOST" "$REDIS_PORT"
    fi
}

# 检查数据库
check_database() {
    if [ -f "./mineru.db" ]; then
        if command -v sqlite3 &> /dev/null; then
            if sqlite3 "./mineru.db" "SELECT 1;" >/dev/null 2>&1; then
                print_check "数据库" "OK" "SQLite数据库可访问"
            else
                print_check "数据库" "FAIL" "SQLite数据库访问失败"
            fi
        else
            print_check "数据库" "OK" "数据库文件存在"
        fi
    else
        print_check "数据库" "FAIL" "数据库文件不存在"
    fi
}

# 主检查流程
main() {
    print_header
    
    echo "1. 检查核心服务..."
    check_http_service "前端服务" "$FRONTEND_URL"
    check_http_service "后端服务" "$BACKEND_URL/health"
    
    echo ""
    echo "2. 检查数据存储..."
    check_database
    check_redis
    check_http_service "MinIO" "$MINIO_URL/minio/health/live"
    
    echo ""
    echo "3. 检查Docker容器..."
    check_docker_container "前端容器" "tender-frontend"
    check_docker_container "后端容器" "tender-backend"
    check_docker_container "工作进程" "tender-worker"
    check_docker_container "Redis容器" "tender-redis"
    check_docker_container "MinIO容器" "tender-minio"
    
    echo ""
    echo "4. 检查监控服务..."
    check_http_service "Prometheus" "$PROMETHEUS_URL/-/healthy"
    check_http_service "Grafana" "$GRAFANA_URL/api/health"
    
    echo ""
    echo "5. 检查系统资源..."
    check_disk_space 85
    check_memory_usage 90
    
    echo ""
    print_summary
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --frontend-url)
            FRONTEND_URL="$2"
            shift 2
            ;;
        --backend-url)
            BACKEND_URL="$2"
            shift 2
            ;;
        --redis-host)
            REDIS_HOST="$2"
            shift 2
            ;;
        --redis-port)
            REDIS_PORT="$2"
            shift 2
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --frontend-url URL    前端服务URL (默认: $FRONTEND_URL)"
            echo "  --backend-url URL     后端服务URL (默认: $BACKEND_URL)"
            echo "  --redis-host HOST     Redis主机 (默认: $REDIS_HOST)"
            echo "  --redis-port PORT     Redis端口 (默认: $REDIS_PORT)"
            echo "  --help               显示此帮助信息"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 运行主检查
main