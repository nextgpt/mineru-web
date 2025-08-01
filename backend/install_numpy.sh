#!/bin/bash

# 快速安装 NumPy 脚本
echo "🔧 安装 NumPy..."

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 检测到虚拟环境: $VIRTUAL_ENV"
    pip install numpy>=1.21.0
else
    echo "⚠️  未检测到虚拟环境，使用系统 Python"
    pip install numpy>=1.21.0
fi

echo "✅ NumPy 安装完成"
echo "🚀 现在可以启动应用了："
echo "   uvicorn main:app --host 0.0.0.0 --port 8088 --reload" 