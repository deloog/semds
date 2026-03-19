"""测试API中间件"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


class TestErrorHandlingMiddleware:
    """错误处理中间件测试"""

    def test_http_exception_returns_formatted_response(self):
        """HTTP异常应返回统一格式的响应"""
        from api.middleware import setup_exception_handlers

        app = FastAPI()
        setup_exception_handlers(app)

        @app.get("/test-404")
        def test_404():
            raise HTTPException(status_code=404, detail="资源不存在")

        client = TestClient(app)
        response = client.get("/test-404")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert data["message"] == "资源不存在"

    def test_500_exception_returns_safe_response(self):
        """500异常应返回安全的通用响应（生产环境不泄露敏感信息）"""
        import os
        from api.middleware import setup_exception_handlers

        # 确保处于生产模式
        os.environ["API_DEBUG"] = "false"

        app = FastAPI(debug=False)
        setup_exception_handlers(app)

        @app.get("/test-error")
        def test_error():
            raise ValueError("sensitive internal error message")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test-error")

        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "message" in data
        # 生产环境应返回通用消息，不包含敏感信息
        assert "sensitive" not in data["message"].lower()

    def test_500_exception_returns_debug_info_in_debug_mode(self):
        """调试模式下500异常应返回详细信息"""
        import os
        from api.middleware import setup_exception_handlers

        # 启用调试模式
        os.environ["API_DEBUG"] = "true"
        # 重新加载模块以应用新配置
        from importlib import reload
        import api.middleware

        reload(api.middleware)
        from api.middleware import setup_exception_handlers

        app = FastAPI(debug=False)
        setup_exception_handlers(app)

        @app.get("/test-error")
        def test_error():
            raise ValueError("debug error details")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test-error")

        assert response.status_code == 500
        data = response.json()
        # 调试模式应包含详细错误信息
        assert "debug error details" in data["message"]

    def test_validation_error_returns_formatted_response(self):
        """验证错误应返回统一格式的响应"""
        from api.middleware import setup_exception_handlers

        app = FastAPI()
        setup_exception_handlers(app)

        @app.get("/test-validation")
        def test_validation(required_param: str):
            return {"param": required_param}

        client = TestClient(app)
        response = client.get("/test-validation")  # 缺少必需参数

        assert response.status_code == 422
        data = response.json()
        assert "error" in data


class TestRequestLoggingMiddleware:
    """请求日志中间件测试"""

    def test_request_logging_middleware_exists(self):
        """请求日志中间件应存在"""
        from api.middleware import setup_logging_middleware

        app = FastAPI()
        setup_logging_middleware(app)

        @app.get("/test")
        def test():
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
