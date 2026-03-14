"""API中间件配置

提供全局错误处理、请求日志等中间件功能。
"""
import logging
import os
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# 是否处于调试模式（开发环境可设为True）
DEBUG_MODE = os.getenv("API_DEBUG", "false").lower() == "true"

__all__ = ["setup_exception_handlers", "setup_logging_middleware"]


def setup_exception_handlers(app: FastAPI) -> None:
    """
    配置全局异常处理
    
    统一处理HTTP异常、验证错误和通用异常，返回标准格式的错误响应。
    
    Args:
        app: FastAPI应用实例
    """
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """处理HTTP异常"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "message": exc.detail
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """处理请求验证错误"""
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": "请求参数验证失败",
                "details": exc.errors()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """处理通用异常"""
        # 记录详细错误信息（服务器端）
        logger.exception(
            f"Unhandled exception: {exc}",
            extra={
                "path": str(request.url.path),
                "method": request.method,
                "client": request.client.host if request.client else "unknown"
            }
        )
        
        # 生产环境返回通用消息，调试模式返回详细信息
        if DEBUG_MODE:
            message = str(exc)
        else:
            message = "服务器内部错误，请稍后重试"
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": message
            }
        )


def setup_logging_middleware(app: FastAPI) -> None:
    """
    配置请求日志中间件
    
    记录每个请求的URL、方法和状态码。
    
    Args:
        app: FastAPI应用实例
    """
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable):
        """记录请求日志"""
        logger.debug(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.debug(f"Response: {response.status_code}")
        return response
