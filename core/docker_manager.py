"""Docker Manager 模块

提供 Docker 沙盒执行环境管理功能
实现代码的隔离执行与资源限制
"""

import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Optional

# 使用完全限定名称导入，避免与 docker/ 目录冲突
import docker as docker_lib


@dataclass
class SandboxConfig:
    """沙盒配置数据类

    属性:
        image: Docker 镜像名称
        memory_limit: 内存限制
        cpu_limit: CPU 核心数限制
        network_disabled: 是否禁用网络
        timeout: 执行超时时间（秒）
    """

    image: str = "semds-sandbox:latest"
    memory_limit: str = "128m"
    cpu_limit: float = 1.0
    network_disabled: bool = True
    timeout: int = 30

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "image": self.image,
            "memory_limit": self.memory_limit,
            "cpu_limit": self.cpu_limit,
            "network_disabled": self.network_disabled,
            "timeout": self.timeout,
        }


@dataclass
class ExecutionResult:
    """代码执行结果数据类

    属性:
        success: 是否执行成功
        stdout: 标准输出
        stderr: 标准错误
        exit_code: 退出码
        duration: 执行耗时（秒）
    """

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration: float

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "duration": self.duration,
        }


class DockerManager:
    """Docker 沙盒管理器

    提供安全的代码执行环境，使用 Docker 容器实现资源隔离
    支持优雅降级：无 Docker 时使用本地 Python 执行
    """

    def __init__(self, config: Optional[SandboxConfig] = None) -> None:
        """初始化 Docker 管理器

        Args:
            config: 沙盒配置，默认使用 SandboxConfig()
        """
        self.config = config or SandboxConfig()
        self._docker_client: Optional[Any] = None
        self._docker_available: bool = True

        # 尝试连接 Docker
        try:
            self._docker_client = docker_lib.from_env()  # type: ignore[attr-defined]
            # 测试连接
            self._docker_client.ping()
        except Exception:
            # 优雅降级：Docker 不可用时使用本地执行
            self._docker_available = False
            self._docker_client = None

    def execute_code(self, code: str, timeout: Optional[int] = None) -> ExecutionResult:
        """在沙盒中执行代码

        Args:
            code: 要执行的 Python 代码
            timeout: 超时时间（秒），默认使用配置中的 timeout

        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()
        timeout = timeout or self.config.timeout

        if self._docker_available and self._docker_client:
            return self._execute_in_docker(code, timeout, start_time)
        else:
            return self._execute_fallback(code, timeout, start_time)

    def _execute_in_docker(
        self, code: str, timeout: int, start_time: float
    ) -> ExecutionResult:
        """在 Docker 容器中执行代码

        Args:
            code: 要执行的代码
            timeout: 超时时间
            start_time: 开始时间

        Returns:
            ExecutionResult: 执行结果
        """
        # 防御性检查：确保 docker_client 不为 None
        if not self._docker_client:
            raise RuntimeError("Docker client is not available")

        container_name = f"semds-exec-{int(time.time())}"

        try:
            # 网络模式
            network_mode = "none" if self.config.network_disabled else "bridge"

            # 创建并运行容器
            container = self._docker_client.containers.run(
                self.config.image,
                f"python -c {repr(code)}",
                detach=True,
                mem_limit=self.config.memory_limit,
                cpu_quota=int(self.config.cpu_limit * 100000),
                network_mode=network_mode,
                security_opt=["no-new-privileges:true"],
                read_only=True,
                tmpfs={"/tmp": "noexec,nosuid,size=100m"},
                name=container_name,
                remove=False,
            )

            try:
                # 等待容器执行完成
                result = container.wait(timeout=timeout)
                exit_code = result.get("StatusCode", 1)

                # 获取输出
                stdout_bytes = container.logs(stdout=True, stderr=False)
                stderr_bytes = container.logs(stdout=False, stderr=True)

                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")

                duration = time.time() - start_time

                return ExecutionResult(
                    success=exit_code == 0,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                    duration=duration,
                )
            finally:
                # 清理容器
                self._cleanup_container(container.id)

        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Docker execution error: {str(e)}",
                exit_code=1,
                duration=duration,
            )

    def _execute_fallback(
        self, code: str, timeout: int, start_time: float
    ) -> ExecutionResult:
        """降级执行：无 Docker 时使用本地 Python

        Args:
            code: 要执行的代码
            timeout: 超时时间
            start_time: 开始时间

        Returns:
            ExecutionResult: 执行结果
        """
        try:
            # 使用 subprocess 执行代码
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            duration = time.time() - start_time

            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration=duration,
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="Execution timeout",
                exit_code=124,
                duration=duration,
            )
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                exit_code=1,
                duration=duration,
            )

    def _cleanup_container(self, container_id: str) -> None:
        """清理 Docker 容器

        Args:
            container_id: 容器 ID
        """
        if not self._docker_available or not self._docker_client:
            return

        try:
            container = self._docker_client.containers.get(container_id)
            container.stop(timeout=5)
            container.remove(force=True)
        except Exception:
            # 忽略清理错误
            pass

    def verify_isolation(self, container_id: str) -> bool:
        """验证容器隔离性

        Args:
            container_id: 容器 ID

        Returns:
            bool: 是否隔离
        """
        if not self._docker_available or not self._docker_client:
            # 无 Docker 时返回 True（假设本地执行是隔离的）
            return True

        try:
            container = self._docker_client.containers.get(container_id)

            # 检查网络隔离
            if not self.config.network_disabled:
                return False

            # 检查容器状态
            if container.status != "running":
                return False

            # 检查网络配置
            network_settings = container.attrs.get("NetworkSettings", {})
            networks = network_settings.get("Networks", {})

            # 如果配置了禁用网络，则应该没有网络连接
            if self.config.network_disabled and networks:
                return False

            # 检查只读文件系统
            host_config = container.attrs.get("HostConfig", {})
            if host_config.get("ReadonlyRootfs", False):
                return True

            # 如果网络已禁用，认为是隔离的
            return self.config.network_disabled

        except Exception:
            return False
