"""SEMDS 测试配置和基类

提供统一的测试基础设施，包括:
- 基类
- Mock 工具
-  fixtures
"""

import os
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# 确保测试时使用内存数据库或临时数据库
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-api-key")
os.environ.setdefault("DOCKER_HOST", "tcp://localhost:2375")


@pytest.fixture(scope="session")
def test_db_engine():
    """创建测试数据库引擎"""
    from storage.models import Base

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """提供数据库会话"""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """提供临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_claude_response():
    """模拟 Claude API 响应"""
    return """
```python
def calculate(a: float, b: float, op: str) -> float:
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    else:
        raise ValueError(f"Invalid operator: {op}")
```
"""


@pytest.fixture
def mock_anthropic_client(mock_claude_response):
    """提供模拟的 Anthropic 客户端"""
    client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text=mock_claude_response)]
    client.messages.create.return_value = response
    return client


@pytest.fixture
def docker_client_mock():
    """提供模拟的 Docker 客户端"""
    client = MagicMock()
    container = MagicMock()
    container.wait.return_value = {"StatusCode": 0}
    container.logs.return_value = b"test passed"
    client.containers.run.return_value = container
    return client


@pytest.fixture
def sample_task_spec():
    """提供示例任务规格"""
    return {
        "name": "calculator_test",
        "description": "测试计算器函数",
        "target_function_signature": "def calculate(a: float, b: float, op: str) -> float",
        "requirements": [
            "支持操作符: +, -, *, /",
            "除零时抛出ValueError",
            "操作符无效时抛出ValueError",
        ],
    }


@pytest.fixture
def sample_test_code():
    """提供示例测试代码"""
    return """
import pytest

def test_addition():
    assert calculate(2, 3, '+') == 5

def test_subtraction():
    assert calculate(5, 3, '-') == 2

def test_multiplication():
    assert calculate(4, 3, '*') == 12

def test_division():
    assert calculate(10, 2, '/') == 5.0

def test_division_by_zero():
    with pytest.raises(ValueError):
        calculate(1, 0, '/')

def test_invalid_operator():
    with pytest.raises(ValueError):
        calculate(1, 2, '%')
"""


class BaseTestCase:
    """测试基类

    提供通用的测试辅助方法
    """

    @pytest.fixture(autouse=True)
    def setup_test_env(self, temp_dir):
        """设置测试环境"""
        self.temp_dir = temp_dir
        self.original_cwd = os.getcwd()
        os.chdir(temp_dir)
        yield
        os.chdir(self.original_cwd)

    def create_test_file(self, filename: str, content: str) -> Path:
        """创建测试文件"""
        filepath = self.temp_dir / filename
        filepath.write_text(content, encoding="utf-8")
        return filepath

    def assert_file_exists(self, filepath: Path):
        """断言文件存在"""
        assert filepath.exists(), f"File should exist: {filepath}"

    def assert_file_contains(self, filepath: Path, content: str):
        """断言文件包含指定内容"""
        text = filepath.read_text(encoding="utf-8")
        assert content in text, f"File should contain '{content}'"


class MockHelpers:
    """Mock 工具类"""

    @staticmethod
    def patch_claude_api(response_text: str = None):
        """Patch Claude API"""
        if response_text is None:
            response_text = MockHelpers._default_claude_response()

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=response_text)]

        return patch(
            "anthropic.Anthropic.messages.create",
            return_value=mock_response,
        )

    @staticmethod
    def patch_docker():
        """Patch Docker 客户端"""
        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"test output"

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container

        return patch("docker.from_env", return_value=mock_client)

    @staticmethod
    def _default_claude_response():
        return """
```python
def calculate(a: float, b: float, op: str) -> float:
    if op == '+':
        return a + b
    raise ValueError("Invalid operator")
```
"""


# 标记分类器
def pytest_configure(config):
    """配置 pytest 标记"""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "docker: marks tests that require Docker")
    config.addinivalue_line("markers", "api: marks tests that test API endpoints")
    config.addinivalue_line("markers", "evolution: marks tests for evolution logic")
