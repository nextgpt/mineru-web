import os
import sys

# 添加项目根目录到 Python 路径
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.append(PROJECT_ROOT)

from app.services.file_parser_worker import run_worker

if __name__ == "__main__":
    run_worker() 