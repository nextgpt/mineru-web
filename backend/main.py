import os
import torch
import gc
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import upload_router, files_router, parsed_router, settings_router
from app.api import task, stats
from contextlib import asynccontextmanager


BACKEND = os.environ.get("BACKEND", "sglang-engine")
MODEL_PATH = os.environ.get("MODEL_PATH", "/models/vlm")
SERVER_URL = os.environ.get("SERVER_URL", "http://127.0.0.1:30000")

def clean_memory():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    gc.collect()

@asynccontextmanager
async def life_span(app: FastAPI):
    print("🔄 正在加载模型...")
    from mineru.backend.vlm.vlm_analyze import ModelSingleton

    app.state.predictor = ModelSingleton().get_model(BACKEND, MODEL_PATH, SERVER_URL)
    print("✅ 模型加载完成")
    yield
    print("🚪 应用退出，清理模型")
    clean_memory()


app = FastAPI(title="MinerU 文档解析系统 API", lifespan=life_span)

# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(upload_router, prefix="/api", tags=["upload"])
app.include_router(files_router, prefix="/api", tags=["files"])
app.include_router(parsed_router, prefix="/api", tags=["parsed"])
app.include_router(settings_router, prefix="/api", tags=["settings"])
app.include_router(task.router, prefix="/api", tags=["task"])
app.include_router(stats.router, prefix="/api", tags=["stats"])

@app.get("/ping")
def ping():
    return {"msg": "pong"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)