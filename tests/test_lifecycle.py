"""Tests for SEMDS lifecycle management (subprocess-based)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from mother.lifecycle import (
    ApplicationDeployer,
    DeploymentConfig,
    DeploymentStatus,
    HealthStatus,
    LifecycleManager,
    ServiceMonitor,
)
from mother.lifecycle.healer import LogAnalyzer, PatchGenerator, HealingAction


class TestLogAnalyzer:
    """Test log analysis for error detection."""
    
    def test_syntax_error_detection(self):
        """Test detection of syntax errors."""
        analyzer = LogAnalyzer()
        logs = [
            "INFO: Starting server",
            "SyntaxError: invalid syntax at line 10",
            "ERROR: Cannot start",
        ]
        
        findings = analyzer.analyze(logs)
        
        assert "syntax_error" in findings
        assert len(findings["syntax_error"]) == 1
    
    def test_import_error_detection(self):
        """Test detection of import errors."""
        analyzer = LogAnalyzer()
        logs = [
            "INFO: Loading module",
            "ImportError: No module named 'requests'",
        ]
        
        findings = analyzer.analyze(logs)
        
        assert "import_error" in findings
    
    def test_port_in_use_detection(self):
        """Test detection of port conflicts."""
        analyzer = LogAnalyzer()
        logs = [
            "OSError: [Errno 48] Address already in use",
        ]
        
        findings = analyzer.analyze(logs)
        
        assert "port_in_use" in findings
    
    def test_no_errors(self):
        """Test clean logs."""
        analyzer = LogAnalyzer()
        logs = ["INFO: All good", "DEBUG: Running normally"]
        
        findings = analyzer.analyze(logs)
        
        assert len(findings) == 0


class TestPatchGenerator:
    """Test code patch generation."""
    
    def test_add_health_endpoint_fastapi(self):
        """Test adding health endpoint to FastAPI app."""
        gen = PatchGenerator()
        code = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"msg": "hello"}
'''
        patched = gen.add_health_endpoint(code)
        
        assert "/health" in patched
        assert "health_check" in patched
    
    def test_no_duplicate_health_endpoint(self):
        """Test not adding duplicate health endpoint."""
        gen = PatchGenerator()
        code = '''
@app.get("/health")
def health():
    return {"status": "ok"}
'''
        patched = gen.add_health_endpoint(code)
        
        # Should not change
        assert patched == code
    
    def test_fix_port_binding(self):
        """Test changing port in code."""
        gen = PatchGenerator()
        code = 'port = 8000'
        
        patched = gen.fix_port_binding(code, 9000)
        
        assert 'port = 9000' in patched


class TestDeploymentConfig:
    """Test deployment configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = DeploymentConfig(name="test")
        
        assert config.port == 8000
        assert config.app_type == "fastapi"
        assert config.python_version == "3.11"
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = DeploymentConfig(
            name="test",
            app_type="flask",
            port=5000,
            dependencies=["requests", "redis"],
        )
        
        assert config.port == 5000
        assert config.app_type == "flask"
        assert "requests" in config.dependencies


class TestHealthStatus:
    """Test health status enum."""
    
    def test_status_values(self):
        """Test health status values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.DEGRADED.value == "degraded"


class TestApplicationDeployer:
    """Test ApplicationDeployer (unit tests)."""
    
    def test_init(self, tmp_path):
        """Test deployer initialization."""
        deployer = ApplicationDeployer(deployment_dir=str(tmp_path / "deployments"))
        assert deployer.deployment_dir.exists()
    
    def test_write_app_files(self, tmp_path):
        """Test writing application files."""
        deployer = ApplicationDeployer(deployment_dir=str(tmp_path))
        deployer._work_dirs["test"] = tmp_path
        
        config = DeploymentConfig(name="test", app_type="fastapi")
        app_code = "from fastapi import FastAPI\napp = FastAPI()"
        
        deployer._write_app_files(tmp_path, app_code, config, None)
        
        assert (tmp_path / "main.py").exists()
        assert (tmp_path / "requirements.txt").exists()
        assert "fastapi" in (tmp_path / "requirements.txt").read_text()
    
    def test_is_running_not_deployed(self, tmp_path):
        """Test is_running for non-existent service."""
        deployer = ApplicationDeployer(deployment_dir=str(tmp_path))
        
        assert deployer.is_running("nonexistent") is False
    
    def test_stop_not_deployed(self, tmp_path):
        """Test stop for non-existent service."""
        deployer = ApplicationDeployer(deployment_dir=str(tmp_path))
        
        assert deployer.stop("nonexistent") is False


class TestServiceMonitor:
    """Test ServiceMonitor."""
    
    def test_register_service(self):
        """Test service registration."""
        monitor = ServiceMonitor()
        
        monitor.register("test-service", "http://localhost:8000")
        
        assert "test-service" in monitor._monitored_services
        assert monitor.get_health("test-service") == HealthStatus.UNKNOWN
    
    def test_unregister_service(self):
        """Test service unregistration."""
        monitor = ServiceMonitor()
        monitor.register("test", "http://localhost:8000")
        
        monitor.unregister("test")
        
        assert "test" not in monitor._monitored_services
        assert monitor.get_health("test") == HealthStatus.UNKNOWN
    
    def test_alert_callback(self):
        """Test alert callback registration."""
        monitor = ServiceMonitor()
        callback = Mock()
        
        monitor.on_alert(callback)
        
        assert callback in monitor._callbacks


class TestLifecycleManager:
    """Test LifecycleManager (unit tests)."""
    
    def test_init(self, tmp_path):
        """Test manager initialization."""
        manager = LifecycleManager(
            deployment_dir=str(tmp_path / "deployments"),
            enable_monitoring=False,
        )
        
        assert manager.deployer is not None
        assert manager.monitor is not None
        assert manager.healer is not None
    
    def test_get_service_status_not_deployed(self, tmp_path):
        """Test get status for non-existent service."""
        manager = LifecycleManager(
            deployment_dir=str(tmp_path),
            enable_monitoring=False,
        )
        
        status = manager.get_service_status("nonexistent")
        
        assert status.name == "nonexistent"
        assert status.health == HealthStatus.UNKNOWN


@pytest.mark.skip(reason="Requires subprocess")
class TestIntegration:
    """Integration tests (skipped by default)."""
    
    def test_full_lifecycle(self, tmp_path):
        """Test complete deployment lifecycle."""
        app_code = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}
'''
        with LifecycleManager(
            deployment_dir=str(tmp_path / "deployments"),
            enable_monitoring=True,
        ) as manager:
            
            result = manager.deploy_service(
                name="test-service",
                app_code=app_code,
                config=DeploymentConfig(name="test-service", port=9999),
                wait_for_healthy=False,
            )
            
            assert result.status == DeploymentStatus.RUNNING
            
            # Clean up
            manager.stop_service("test-service")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
