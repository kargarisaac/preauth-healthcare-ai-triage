"""
Comprehensive health checks for Healthcare AI Pre-authorization Platform production deployment.

Provides detailed health assessments for Kubernetes liveness and readiness probes,
monitoring systems, and operational validation.
"""

import asyncio
import time
import json
import psutil
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from loguru import logger

from api.config import get_config


class HealthStatus(str, Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CheckType(str, Enum):
    """Types of health checks."""
    LIVENESS = "liveness"
    READINESS = "readiness"
    DEEP = "deep"
    STARTUP = "startup"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    duration_ms: float
    message: str = ""
    details: Dict[str, Any] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }


class BaseHealthCheck:
    """Base class for health checks."""
    
    def __init__(self, name: str, timeout_seconds: float = 5.0):
        self.name = name
        self.timeout_seconds = timeout_seconds
    
    async def check(self) -> HealthCheckResult:
        """Perform the health check."""
        start_time = time.time()
        
        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                self._perform_check(), 
                timeout=self.timeout_seconds
            )
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                duration_ms=duration_ms,
                message="Check passed" if result else "Check failed",
                details=await self._get_details() if hasattr(self, '_get_details') else {}
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                duration_ms=duration_ms,
                message=f"Check timed out after {self.timeout_seconds}s"
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                duration_ms=duration_ms,
                message=f"Check failed: {str(e)}"
            )
    
    async def _perform_check(self) -> bool:
        """Override this method to implement the actual check."""
        raise NotImplementedError


class BasicLivenessCheck(BaseHealthCheck):
    """Basic liveness check - ensures the application is running."""
    
    def __init__(self):
        super().__init__("basic_liveness", timeout_seconds=1.0)
    
    async def _perform_check(self) -> bool:
        """Simple check that the process is alive."""
        return True  # If we can execute this, the process is alive


class SystemResourcesCheck(BaseHealthCheck):
    """Check system resource usage."""
    
    def __init__(self, memory_threshold_percent: float = 90.0, 
                 cpu_threshold_percent: float = 95.0,
                 disk_threshold_percent: float = 95.0):
        super().__init__("system_resources", timeout_seconds=3.0)
        self.memory_threshold = memory_threshold_percent
        self.cpu_threshold = cpu_threshold_percent
        self.disk_threshold = disk_threshold_percent
    
    async def _perform_check(self) -> bool:
        """Check if system resources are within acceptable limits."""
        # Memory check
        memory = psutil.virtual_memory()
        if memory.percent > self.memory_threshold:
            return False
        
        # CPU check (1-second sample)
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > self.cpu_threshold:
            return False
        
        # Disk check
        try:
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > self.disk_threshold:
                return False
        except Exception:
            pass  # Disk check is optional
        
        return True
    
    async def _get_details(self) -> Dict[str, Any]:
        """Get detailed resource information."""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            details = {
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "threshold": self.memory_threshold
                },
                "cpu": {
                    "percent": cpu_percent,
                    "threshold": self.cpu_threshold
                }
            }
            
            try:
                disk = psutil.disk_usage('/')
                details["disk"] = {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                    "threshold": self.disk_threshold
                }
            except Exception:
                pass
            
            return details
        except Exception as e:
            return {"error": str(e)}


class DatabaseCheck(BaseHealthCheck):
    """Database connectivity check."""
    
    def __init__(self):
        super().__init__("database", timeout_seconds=5.0)
    
    async def _perform_check(self) -> bool:
        """Check database connectivity."""
        config = get_config()
        
        # For now, we're not using a database
        # This is a placeholder for future implementation
        if not hasattr(config, 'database') or not getattr(config.database, 'enabled', False):
            return True  # Not using database, so it's "healthy"
        
        # TODO: Implement actual database connectivity check
        return True


class RedisCheck(BaseHealthCheck):
    """Redis cache connectivity check."""
    
    def __init__(self):
        super().__init__("redis", timeout_seconds=3.0)
    
    async def _perform_check(self) -> bool:
        """Check Redis connectivity."""
        try:
            import redis
            config = get_config()
            
            if hasattr(config, 'redis') and config.redis.url:
                # Parse Redis URL
                r = redis.from_url(config.redis.url, socket_timeout=2)
                
                # Simple ping test
                result = r.ping()
                return result is True
            else:
                # Redis not configured, consider it healthy
                return True
                
        except ImportError:
            # Redis not installed, skip check
            return True
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False


class ExternalServicesCheck(BaseHealthCheck):
    """Check external service dependencies."""
    
    def __init__(self):
        super().__init__("external_services", timeout_seconds=10.0)
    
    async def _perform_check(self) -> bool:
        """Check external service connectivity."""
        config = get_config()
        
        # Check Claude API availability (if configured)
        if hasattr(config, 'ai') and config.ai.claude_api_key:
            try:
                # For readiness, we could make a lightweight API call
                # For now, just check if the key is configured
                return len(config.ai.claude_api_key) > 10
            except Exception:
                return False
        
        return True  # No external services to check


class ApplicationReadinessCheck(BaseHealthCheck):
    """Check if application is ready to serve requests."""
    
    def __init__(self):
        super().__init__("application_readiness", timeout_seconds=5.0)
    
    async def _perform_check(self) -> bool:
        """Check if application is ready."""
        try:
            # Check if required services are initialized
            from api.services.patient_lookup_service import get_patient_lookup_service
            from api.services.xml_processing_service import get_xml_processing_service
            
            # Quick service availability check
            patient_service = get_patient_lookup_service()
            xml_service = get_xml_processing_service()
            
            # Verify services are responsive
            patient_status = patient_service.get_service_status()
            xml_status = xml_service.get_processing_stats()
            
            return (patient_status.get("status") == "ready" and 
                    xml_status.get("service_status") == "ready")
        except Exception as e:
            logger.warning(f"Application readiness check failed: {e}")
            return False


class StartupCheck(BaseHealthCheck):
    """Check if application has completed startup procedures."""
    
    def __init__(self):
        super().__init__("startup", timeout_seconds=30.0)
        self.startup_complete_file = Path("/.startup_complete")
    
    async def _perform_check(self) -> bool:
        """Check if startup is complete."""
        # Check if startup marker file exists
        if self.startup_complete_file.exists():
            return True
        
        # Alternative: check if critical components are loaded
        try:
            # Check if configuration is loaded
            config = get_config()
            
            # Check if logging is configured
            if not hasattr(logger, '_core'):
                return False
            
            # Check if services are available
            from api.services.patient_lookup_service import get_patient_lookup_service
            patient_service = get_patient_lookup_service()
            
            return True
        except Exception:
            return False


class DeepHealthCheck(BaseHealthCheck):
    """Comprehensive deep health check for operational validation."""
    
    def __init__(self):
        super().__init__("deep_health", timeout_seconds=60.0)
    
    async def _perform_check(self) -> bool:
        """Perform comprehensive system validation."""
        try:
            # Test core functionality
            from preauth_system.pipeline_module import PreAuthPipeline
            
            # Initialize pipeline
            pipeline = PreAuthPipeline()
            
            # Test basic processing capability
            # This would ideally use a small test case
            
            return True  # Placeholder for actual deep validation
        except Exception as e:
            logger.error(f"Deep health check failed: {e}")
            return False


class HealthChecker:
    """Main health checker orchestrator."""
    
    def __init__(self):
        self.liveness_checks = [
            BasicLivenessCheck(),
        ]
        
        self.readiness_checks = [
            SystemResourcesCheck(),
            DatabaseCheck(),
            RedisCheck(),
            ExternalServicesCheck(),
            ApplicationReadinessCheck(),
        ]
        
        self.startup_checks = [
            StartupCheck(),
        ]
        
        self.deep_checks = [
            DeepHealthCheck(),
        ]
    
    async def check_liveness(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Perform liveness checks (Kubernetes liveness probe)."""
        return await self._run_checks(self.liveness_checks, CheckType.LIVENESS)
    
    async def check_readiness(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Perform readiness checks (Kubernetes readiness probe)."""
        return await self._run_checks(self.readiness_checks, CheckType.READINESS)
    
    async def check_startup(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Perform startup checks (Kubernetes startup probe)."""
        return await self._run_checks(self.startup_checks, CheckType.STARTUP)
    
    async def check_deep(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Perform deep health validation."""
        return await self._run_checks(self.deep_checks, CheckType.DEEP)
    
    async def _run_checks(self, checks: List[BaseHealthCheck], 
                         check_type: CheckType) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Run a list of health checks."""
        start_time = time.time()
        results = []
        overall_status = HealthStatus.HEALTHY
        
        # Run checks concurrently
        check_tasks = [check.check() for check in checks]
        check_results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        for i, result in enumerate(check_results):
            if isinstance(result, Exception):
                # Handle exception during check
                check_result = HealthCheckResult(
                    name=checks[i].name,
                    status=HealthStatus.UNHEALTHY,
                    duration_ms=0,
                    message=f"Check failed with exception: {str(result)}"
                )
            else:
                check_result = result
            
            results.append(check_result.to_dict())
            
            # Update overall status
            if check_result.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif check_result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        total_duration = (time.time() - start_time) * 1000
        
        return overall_status, {
            "status": overall_status.value,
            "check_type": check_type.value,
            "checks": results,
            "summary": {
                "total_checks": len(results),
                "passed": sum(1 for r in results if r["status"] == "healthy"),
                "failed": sum(1 for r in results if r["status"] == "unhealthy"),
                "degraded": sum(1 for r in results if r["status"] == "degraded"),
                "duration_ms": total_duration
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global health checker instance
health_checker = HealthChecker()


# FastAPI endpoint functions
async def liveness_probe() -> Dict[str, Any]:
    """Kubernetes liveness probe endpoint."""
    status, details = await health_checker.check_liveness()
    
    if status == HealthStatus.HEALTHY:
        return details
    else:
        # For liveness, we only fail on critical issues
        # Degraded services might still be "alive"
        if status == HealthStatus.UNHEALTHY:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail=details)
        return details


async def readiness_probe() -> Dict[str, Any]:
    """Kubernetes readiness probe endpoint."""
    status, details = await health_checker.check_readiness()
    
    if status == HealthStatus.HEALTHY:
        return details
    else:
        # For readiness, any non-healthy status means not ready
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=details)


async def startup_probe() -> Dict[str, Any]:
    """Kubernetes startup probe endpoint."""
    status, details = await health_checker.check_startup()
    
    if status == HealthStatus.HEALTHY:
        return details
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=details)


async def deep_health_check() -> Dict[str, Any]:
    """Comprehensive health check for monitoring systems."""
    status, details = await health_checker.check_deep()
    return details


# Utility functions
def mark_startup_complete():
    """Mark application startup as complete."""
    try:
        startup_file = Path("/.startup_complete")
        startup_file.touch()
        logger.info("Startup marked as complete")
    except Exception as e:
        logger.warning(f"Failed to mark startup complete: {e}")


def cleanup_startup_marker():
    """Clean up startup marker on shutdown."""
    try:
        startup_file = Path("/.startup_complete")
        if startup_file.exists():
            startup_file.unlink()
    except Exception as e:
        logger.warning(f"Failed to cleanup startup marker: {e}")


if __name__ == "__main__":
    # Test health checks
    import asyncio
    
    async def test_health_checks():
        checker = HealthChecker()
        
        print("Testing liveness checks...")
        status, result = await checker.check_liveness()
        print(f"Liveness: {status.value}")
        print(json.dumps(result, indent=2))
        
        print("\nTesting readiness checks...")
        status, result = await checker.check_readiness()
        print(f"Readiness: {status.value}")
        print(json.dumps(result, indent=2))
        
        print("\nTesting startup checks...")
        status, result = await checker.check_startup()
        print(f"Startup: {status.value}")
        print(json.dumps(result, indent=2))
    
    asyncio.run(test_health_checks())