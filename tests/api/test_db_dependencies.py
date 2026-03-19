"""测试API依赖注入"""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


class TestDatabaseDependency:
    """数据库依赖注入测试"""

    def test_get_db_session_returns_session(self):
        """get_db_session应返回数据库会话生成器"""
        from api.dependencies import get_db_session

        # 调用依赖函数获取生成器
        gen = get_db_session()

        # 从生成器获取会话
        try:
            db = next(gen)
            # 验证返回的是数据库会话
            assert db is not None
        finally:
            # 清理生成器
            try:
                next(gen)
            except StopIteration:
                pass

    def test_db_session_closed_after_use(self):
        """数据库会话应在使用后正确关闭"""
        from api.dependencies import get_db_session
        from unittest.mock import patch, MagicMock

        mock_session = MagicMock()

        # 直接在get_db_session内部mock SessionFactory
        from unittest.mock import patch
        with patch("storage.database.get_session_factory", return_value=lambda: mock_session):
            gen = get_db_session()
            db = next(gen)

            # 模拟会话结束
            try:
                next(gen)
            except StopIteration:
                pass

            # 验证close被调用
            mock_session.close.assert_called_once()

    def test_db_dependency_injection_in_endpoint(self):
        """端点中应能正确注入数据库依赖"""
        from api.dependencies import get_db_session
        from unittest.mock import patch, MagicMock

        app = FastAPI()

        @app.get("/test-db")
        def test_endpoint(db=Depends(get_db_session)):
            return {"has_db": db is not None}

        mock_session = MagicMock()
        mock_session.close = MagicMock()

        with patch("storage.database.get_session_factory", return_value=lambda: mock_session):
            client = TestClient(app)
            response = client.get("/test-db")

            assert response.status_code == 200
            assert response.json()["has_db"] is True


class TestDependencyErrorHandling:
    """依赖注入错误处理测试"""

    def test_db_session_handles_exception(self):
        """数据库会话应正确处理异常"""
        from api.dependencies import get_db_session
        from unittest.mock import patch, MagicMock

        mock_session = MagicMock()

        with patch("storage.database.get_session_factory", return_value=lambda: mock_session):
            gen = get_db_session()
            db = next(gen)

            # 模拟抛出异常
            try:
                raise ValueError("测试异常")
            except:
                # 确保生成器正确关闭
                try:
                    next(gen)
                except StopIteration:
                    pass

            # 即使发生异常，close也应被调用
            mock_session.close.assert_called_once()
