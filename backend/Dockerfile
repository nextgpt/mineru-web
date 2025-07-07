# Use the official sglang image
FROM lmsysorg/sglang:v0.4.8.post1-cu126

# Install libgl for opencv support
RUN apt-get update && apt-get install -y libgl1 && apt-get clean && rm -rf /var/lib/apt/lists/*


WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN python3 -m pip install -U -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

# Download models and update the configuration file
# 模型文件外部挂载
# RUN /bin/bash -c "mineru-models-download -s modelscope -m all"

# 复制应用代码和启动脚本
COPY . .
RUN chmod +x /app/entrypoint.sh

# 设置入口点
ENTRYPOINT ["/app/entrypoint.sh"]

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 