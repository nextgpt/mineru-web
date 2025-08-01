import os
import torch
import gc
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.api import upload_router, files_router, parsed_router, settings_router
from app.api import task, stats
from app.api.health import router as health_router
from app.api.projects import router as projects_router
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


BACKEND = os.environ.get("BACKEND", "sglang-client")
MODEL_PATH = os.environ.get("MODEL_PATH", "/models/vlm")
SERVER_URL = os.environ.get("SERVER_URL", "http://127.0.0.1:30000")
PRELOAD_MODEL = os.environ.get("PRELOAD_MODEL", False)

def clean_memory():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    gc.collect()

@asynccontextmanager
async def life_span(app: FastAPI):
    print("🔄 启动 MinerU Web 后端服务...")
    # 由于 MinerU 服务已在其他服务器部署，这里不需要加载本地模型
    app.state.predictor = None
    yield
    print("🚪 应用退出，清理资源")
    clean_memory()


app = FastAPI(
    title="MinerU 文档解析系统 API", 
    lifespan=life_span,
    # 增加文件大小限制到100MB
    max_request_size=100 * 1024 * 1024
)

# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)



app.include_router(upload_router, prefix="/api", tags=["upload"])
app.include_router(files_router, prefix="/api", tags=["files"])
app.include_router(parsed_router, prefix="/api", tags=["parsed"])
app.include_router(settings_router, prefix="/api", tags=["settings"])
app.include_router(task.router, prefix="/api", tags=["task"])
app.include_router(stats.router, prefix="/api", tags=["stats"])
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(projects_router, prefix="/api", tags=["projects"])

@app.get("/ping")
def ping():
    return {"msg": "pong"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)