"""Application deployment using subprocess + tempfile (No Docker)."""

import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class DeploymentStatus(Enum):
    """Deployment lifecycle states."""

    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class DeploymentConfig:
    """Configuration for application deployment."""

    name: str
    app_type: str = "fastapi"  # 'fastapi', 'flask', 'cli'
    port: int = 8000
    python_version: str = "3.11"
    dependencies: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""

    status: DeploymentStatus
    service_url: Optional[str] = None
    process_id: Optional[int] = None
    work_dir: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    error: Optional[str] = None
    start_time_ms: int = 0


class ApplicationDeployer:
    """
    Deploy applications using subprocess + tempfile.

    No Docker required - runs Python processes directly in
    isolated temporary directories.
    """

    def __init__(self, deployment_dir: str = "storage/deployments"):
        self.deployment_dir = Path(deployment_dir)
        self.deployment_dir.mkdir(parents=True, exist_ok=True)
        self._active_processes: Dict[str, subprocess.Popen] = {}
        self._work_dirs: Dict[str, Path] = {}

    def deploy(
        self,
        app_code: str,
        config: DeploymentConfig,
        test_code: Optional[str] = None,
    ) -> DeploymentResult:
        """
        Deploy application as subprocess in isolated directory.

        Args:
            app_code: Main application code
            config: Deployment configuration
            test_code: Optional test code

        Returns:
            DeploymentResult with process info
        """
        start_time = time.time()
        logs = []

        try:
            # Step 1: Create isolated workspace
            work_dir = self.deployment_dir / config.name
            work_dir.mkdir(exist_ok=True)
            self._work_dirs[config.name] = work_dir
            logs.append(f"[1/4] Workspace: {work_dir}")

            # Step 2: Write application files
            self._write_app_files(work_dir, app_code, config, test_code)
            logs.append("[2/4] Files written")

            # Step 3: Install dependencies in workspace
            if config.dependencies:
                logs.append(f"[3/4] Installing deps: {config.dependencies}")
                self._install_deps(work_dir, config.dependencies, logs)

            # Step 4: Start subprocess
            logs.append("[4/4] Starting process...")
            process = self._start_process(work_dir, config, logs)

            if process is None:
                return DeploymentResult(
                    status=DeploymentStatus.FAILED,
                    error="Failed to start process",
                    logs=logs,
                    work_dir=str(work_dir),
                    start_time_ms=int((time.time() - start_time) * 1000),
                )

            self._active_processes[config.name] = process

            service_url = f"http://localhost:{config.port}"

            logs.append(f"Process started (PID: {process.pid})")

            return DeploymentResult(
                status=DeploymentStatus.RUNNING,
                service_url=service_url,
                process_id=process.pid,
                work_dir=str(work_dir),
                logs=logs,
                start_time_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            return DeploymentResult(
                status=DeploymentStatus.FAILED,
                error=str(e),
                logs=logs + [f"[ERROR] {e}"],
                start_time_ms=int((time.time() - start_time) * 1000),
            )

    def _write_app_files(
        self,
        work_dir: Path,
        app_code: str,
        config: DeploymentConfig,
        test_code: Optional[str],
    ) -> None:
        """Write application files to workspace."""
        # Main app file
        app_filename = "main.py" if config.app_type in ("fastapi", "cli") else "app.py"
        (work_dir / app_filename).write_text(app_code, encoding="utf-8")

        # Requirements
        base_deps = []
        if config.app_type == "fastapi":
            base_deps = ["fastapi", "uvicorn[standard]"]
        elif config.app_type == "flask":
            base_deps = ["flask"]

        all_deps = list(set(base_deps + config.dependencies))
        (work_dir / "requirements.txt").write_text("\n".join(all_deps))

        # Tests
        if test_code:
            (work_dir / "test_app.py").write_text(test_code, encoding="utf-8")

    def _install_deps(self, work_dir: Path, deps: List[str], logs: List[str]) -> None:
        """Install dependencies using pip."""
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--target",
                    str(work_dir / "lib"),
                ]
                + deps,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                logs.append(f"[WARN] pip install: {result.stderr[:200]}")
        except Exception as e:
            logs.append(f"[WARN] Failed to install deps: {e}")

    def _start_process(
        self,
        work_dir: Path,
        config: DeploymentConfig,
        logs: List[str],
    ) -> Optional[subprocess.Popen]:
        """Start application as subprocess."""
        env = os.environ.copy()
        env.update(config.env_vars)
        env["PYTHONPATH"] = str(work_dir / "lib")
        env["PORT"] = str(config.port)

        if config.app_type == "fastapi":
            cmd = [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "0.0.0.0",
                "--port",
                str(config.port),
                "--log-level",
                "info",
            ]
        elif config.app_type == "flask":
            cmd = [
                sys.executable,
                "-m",
                "flask",
                "run",
                "--host=0.0.0.0",
                f"--port={config.port}",
            ]
            env["FLASK_APP"] = "app.py"
        else:
            cmd = [sys.executable, "main.py"]

        try:
            process = subprocess.Popen(
                cmd,
                cwd=str(work_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
                ),
            )

            # Quick check if process started
            time.sleep(1)
            if process.poll() is not None:
                # Process exited immediately
                stdout, stderr = process.communicate()
                logs.append(f"[ERROR] Process exited: {stderr.decode()[:500]}")
                return None

            return process

        except Exception as e:
            logs.append(f"[ERROR] Failed to start: {e}")
            return None

    def stop(self, name: str) -> bool:
        """Stop a running deployment."""
        process = self._active_processes.get(name)
        if process is None:
            return False

        try:
            # Terminate process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

            del self._active_processes[name]
            return True
        except Exception:
            return False

    def get_logs(self, name: str, tail: int = 100) -> List[str]:
        """Get process logs (limited - processes use pipes)."""
        # Note: Real implementation would need log file or queue
        # For now, return placeholder
        return ["Logs available in process stdout/stderr"]

    def is_running(self, name: str) -> bool:
        """Check if deployment is running."""
        process = self._active_processes.get(name)
        if process is None:
            return False
        return process.poll() is None

    def list_active(self) -> Dict[str, dict]:
        """List all active deployments."""
        result = {}
        for name, process in list(self._active_processes.items()):
            if process.poll() is None:
                result[name] = {
                    "pid": process.pid,
                    "work_dir": str(self._work_dirs.get(name, "")),
                }
        return result

    def redeploy(self, name: str, new_code: Optional[str] = None) -> DeploymentResult:
        """Redeploy with optional new code."""
        # Stop current
        self.stop(name)
        time.sleep(1)

        # Update code if provided
        work_dir = self._work_dirs.get(name)
        if work_dir and new_code:
            app_file = work_dir / "main.py"
            if app_file.exists():
                app_file.write_text(new_code, encoding="utf-8")

        # Re-read config and redeploy
        config = DeploymentConfig(name=name)
        if work_dir:
            app_code = (work_dir / "main.py").read_text(encoding="utf-8")
            return self.deploy(app_code, config)

        return DeploymentResult(
            status=DeploymentStatus.FAILED,
            error=f"Deployment {name} not found",
        )
