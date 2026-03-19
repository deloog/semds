"""Runtime monitoring for subprocess-based deployments."""

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional

import requests


class HealthStatus(Enum):
    """Service health states."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceMetrics:
    """Collected metrics for a service."""

    service_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    request_count: int = 0
    error_count: int = 0
    avg_response_time_ms: float = 0.0
    process_alive: bool = True


@dataclass
class Alert:
    """Alert triggered by monitoring."""

    service_name: str
    alert_type: str
    message: str
    severity: str  # 'info', 'warning', 'critical'
    timestamp: datetime = field(default_factory=datetime.now)
    metric_value: Optional[float] = None


class ServiceMonitor:
    """
    Monitor deployed services via HTTP health checks.

    Works with subprocess-based deployments - checks both
    process status and HTTP endpoints.
    """

    def __init__(self, check_interval: int = 10):
        self.check_interval = check_interval
        self._monitored_services: Dict[str, dict] = {}
        self._health_status: Dict[str, HealthStatus] = {}
        self._metrics_history: Dict[str, List[ServiceMetrics]] = {}
        self._alerts: List[Alert] = []
        self._callbacks: List[Callable[[Alert], None]] = []
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._process_checkers: Dict[str, Callable[[], bool]] = {}

    def start(self) -> None:
        """Start the monitoring loop."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop(self) -> None:
        """Stop the monitoring loop."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def register(
        self,
        service_name: str,
        service_url: str,
        process_checker: Optional[Callable[[], bool]] = None,
        health_path: str = "/health",
    ) -> None:
        """
        Register a service for monitoring.

        Args:
            service_name: Unique identifier
            service_url: Base URL
            process_checker: Function to check if process is alive
            health_path: Health check endpoint
        """
        with self._lock:
            self._monitored_services[service_name] = {
                "url": service_url,
                "health_path": health_path,
                "last_check": None,
                "consecutive_failures": 0,
            }
            self._health_status[service_name] = HealthStatus.UNKNOWN
            self._metrics_history[service_name] = []
            if process_checker:
                self._process_checkers[service_name] = process_checker

    def unregister(self, service_name: str) -> None:
        """Remove a service from monitoring."""
        with self._lock:
            self._monitored_services.pop(service_name, None)
            self._health_status.pop(service_name, None)
            self._metrics_history.pop(service_name, None)
            self._process_checkers.pop(service_name, None)

    def get_health(self, service_name: str) -> HealthStatus:
        """Get current health status."""
        with self._lock:
            return self._health_status.get(service_name, HealthStatus.UNKNOWN)

    def get_all_health(self) -> Dict[str, HealthStatus]:
        """Get all services health."""
        with self._lock:
            return self._health_status.copy()

    def get_alerts(
        self, service_name: Optional[str] = None, limit: int = 50
    ) -> List[Alert]:
        """Get recent alerts."""
        with self._lock:
            alerts = self._alerts
            if service_name:
                alerts = [a for a in alerts if a.service_name == service_name]
            return alerts[-limit:]

    def on_alert(self, callback: Callable[[Alert], None]) -> None:
        """Register alert callback."""
        self._callbacks.append(callback)

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            with self._lock:
                services = list(self._monitored_services.items())

            for service_name, config in services:
                try:
                    self._check_service(service_name, config)
                except Exception as e:
                    self._trigger_alert(
                        service_name,
                        "check_error",
                        f"Health check failed: {e}",
                        "warning",
                    )

            self._stop_event.wait(self.check_interval)

    def _check_service(self, service_name: str, config: dict) -> None:
        """Check service health."""
        # Check process is alive
        process_alive = True
        if service_name in self._process_checkers:
            process_alive = self._process_checkers[service_name]()

        if not process_alive:
            with self._lock:
                old_status = self._health_status[service_name]
                self._health_status[service_name] = HealthStatus.UNHEALTHY
                self._monitored_services[service_name]["consecutive_failures"] += 1

                if old_status != HealthStatus.UNHEALTHY:
                    self._trigger_alert(
                        service_name,
                        "process_dead",
                        "Process is not running",
                        "critical",
                    )
            return

        # Check HTTP health endpoint
        health_url = f"{config['url']}{config['health_path']}"
        start_time = time.time()

        try:
            response = requests.get(health_url, timeout=5)
            response_time = (time.time() - start_time) * 1000

            is_healthy = response.status_code == 200

            with self._lock:
                self._monitored_services[service_name]["last_check"] = datetime.now()

                if is_healthy:
                    self._monitored_services[service_name]["consecutive_failures"] = 0
                    new_status = HealthStatus.HEALTHY
                else:
                    failures = (
                        self._monitored_services[service_name]["consecutive_failures"]
                        + 1
                    )
                    self._monitored_services[service_name][
                        "consecutive_failures"
                    ] = failures
                    new_status = (
                        HealthStatus.UNHEALTHY
                        if failures >= 2
                        else HealthStatus.DEGRADED
                    )

                old_status = self._health_status[service_name]
                self._health_status[service_name] = new_status

                # Record metrics
                metrics = ServiceMetrics(
                    service_name=service_name,
                    request_count=1,
                    error_count=0 if is_healthy else 1,
                    avg_response_time_ms=response_time,
                    process_alive=True,
                )
                self._metrics_history[service_name].append(metrics)

                # Alert on status change to unhealthy
                if (
                    new_status == HealthStatus.UNHEALTHY
                    and old_status != HealthStatus.UNHEALTHY
                ):
                    self._trigger_alert(
                        service_name,
                        "health_check_failed",
                        f"HTTP {response.status_code}",
                        "critical",
                    )

        except requests.RequestException as e:
            with self._lock:
                failures = (
                    self._monitored_services[service_name].get(
                        "consecutive_failures", 0
                    )
                    + 1
                )
                self._monitored_services[service_name][
                    "consecutive_failures"
                ] = failures

                new_status = (
                    HealthStatus.UNHEALTHY if failures >= 2 else HealthStatus.DEGRADED
                )
                old_status = self._health_status[service_name]
                self._health_status[service_name] = new_status

                if (
                    new_status == HealthStatus.UNHEALTHY
                    and old_status != HealthStatus.UNHEALTHY
                ):
                    self._trigger_alert(
                        service_name,
                        "service_unreachable",
                        f"Cannot connect: {e}",
                        "critical",
                    )

    def _trigger_alert(
        self,
        service_name: str,
        alert_type: str,
        message: str,
        severity: str,
        metric_value: Optional[float] = None,
    ) -> None:
        """Create and dispatch alert."""
        alert = Alert(
            service_name=service_name,
            alert_type=alert_type,
            message=message,
            severity=severity,
            metric_value=metric_value,
        )

        with self._lock:
            self._alerts.append(alert)

        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception:
                pass

    def check_now(self, service_name: str) -> HealthStatus:
        """Force immediate health check."""
        with self._lock:
            config = self._monitored_services.get(service_name)

        if config:
            self._check_service(service_name, config)

        return self.get_health(service_name)
