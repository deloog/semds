"""监控界面集成测试"""

from fastapi.testclient import TestClient


class TestMonitorUI:
    """监控界面测试"""

    def test_monitor_page_returns_html(self):
        """监控页面应返回HTML"""
        from api.main import app

        client = TestClient(app)
        response = client.get("/monitor/index.html")

        # 验证返回HTML内容
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_monitor_page_contains_required_elements(self):
        """页面应包含必要元素"""
        from api.main import app

        client = TestClient(app)
        response = client.get("/monitor/index.html")

        html = response.text

        # 验证关键元素存在
        assert "<html" in html.lower()
        assert "<head" in html.lower()
        assert "<body" in html.lower()

        # 验证SEMDS相关元素
        assert "SEMDS" in html or "semds" in html.lower()

        # 验证JavaScript存在
        assert "<script" in html.lower()

        # 验证CSS样式存在
        assert "<style" in html.lower() or "stylesheet" in html.lower()

    def test_monitor_page_contains_api_calls(self):
        """页面应包含API调用代码"""
        from api.main import app

        client = TestClient(app)
        response = client.get("/monitor/index.html")

        html = response.text

        # 验证fetch或axios等HTTP调用
        assert "fetch(" in html or "axios" in html or "XMLHttpRequest" in html

        # 验证WebSocket连接代码
        assert "WebSocket(" in html or "websocket" in html.lower()

    def test_monitor_page_contains_task_list_elements(self):
        """页面应包含任务列表相关元素"""
        from api.main import app

        client = TestClient(app)
        response = client.get("/monitor/index.html")

        html = response.text

        # 验证任务列表相关元素
        assert "task" in html.lower() or "任务" in html

        # 验证状态显示相关
        assert "status" in html.lower() or "状态" in html

    def test_monitor_page_contains_progress_elements(self):
        """页面应包含进度显示相关元素"""
        from api.main import app

        client = TestClient(app)
        response = client.get("/monitor/index.html")

        html = response.text

        # 验证进度相关元素
        assert "progress" in html.lower() or "进度" in html or "score" in html.lower()
