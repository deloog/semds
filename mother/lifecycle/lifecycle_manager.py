"""
SEMDS Lifecycle Manager - Subprocess-based (No Docker).

Full lifecycle闭环 using subprocess + tempfile:
- No Docker required
- Runs Python processes directly
- Process-level monitoring
- Auto-restart on failure
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from .deployer import (
    ApplicationDeployer,
    DeploymentConfig,
    DeploymentResult,
    DeploymentStatus,
)
from .healer import AutoHealer, HealingResult
from .monitor import Alert, HealthStatus, ServiceMonitor


@dataclass
class ServiceStatus:
    """Complete status of a deployed service."""
    name: str
    deployment_status: DeploymentStatus
    health: HealthStatus
    url: Optional[str]
    process_id: Optional[int] = None
    uptime_seconds: Optional[int] = None
    last_error: Optional[str] = None


class LifecycleManager:
    """
    High-level lifecycle management for SEMDS applications.
    
    Uses subprocess + tempfile - no Docker required.
    Suitable for Windows development environment.
    """
    
    def __init__(
        self,
        deployment_dir: str = "storage/deployments",
        enable_monitoring: bool = True,
        enable_auto_healing: bool = True,
    ):
        self.deployer = ApplicationDeployer(deployment_dir)
        self.monitor = ServiceMonitor()
        self.healer = AutoHealer(
            self.deployer,
            self.monitor,
            enable_auto_fix=enable_auto_healing,
        )
        
        if enable_monitoring:
            self.monitor.start()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("LifecycleManager initialized (subprocess mode)")
    
    def deploy_service(
        self,
        name: str,
        app_code: str,
        config: Optional[DeploymentConfig] = None,
        test_code: Optional[str] = None,
        wait_for_healthy: bool = True,
        timeout_seconds: int = 30,
    ) -> DeploymentResult:
        """
        Deploy a service with full lifecycle management.
        
        Args:
            name: Unique service name
            app_code: Application source code
            config: Deployment config (uses defaults if None)
            test_code: Optional test code
            wait_for_healthy: Whether to wait for health check
            timeout_seconds: Max wait time
            
        Returns:
            DeploymentResult with service URL
        """
        if config is None:
            config = DeploymentConfig(name=name)
        
        self.logger.info(f"Deploying {name}")
        
        # Deploy
        result = self.deployer.deploy(app_code, config, test_code)
        
        if result.status != DeploymentStatus.RUNNING:
            self.logger.error(f"Deployment failed: {result.error}")
            return result
        
        # Register for monitoring with process checker
        self.monitor.register(
            name,
            result.service_url,
            process_checker=lambda: self.deployer.is_running(name),
        )
        
        # Wait for healthy if requested
        if wait_for_healthy:
            import time
            start = time.time()
            while time.time() - start < timeout_seconds:
                health = self.monitor.get_health(name)
                if health == HealthStatus.HEALTHY:
                    self.logger.info(f"{name} is healthy")
                    break
                elif health == HealthStatus.UNHEALTHY:
                    self.logger.warning(f"{name} unhealthy, healing...")
                    self.healer.heal(name)
                    break
                time.sleep(1)
        
        return result
    
    def get_service_status(self, name: str) -> ServiceStatus:
        """Get complete status of a service."""
        active = self.deployer.list_active()
        deployment_info = active.get(name, {})
        
        health = self.monitor.get_health(name)
        
        # Check if actually running
        is_running = self.deployer.is_running(name)
        if not is_running and health == HealthStatus.HEALTHY:
            health = HealthStatus.UNHEALTHY
        
        return ServiceStatus(
            name=name,
            deployment_status=DeploymentStatus.RUNNING if is_running else DeploymentStatus.STOPPED,
            health=health,
            url=f"http://localhost:8000",  # Default, should be tracked per service
            process_id=deployment_info.get("pid"),
        )
    
    def list_services(self) -> Dict[str, ServiceStatus]:
        """List all services and their status."""
        result = {}
        active = self.deployer.list_active()
        
        for name in active:
            result[name] = self.get_service_status(name)
        
        return result
    
    def stop_service(self, name: str) -> bool:
        """Stop a running service."""
        self.logger.info(f"Stopping {name}")
        self.monitor.unregister(name)
        return self.deployer.stop(name)
    
    def restart_service(self, name: str) -> DeploymentResult:
        """Restart a service."""
        self.logger.info(f"Restarting {name}")
        
        result = self.deployer.redeploy(name)
        
        if result.status == DeploymentStatus.RUNNING:
            self.monitor.register(
                name,
                result.service_url,
                process_checker=lambda: self.deployer.is_running(name),
            )
        
        return result
    
    def get_service_alerts(self, name: str, limit: int = 50) -> List[Alert]:
        """Get alerts for a service."""
        return self.monitor.get_alerts(name, limit)
    
    def get_healing_history(self, name: Optional[str] = None) -> List[HealingResult]:
        """Get healing history."""
        return self.healer.get_healing_history(name)
    
    def force_heal(self, name: str) -> HealingResult:
        """Manually trigger healing."""
        self.logger.info(f"Manual healing: {name}")
        return self.healer.heal(name)
    
    def shutdown(self) -> None:
        """Shutdown lifecycle manager."""
        self.logger.info("Shutting down")
        self.monitor.stop()
        
        # Stop all services
        for name in list(self.deployer.list_active().keys()):
            self.stop_service(name)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
        return False
