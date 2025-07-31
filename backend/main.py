import os
import torch
import gc
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.api import upload_router, files_router, parsed_router, settings_router
from app.api import task, stats, websocket, tender
from contextlib import asynccontextmanager
from mineru.cli.fast_api import parse_pdf


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
    # 启动时初始化
    if not PRELOAD_MODEL:
        print("🔄 不预加载模型...")
        app.state.predictor = None
    else:
        print("🔄 正在加载模型...")
        from mineru.backend.vlm.vlm_analyze import ModelSingleton

        app.state.predictor = ModelSingleton().get_model(BACKEND, MODEL_PATH, SERVER_URL)
        print("✅ 模型加载完成")
    
    # 启动WebSocket监听器
    print("🔄 启动WebSocket监听器...")
    from app.api.websocket import startup_websocket_listener
    await startup_websocket_listener()
    print("✅ WebSocket监听器启动完成")
    
    yield
    
    # 关闭时清理
    print("🚪 应用退出，清理资源...")
    
    # 停止WebSocket监听器
    from app.api.websocket import shutdown_websocket_listener
    await shutdown_websocket_listener()
    print("✅ WebSocket监听器已停止")
    
    # 清理模型
    clean_memory()
    print("✅ 资源清理完成")


app = FastAPI(title="MinerU 文档解析系统 API", lifespan=life_span)

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
app.include_router(websocket.router, prefix="/api", tags=["websocket"])
app.include_router(tender.router, prefix="/api", tags=["tender"])

@app.get("/ping")
def ping():
    return {"msg": "pong"}


app.add_api_route("/api/file_parse", parse_pdf, methods=['POST'])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)