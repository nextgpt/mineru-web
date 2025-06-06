from .upload import router as upload_router
from .files import router as files_router
from .parsed import router as parsed_router
from .settings import router as settings_router
from . import task
from . import stats

routers = [
    upload_router,
    files_router,
    parsed_router,
    settings_router,
    task.router,  # 注册 task 路由
    stats.router,  # 注册 stats 路由
] 