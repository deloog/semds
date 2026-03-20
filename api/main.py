"""FastAPI主应用

SEMDS API入口模块，提供HTTP API和WebSocket服务。
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.env_loader import load_env

# 加载环境变量
load_env()

__all__ = ["app", "init_database", "close_database"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_database()
    yield
    await close_database()


app = FastAPI(
    title="SEMDS API",
    description="自进化元开发系统 API",
    version="1.1.0",
    lifespan=lifespan,
)


# CORS配置 - 从环境变量读取，生产环境必须配置具体域名
def get_cors_origins() -> list:
    """获取CORS允许的域名列表"""
    origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# 注册路由
from api.routers import approvals, auth, evolution, monitor, tasks

app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(evolution.router, prefix="/api/tasks", tags=["evolution"])
app.include_router(approvals.router, prefix="/api", tags=["approvals"])
app.include_router(monitor.router, prefix="/api", tags=["monitor"])

# 静态文件服务（监控界面）
app.mount("/monitor", StaticFiles(directory="monitor", html=True), name="monitor")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "version": "1.1.0"}


async def init_database() -> None:
    """初始化数据库

    应用启动时调用，初始化数据库连接和表结构。
    目前为占位实现，后续将集成storage.database模块。
    """
    pass


async def close_database() -> None:
    """关闭数据库连接

    应用关闭时调用，清理数据库资源。
    目前为占位实现，后续将集成storage.database模块。
    """
    pass
