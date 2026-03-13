"""
Health Check and Monitoring Endpoint
Provides system health status and detects silent failures
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime, timezone
import logging
import sys

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from routes.auth_routes import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "email-assistant-api"
    }

@router.get("/detailed")
async def detailed_health_check(db = Depends(get_db)):
    """
    Detailed health check with all system components
    Returns errors if any component is failing
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {},
        "errors": []
    }
    
    try:
        # Check Database
        try:
            await db.command("ping")
            health_status["components"]["database"] = {
                "status": "healthy",
                "message": "MongoDB connected"
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["errors"].append(f"Database: {str(e)}")
            health_status["status"] = "unhealthy"
        
        # Check System Resources
        if HAS_PSUTIL:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                health_status["components"]["system"] = {
                    "status": "healthy",
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "warnings": []
                }
                
                # Add warnings for high resource usage
                if cpu_percent > 90:
                    health_status["components"]["system"]["warnings"].append("High CPU usage")
                if memory.percent > 90:
                    health_status["components"]["system"]["warnings"].append("High memory usage")
                if disk.percent > 90:
                    health_status["components"]["system"]["warnings"].append("High disk usage")
                    
            except Exception as e:
                health_status["components"]["system"] = {
                    "status": "unknown",
                    "error": str(e)
                }
        else:
            health_status["components"]["system"] = {
                "status": "unavailable",
                "message": "psutil not installed"
            }
        
        # Check Python Environment
        try:
            health_status["components"]["python"] = {
                "status": "healthy",
                "version": sys.version,
                "executable": sys.executable
            }
        except Exception as e:
            health_status["components"]["python"] = {
                "status": "unknown",
                "error": str(e)
            }
        
        # Check Collections
        try:
            collections = await db.list_collection_names()
            health_status["components"]["collections"] = {
                "status": "healthy",
                "count": len(collections),
                "collections": collections[:10]  # First 10 collections
            }
        except Exception as e:
            health_status["components"]["collections"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["errors"].append(f"Collections: {str(e)}")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }

@router.get("/workers")
async def worker_health_check(db = Depends(get_db)):
    """
    Check the health of background workers with orchestrator and AI concurrency stats
    """
    try:
        from services.orchestrator_service import orchestrator
        from utils.ai_concurrency import ai_concurrency
        from utils.redis_rate_limiter import redis_rate_limiter
        
        orch_metrics = orchestrator.get_metrics()
        ai_stats = ai_concurrency.get_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "orchestrator": {
                "running": orch_metrics["running"],
                "active_tasks": orch_metrics["active_tasks"],
                "tasks_dispatched": orch_metrics["tasks_dispatched"],
                "tasks_completed": orch_metrics["tasks_completed"],
                "tasks_failed": orch_metrics["tasks_failed"],
                "max_concurrent_users": orch_metrics["max_concurrent_users"],
                "max_tasks_per_user": orch_metrics["max_tasks_per_user"],
            },
            "ai_concurrency": {
                "active_calls": ai_stats["active_calls"],
                "total_calls": ai_stats["total_calls"],
                "total_errors": ai_stats["total_errors"],
                "total_retries": ai_stats["total_retries"],
                "max_concurrent": ai_stats["max_concurrent"],
                "per_user_limit": ai_stats["per_user_limit"],
            },
            "redis": {
                "available": redis_rate_limiter._redis is not None,
            },
        }
    except Exception as e:
        logger.error(f"Worker health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
