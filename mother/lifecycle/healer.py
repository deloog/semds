"""Auto-healing for subprocess-based deployments."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional

from .deployer import ApplicationDeployer, DeploymentConfig, DeploymentStatus
from .monitor import Alert, HealthStatus, ServiceMonitor


class HealingAction(Enum):
    """Types of healing actions."""

    RESTART = "restart"
    HOTFIX = "hotfix"
    PORT_CHANGE = "port_change"
    INVESTIGATE = "investigate"


@dataclass
class HealingResult:
    """Result of a healing attempt."""

    success: bool
    action: HealingAction
    message: str
    timestamp: datetime = datetime.now


class LogAnalyzer:
    """Analyze process output to identify root causes."""

    ERROR_PATTERNS = {
        "syntax_error": re.compile(r"SyntaxError|IndentationError"),
        "import_error": re.compile(r"ImportError|ModuleNotFoundError"),
        "port_in_use": re.compile(r"Address already in use|port.*in use|OSError.*port"),
        "startup_error": re.compile(r"Error.*starting|Failed.*bind"),
    }

    def analyze(self, logs: List[str]) -> Dict[str, List[str]]:
        """Analyze logs and return detected errors."""
        findings = {key: [] for key in self.ERROR_PATTERNS.keys()}

        for line in logs:
            for error_type, pattern in self.ERROR_PATTERNS.items():
                if pattern.search(line):
                    findings[error_type].append(line)

        return {k: v for k, v in findings.items() if v}


class PatchGenerator:
    """Generate code patches for common issues."""

    def add_health_endpoint(self, code: str) -> str:
        """Add /health endpoint if missing."""
        if "/health" in code:
            return code

        if "from fastapi import" in code:
            patch = """
@app.get("/health")
def health_check():
    return {"status": "healthy"}
"""
            return code + patch

        return code

    def fix_port_binding(self, code: str, new_port: int) -> str:
        """Change hardcoded port in code."""
        return re.sub(r"port\s*=\s*\d+", f"port = {new_port}", code)


class AutoHealer:
    """
    Self-healing system for subprocess deployments.

    Detects failures and automatically fixes them by:
    1. Restarting the process
    2. Changing port if conflict
    3. Adding missing health endpoints
    """

    def __init__(
        self,
        deployer: ApplicationDeployer,
        monitor: ServiceMonitor,
        enable_auto_fix: bool = True,
    ):
        self.deployer = deployer
        self.monitor = monitor
        self.enable_auto_fix = enable_auto_fix
        self.log_analyzer = LogAnalyzer()
        self.patch_generator = PatchGenerator()
        self._healing_history: List[HealingResult] = []

        self.monitor.on_alert(self._handle_alert)

        self.logger = logging.getLogger(__name__)

    def _handle_alert(self, alert: Alert) -> None:
        """Handle monitoring alerts."""
        if alert.severity != "critical":
            return

        self.logger.warning(f"Alert: {alert.message}")

        if self.enable_auto_fix:
            result = self.heal(alert.service_name)
            self._healing_history.append(result)

            if result.success:
                self.logger.info(f"Healed: {result.message}")
            else:
                self.logger.error(f"Healing failed: {result.message}")

    def heal(self, service_name: str) -> HealingResult:
        """Attempt to heal a failing service."""
        self.logger.info(f"Healing {service_name}")

        health = self.monitor.get_health(service_name)
        if health == HealthStatus.HEALTHY:
            return HealingResult(
                success=True,
                action=HealingAction.INVESTIGATE,
                message="Already healthy",
            )

        # Try restart first
        result = self._try_restart(service_name)
        if result.success:
            return result

        # If restart fails, check for port conflict
        work_dir = self.deployer._work_dirs.get(service_name)
        if work_dir and (work_dir / "main.py").exists():
            code = (work_dir / "main.py").read_text(encoding="utf-8")

            # Check if health endpoint missing
            if "/health" not in code:
                return self._try_hotfix(service_name, code)

            # Try port change
            return self._try_port_change(service_name, code)

        return result

    def _try_restart(self, service_name: str) -> HealingResult:
        """Restart the process."""
        self.logger.info(f"Restarting {service_name}")

        result = self.deployer.redeploy(service_name)

        if result.status == DeploymentStatus.RUNNING:
            # Wait and verify
            import time

            time.sleep(3)

            if self.deployer.is_running(service_name):
                return HealingResult(
                    success=True,
                    action=HealingAction.RESTART,
                    message="Process restarted successfully",
                )

        return HealingResult(
            success=False,
            action=HealingAction.RESTART,
            message=f"Restart failed: {result.error}",
        )

    def _try_hotfix(self, service_name: str, code: str) -> HealingResult:
        """Apply hotfix for missing health endpoint."""
        self.logger.info(f"Hotfixing {service_name}")

        patched = self.patch_generator.add_health_endpoint(code)

        if patched != code:
            result = self.deployer.redeploy(service_name, new_code=patched)

            if result.status == DeploymentStatus.RUNNING:
                return HealingResult(
                    success=True,
                    action=HealingAction.HOTFIX,
                    message="Added health endpoint",
                )

        return HealingResult(
            success=False,
            action=HealingAction.HOTFIX,
            message="Hotfix not applicable",
        )

    def _try_port_change(self, service_name: str, code: str) -> HealingResult:
        """Change port to avoid conflict."""
        self.logger.info(f"Changing port for {service_name}")

        new_port = self._find_available_port()
        patched = self.patch_generator.fix_port_binding(code, new_port)

        # Also update env var
        result = self.deployer.redeploy(service_name, new_code=patched)

        if result.status == DeploymentStatus.RUNNING:
            # Update monitor URL
            self.monitor.unregister(service_name)
            self.monitor.register(
                service_name,
                f"http://localhost:{new_port}",
                lambda: self.deployer.is_running(service_name),
            )

            return HealingResult(
                success=True,
                action=HealingAction.PORT_CHANGE,
                message=f"Changed to port {new_port}",
            )

        return HealingResult(
            success=False,
            action=HealingAction.PORT_CHANGE,
            message="Port change failed",
        )

    def _find_available_port(self, start: int = 9000) -> int:
        """Find available port."""
        import socket

        port = start
        while port < 65535:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("localhost", port)) != 0:
                    return port
            port += 1

        raise RuntimeError("No ports available")

    def get_healing_history(
        self, service_name: Optional[str] = None
    ) -> List[HealingResult]:
        """Get healing history."""
        if service_name:
            return [h for h in self._healing_history if service_name in h.message]
        return self._healing_history.copy()
