"""测试FastAPI主应用"""

from fastapi.testclient import TestClient


class TestFastAPIApp:
    """FastAPI应用测试"""

    def test_health_check_returns_healthy_status(self):
        """健康检查应返回healthy状态"""
        from api.main import app

        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "version" in response.json()

    def test_api_docs_endpoint_exists(self):
        """API文档端点应可访问"""
        from api.main import app

        client = TestClient(app)

        response = client.get("/docs")

        assert response.status_code == 200

    def test_health_check_returns_correct_version(self):
        """健康检查应返回正确版本号"""
        from api.main import app

        client = TestClient(app)

        response = client.get("/health")
        data = response.json()

        assert data["version"] == "1.1.0"

    def test_cors_origins_function_works(self):
        """CORS配置函数应正确解析环境变量"""
        import os

        from api.main import get_cors_origins

        # 测试默认值
        os.environ.pop("CORS_ORIGINS", None)
        origins = get_cors_origins()
        assert "http://localhost:3000" in origins

        # 测试自定义值
        os.environ["CORS_ORIGINS"] = "http://example.com,http://test.com"
        origins = get_cors_origins()
        assert "http://example.com" in origins
        assert "http://test.com" in origins
