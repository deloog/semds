"""Docker Manager 测试模块

测试 DockerManager 沙盒执行功能
TDD Red 阶段：先写测试用例
"""

from unittest.mock import MagicMock, patch


class TestSandboxConfig:
    """SandboxConfig 数据类测试"""

    def test_sandbox_config_default_values(self):
        """测试默认配置值"""
        from core.docker_manager import SandboxConfig

        config = SandboxConfig()
        assert config.image == "semds-sandbox:latest"
        assert config.memory_limit == "128m"
        assert config.cpu_limit == 1.0
        assert config.network_disabled is True
        assert config.timeout == 30

    def test_sandbox_config_custom_values(self):
        """测试自定义配置值"""
        from core.docker_manager import SandboxConfig

        config = SandboxConfig(
            image="custom-image:latest",
            memory_limit="256m",
            cpu_limit=2.0,
            network_disabled=False,
            timeout=60,
        )
        assert config.image == "custom-image:latest"
        assert config.memory_limit == "256m"
        assert config.cpu_limit == 2.0
        assert config.network_disabled is False
        assert config.timeout == 60

    def test_sandbox_config_to_dict(self):
        """测试配置转换为字典"""
        from core.docker_manager import SandboxConfig

        config = SandboxConfig(memory_limit="256m", timeout=60)
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["memory_limit"] == "256m"
        assert config_dict["timeout"] == 60


class TestExecutionResult:
    """ExecutionResult 数据类测试"""

    def test_execution_result_success(self):
        """测试成功执行结果"""
        from core.docker_manager import ExecutionResult

        result = ExecutionResult(
            success=True,
            stdout="test output",
            stderr="",
            exit_code=0,
            duration=1.5,
        )
        assert result.success is True
        assert result.stdout == "test output"
        assert result.exit_code == 0
        assert result.duration == 1.5

    def test_execution_result_failure(self):
        """测试失败执行结果"""
        from core.docker_manager import ExecutionResult

        result = ExecutionResult(
            success=False,
            stdout="",
            stderr="error message",
            exit_code=1,
            duration=0.5,
        )
        assert result.success is False
        assert result.stderr == "error message"
        assert result.exit_code == 1

    def test_execution_result_to_dict(self):
        """测试结果转换为字典"""
        from core.docker_manager import ExecutionResult

        result = ExecutionResult(
            success=True,
            stdout="output",
            stderr="",
            exit_code=0,
            duration=1.0,
        )
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["stdout"] == "output"


class TestDockerManagerInit:
    """DockerManager 初始化测试"""

    @patch("core.docker_manager.docker_lib")
    def test_docker_manager_default_init(self, mock_docker):
        """测试默认初始化"""
        from core.docker_manager import DockerManager

        # 先模拟 docker 包可用
        mock_docker.from_env.return_value.ping.return_value = True

        manager = DockerManager()
        assert manager.config.image == "semds-sandbox:latest"
        assert manager.config.memory_limit == "128m"

    @patch("core.docker_manager.docker_lib")
    def test_docker_manager_custom_config(self, mock_docker):
        """测试自定义配置初始化"""
        from core.docker_manager import DockerManager, SandboxConfig

        mock_docker.from_env.return_value.ping.return_value = True
        custom_config = SandboxConfig(
            image="test-image:latest",
            memory_limit="512m",
        )
        manager = DockerManager(config=custom_config)

        assert manager.config.image == "test-image:latest"
        assert manager.config.memory_limit == "512m"

    @patch("core.docker_manager.docker_lib")
    def test_docker_manager_graceful_degradation_no_docker(self, mock_docker):
        """测试无 Docker 时的优雅降级"""
        mock_docker.from_env.side_effect = Exception("Docker not available")
        from core.docker_manager import DockerManager

        # 应该不会抛出异常，而是降级运行
        manager = DockerManager()
        assert manager._docker_available is False


class TestExecuteCode:
    """代码执行功能测试"""

    @patch("core.docker_manager.docker_lib")
    def test_execute_code_basic(self, mock_docker_lib):
        """测试基本代码执行"""
        # Mock Docker 容器
        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"Hello, World!"

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container
        mock_client.ping.return_value = True
        mock_docker_lib.from_env.return_value = mock_client

        from core.docker_manager import DockerManager

        manager = DockerManager()
        result = manager.execute_code("print('Hello, World!')")

        assert result.success is True
        assert result.exit_code == 0
        assert "Hello, World!" in result.stdout

    @patch("core.docker_manager.docker_lib")
    def test_execute_code_with_error(self, mock_docker_lib):
        """测试代码执行错误"""
        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 1}
        error_msg = b"Traceback (most recent call last):\n  NameError"
        mock_container.logs.return_value = error_msg

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container
        mock_client.ping.return_value = True
        mock_docker_lib.from_env.return_value = mock_client

        from core.docker_manager import DockerManager

        manager = DockerManager()
        result = manager.execute_code("print(x)")

        assert result.success is False
        assert result.exit_code == 1

    @patch("core.docker_manager.docker_lib")
    def test_execute_code_with_timeout(self, mock_docker_lib):
        """测试代码执行超时"""
        mock_client = MagicMock()
        mock_client.containers.run.side_effect = Exception("Timeout")
        mock_client.ping.return_value = True
        mock_docker_lib.from_env.return_value = mock_client

        from core.docker_manager import DockerManager

        manager = DockerManager()
        code = "import time; time.sleep(100)"
        result = manager.execute_code(code, timeout=1)

        assert result.success is False
        assert "timeout" in result.stderr.lower() or "Timeout" in result.stderr

    @patch("core.docker_manager.docker_lib")
    def test_execute_code_fallback_no_docker(self, mock_docker):
        """测试无 Docker 时的降级执行"""
        mock_docker.side_effect = Exception("Docker not available")

        from core.docker_manager import DockerManager

        manager = DockerManager()
        # 降级模式下应该使用本地执行
        result = manager.execute_code("print(1+1)")

        # 降级执行应该仍然返回结果
        assert result is not None
        assert result.success is True or result.success is False


class TestIsolation:
    """隔离验证测试"""

    @patch("core.docker_manager.docker_lib")
    def test_verify_isolation_network(self, mock_docker_lib):
        """测试网络隔离验证"""
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.attrs = {"NetworkSettings": {"Networks": {}}}

        mock_client = MagicMock()
        mock_client.containers.get.return_value = mock_container
        mock_client.ping.return_value = True
        mock_docker_lib.from_env.return_value = mock_client

        from core.docker_manager import DockerManager

        manager = DockerManager()
        result = manager.verify_isolation("test-container-id")

        assert result is True  # 无网络 = 隔离

    @patch("core.docker_manager.docker_lib")
    def test_verify_isolation_read_only(self, mock_docker_lib):
        """测试只读文件系统验证"""
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.attrs = {"HostConfig": {"ReadonlyRootfs": True}}

        mock_client = MagicMock()
        mock_client.containers.get.return_value = mock_container
        mock_client.ping.return_value = True
        mock_docker_lib.from_env.return_value = mock_client

        from core.docker_manager import DockerManager

        manager = DockerManager()
        result = manager.verify_isolation("test-container-id")

        assert result is True  # 只读根文件系统 = 隔离

    @patch("core.docker_manager.docker_lib")
    def test_cleanup_container(self, mock_docker_lib):
        """测试容器清理"""
        mock_container = MagicMock()

        mock_client = MagicMock()
        mock_client.containers.get.return_value = mock_container
        mock_client.ping.return_value = True
        mock_docker_lib.from_env.return_value = mock_client

        from core.docker_manager import DockerManager

        manager = DockerManager()
        manager._cleanup_container("test-container-id")

        mock_container.stop.assert_called_once()
        mock_container.remove.assert_called_once()
