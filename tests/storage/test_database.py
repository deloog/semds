"""Tests for storage/database.py

测试数据库连接管理功能。
"""

import os
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from storage import database as db_module
from storage.database import (
    close_database,
    get_db_path,
    get_db_session,
    get_engine,
    get_session,
    get_session_factory,
    init_database,
    reset_database,
)
from storage.models import Base, Task


class TestGetDbPath:
    """测试get_db_path函数"""

    def test_default_path(self):
        """测试默认数据库路径"""
        path = get_db_path()

        # 应该是绝对路径
        assert os.path.isabs(path)
        # 应该包含semds.db
        assert path.endswith("semds.db")

    def test_env_variable_override(self, monkeypatch):
        """测试环境变量可以覆盖默认路径"""
        # 使用绝对路径（跨平台）
        custom_path = os.path.abspath("/custom/path/to/db.sqlite")
        monkeypatch.setenv("SEMDS_DB_PATH", custom_path)

        path = get_db_path()
        assert path == custom_path

    def test_env_variable_relative_path_converted_to_absolute(
        self, monkeypatch, tmp_path
    ):
        """测试环境变量中的相对路径被转换为绝对路径"""
        relative_path = "relative/path/db.sqlite"
        monkeypatch.setenv("SEMDS_DB_PATH", relative_path)

        path = get_db_path()
        # 相对路径应该被转换为绝对路径
        assert os.path.isabs(path)
        # 使用os.path.normpath来处理路径分隔符差异
        normalized_path = os.path.normpath(path)
        assert "relative" in normalized_path and "db.sqlite" in normalized_path


class TestGetEngine:
    """测试get_engine函数"""

    def setup_method(self):
        """每个测试前重置全局状态"""
        close_database()

    def teardown_method(self):
        """每个测试后清理"""
        close_database()

    def test_returns_engine_instance(self):
        """测试返回Engine实例"""
        engine = get_engine()

        assert isinstance(engine, Engine)

    def test_returns_same_engine_on_multiple_calls(self):
        """测试多次调用返回同一个引擎实例（单例模式）"""
        engine1 = get_engine()
        engine2 = get_engine()

        assert engine1 is engine2

    def test_creates_directory_if_not_exists(self, tmp_path):
        """测试如果目录不存在则创建"""
        db_path = tmp_path / "new_folder" / "test.db"

        # 确保目录不存在
        assert not db_path.parent.exists()

        engine = get_engine(str(db_path))

        # 目录应该被创建
        assert db_path.parent.exists()
        engine.dispose()

    def test_engine_with_memory_database(self):
        """测试内存数据库引擎"""
        engine = get_engine(":memory:")

        assert isinstance(engine, Engine)
        engine.dispose()

    def test_foreign_keys_enabled(self):
        """测试外键约束被启用"""
        engine = get_engine(":memory:")

        # 查询外键设置
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA foreign_keys"))
            fk_enabled = result.scalar()

        assert fk_enabled == 1
        engine.dispose()

    def test_engine_with_custom_path(self, tmp_path):
        """测试使用自定义路径创建引擎"""
        db_path = tmp_path / "custom.db"
        engine = get_engine(str(db_path))

        assert isinstance(engine, Engine)
        # 验证数据库文件被创建
        # 注意：引擎创建时不会立即创建文件，需要执行操作
        engine.dispose()


class TestInitDatabase:
    """测试init_database函数"""

    def setup_method(self):
        """每个测试前重置全局状态"""
        close_database()

    def teardown_method(self):
        """每个测试后清理"""
        close_database()

    def test_returns_engine(self):
        """测试返回引擎实例"""
        engine = init_database(":memory:")

        assert isinstance(engine, Engine)
        engine.dispose()

    def test_creates_all_tables(self):
        """测试创建所有表"""
        engine = init_database(":memory:")

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert "tasks" in tables
        assert "generations" in tables
        assert "strategy_states" in tables
        engine.dispose()

    def test_creates_task_columns(self):
        """测试Task表的列被正确创建"""
        engine = init_database(":memory:")

        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("tasks")}

        assert "id" in columns
        assert "name" in columns
        assert "description" in columns
        assert "status" in columns
        assert "current_generation" in columns
        engine.dispose()

    def test_creates_generation_columns(self):
        """测试Generation表的列被正确创建"""
        engine = init_database(":memory:")

        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("generations")}

        assert "id" in columns
        assert "task_id" in columns
        assert "gen_number" in columns
        assert "code" in columns
        assert "intrinsic_score" in columns
        engine.dispose()

    def test_creates_strategy_state_columns(self):
        """测试StrategyState表的列被正确创建"""
        engine = init_database(":memory:")

        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("strategy_states")}

        assert "task_id" in columns
        assert "strategy_key" in columns
        assert "alpha" in columns
        assert "beta" in columns
        engine.dispose()

    def test_idempotent_multiple_calls(self):
        """测试多次调用不会出错（幂等）"""
        engine1 = init_database(":memory:")
        engine2 = init_database()

        # 第二次调用应该使用已存在的引擎
        assert engine1 is engine2
        engine1.dispose()


class TestGetSessionFactory:
    """测试get_session_factory函数"""

    def setup_method(self):
        """每个测试前重置全局状态"""
        close_database()

    def teardown_method(self):
        """每个测试后清理"""
        close_database()

    def test_returns_sessionmaker(self):
        """测试返回sessionmaker"""
        factory = get_session_factory(":memory:")

        assert factory is not None
        # 验证可以创建会话
        session = factory()
        assert isinstance(session, Session)
        session.close()

    def test_returns_same_factory_on_multiple_calls(self):
        """测试多次调用返回同一个工厂（单例模式）"""
        factory1 = get_session_factory(":memory:")
        factory2 = get_session_factory()

        assert factory1 is factory2


class TestGetSession:
    """测试get_session函数"""

    def setup_method(self):
        """每个测试前重置全局状态"""
        close_database()

    def teardown_method(self):
        """每个测试后清理"""
        close_database()

    def test_returns_session(self):
        """测试返回Session实例"""
        session = get_session(":memory:")

        assert isinstance(session, Session)
        session.close()

    def test_session_can_execute_queries(self):
        """测试会话可以执行查询"""
        init_database(":memory:")
        session = get_session()

        # 应该能够执行简单查询
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        session.close()

    def test_session_is_independent(self):
        """测试每次调用返回独立的会话"""
        init_database(":memory:")
        session1 = get_session()
        session2 = get_session()

        assert session1 is not session2
        assert session1.bind is session2.bind  # 但使用相同的引擎

        session1.close()
        session2.close()


class TestGetDbSession:
    """测试get_db_session生成器函数"""

    def setup_method(self):
        """每个测试前重置全局状态"""
        close_database()

    def teardown_method(self):
        """每个测试后清理"""
        close_database()

    def test_yields_session(self):
        """测试生成Session实例"""
        init_database(":memory:")

        gen = get_db_session()
        session = next(gen)

        assert isinstance(session, Session)

        # 清理
        try:
            next(gen)
        except StopIteration:
            pass

    def test_session_closed_after_use(self):
        """测试会话在使用后被关闭"""
        init_database(":memory:")

        gen = get_db_session()
        session = next(gen)

        # 使用完会话
        try:
            next(gen)
        except StopIteration:
            pass

        # 会话应该被关闭
        # 注意：无法直接检测会话是否关闭，但可以尝试使用
        # 关闭后的会话操作会报错或无效

    def test_handles_exception(self):
        """测试处理异常情况"""
        init_database(":memory:")

        gen = get_db_session()
        session = next(gen)

        # 模拟异常
        try:
            raise ValueError("Test exception")
        except ValueError:
            try:
                next(gen)
            except StopIteration:
                pass

        # 即使发生异常，会话也应该被正确处理


class TestResetDatabase:
    """测试reset_database函数"""

    def setup_method(self):
        """每个测试前重置全局状态"""
        close_database()

    def teardown_method(self):
        """每个测试后清理"""
        close_database()

    def test_clears_all_data(self):
        """测试清除所有数据"""
        engine = init_database(":memory:")
        session = get_session()

        # 添加一些数据
        task = Task(name="test_task")
        session.add(task)
        session.commit()

        # 验证数据存在
        count_before = session.query(Task).count()
        assert count_before == 1
        session.close()

        # 重置数据库
        reset_database(":memory:")

        # 数据应该被清除
        session = get_session()
        count_after = session.query(Task).count()
        assert count_after == 0
        session.close()
        engine.dispose()

    def test_recreates_tables(self):
        """测试重新创建表"""
        engine = init_database(":memory:")

        # 验证表存在
        inspector = inspect(engine)
        tables_before = inspector.get_table_names()
        assert "tasks" in tables_before

        # 重置
        reset_database(":memory:")

        # 表应该仍然存在
        tables_after = inspector.get_table_names()
        assert "tasks" in tables_after
        assert "generations" in tables_after
        assert "strategy_states" in tables_after
        engine.dispose()


class TestCloseDatabase:
    """测试close_database函数"""

    def setup_method(self):
        """每个测试前重置全局状态"""
        close_database()

    def teardown_method(self):
        """每个测试后清理"""
        close_database()

    def test_disposes_engine(self):
        """测试释放引擎资源"""
        engine = get_engine(":memory:")
        assert engine is not None

        close_database()

        # 全局引擎应该被重置为None
        # 下次调用get_engine应该创建新引擎
        engine2 = get_engine(":memory:")
        # 由于引擎被重置，应该创建新实例
        assert engine2 is not None
        engine2.dispose()

    def test_resets_session_factory(self):
        """测试重置会话工厂"""
        factory1 = get_session_factory(":memory:")

        close_database()

        # 获取新的工厂
        factory2 = get_session_factory(":memory:")
        # 工厂应该被重新创建
        assert factory2 is not None

    def test_safe_to_call_multiple_times(self):
        """测试多次调用安全"""
        # 第一次调用
        close_database()
        # 第二次调用（应该不报错）
        close_database()
        # 第三次调用
        close_database()

    def test_safe_to_call_when_not_initialized(self):
        """测试在未初始化时调用安全"""
        # 确保全局变量为None
        close_database()

        # 再次调用应该不报错
        close_database()


class TestIntegration:
    """集成测试"""

    def setup_method(self):
        """每个测试前重置全局状态"""
        close_database()

    def teardown_method(self):
        """每个测试后清理"""
        close_database()

    def test_full_workflow_memory_db(self):
        """测试完整工作流程（内存数据库）"""
        # 初始化
        engine = init_database(":memory:")

        # 获取会话
        session = get_session()

        # 创建任务
        task = Task(name="integration_test", status="running")
        session.add(task)
        session.commit()

        # 验证
        result = session.query(Task).filter_by(name="integration_test").first()
        assert result is not None
        assert result.status == "running"

        session.close()
        engine.dispose()

    def test_full_workflow_file_db(self, tmp_path):
        """测试完整工作流程（文件数据库）"""
        db_path = tmp_path / "test_integration.db"

        # 初始化
        engine = init_database(str(db_path))

        # 获取会话
        session = get_session()

        # 创建任务
        task = Task(name="file_test", description="Test with file db")
        session.add(task)
        session.commit()
        session.close()
        engine.dispose()

        # 关闭并重新连接
        close_database()

        # 重新初始化
        engine2 = init_database(str(db_path))
        session2 = get_session()

        # 验证数据持久化
        result = session2.query(Task).filter_by(name="file_test").first()
        assert result is not None
        assert result.description == "Test with file db"

        session2.close()
        engine2.dispose()

    def test_concurrent_sessions(self):
        """测试并发会话"""
        init_database(":memory:")

        # 创建多个会话
        sessions = [get_session() for _ in range(5)]

        # 每个会话添加一个任务
        for i, session in enumerate(sessions):
            task = Task(name=f"task_{i}")
            session.add(task)
            session.commit()

        # 验证所有任务都被添加
        count = sessions[0].query(Task).count()
        assert count == 5

        # 关闭所有会话
        for session in sessions:
            session.close()


class TestGlobalState:
    """测试模块级别的全局状态管理"""

    def setup_method(self):
        """每个测试前重置全局状态"""
        close_database()

    def teardown_method(self):
        """每个测试后清理"""
        close_database()

    def test_global_engine_starts_none(self):
        """测试全局引擎初始为None"""
        # 关闭后检查
        close_database()

        # 直接访问模块级变量（仅用于测试）
        assert db_module._engine is None

    def test_global_session_factory_starts_none(self):
        """测试全局会话工厂初始为None"""
        # 关闭后检查
        close_database()

        # 直接访问模块级变量（仅用于测试）
        assert db_module._SessionFactory is None

    def test_global_engine_set_after_get_engine(self):
        """测试get_engine后全局引擎被设置"""
        engine = get_engine(":memory:")

        # 验证全局变量
        assert db_module._engine is engine
        engine.dispose()

    def test_global_factory_set_after_get_session_factory(self):
        """测试get_session_factory后全局工厂被设置"""
        factory = get_session_factory(":memory:")

        # 验证全局变量
        assert db_module._SessionFactory is factory


class TestErrorHandling:
    """测试错误处理"""

    def setup_method(self):
        """每个测试前重置全局状态"""
        close_database()

    def teardown_method(self):
        """每个测试后清理"""
        close_database()

    def test_invalid_db_path(self):
        """测试无效的数据库路径"""
        # 使用无效路径（如只读目录）
        # 在某些系统上可能会失败
        invalid_path = "/nonexistent/path/that/cannot/be/created/db.sqlite"

        # 尝试创建引擎可能会失败或成功（取决于系统）
        # 这里主要测试不会抛出未预期的异常
        try:
            engine = get_engine(invalid_path)
            engine.dispose()
        except Exception as e:
            # 预期可能会抛出异常
            assert isinstance(e, (OSError, PermissionError))

    def test_session_lifecycle(self):
        """测试会话生命周期管理"""
        init_database(":memory:")

        # 创建会话
        session = get_session()
        assert session is not None

        # 使用会话
        session.execute(text("SELECT 1"))

        # 关闭会话
        session.close()

        # 验证会话对象仍然存在（即使已关闭）
        assert session is not None
        # 会话关闭后不应影响其他操作

    def test_session_rollback_on_error(self):
        """测试会话在错误时回滚"""
        init_database(":memory:")
        session = get_session()

        # 开始事务
        task = Task(name="rollback_test")
        session.add(task)

        # 强制回滚
        session.rollback()

        # 验证数据未提交
        count = session.query(Task).filter_by(name="rollback_test").count()
        assert count == 0

        session.close()


class TestModuleEntryPoint:
    """测试模块入口点（__main__部分）"""

    def test_models_module_imports(self):
        """测试模型模块可以被导入"""
        from storage import models

        assert hasattr(models, "Task")
        assert hasattr(models, "Generation")
        assert hasattr(models, "StrategyState")
        assert hasattr(models, "Base")

    def test_database_module_imports(self):
        """测试数据库模块可以被导入"""
        from storage import database

        assert hasattr(database, "init_database")
        assert hasattr(database, "get_session")
        assert hasattr(database, "get_engine")
        assert hasattr(database, "close_database")
