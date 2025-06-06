from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import upload_router, files_router, parsed_router, settings_router
from app.api import task, stats

app = FastAPI(title="MinerU 文档解析系统 API")

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