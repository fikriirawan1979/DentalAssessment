from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import psutil
import time
import asyncio

from ..core.database import get_db, engine
from ..core.config import settings
from ..api.schemas.schemas import HealthCheck

router = APIRouter(tags=["health"])

# Store application start time
start_time = time.time()


@router.get("/health", response_model=HealthCheck)
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check for all system components"""
    
    try:
        # Check database connection
        db_status = "healthy"
        try:
            db.execute("SELECT 1")
        except Exception:
            db_status = "unhealthy"
        
        # Check Redis connection
        redis_status = await check_redis_health()
        
        # Check MinIO connection
        minio_status = await check_minio_health()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Determine overall status
        overall_status = "healthy"
        if db_status != "healthy" or redis_status != "healthy" or minio_status != "healthy":
            overall_status = "degraded"
        
        if cpu_percent > 90 or memory.percent > 90:
            overall_status = "stressed"
        
        return HealthCheck(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            services={
                "database": db_status,
                "redis": redis_status,
                "minio": minio_status,
                "cpu_usage": f"{cpu_percent}%",
                "memory_usage": f"{memory.percent}%",
                "disk_usage": f"{disk.percent}%"
            },
            uptime_seconds=time.time() - start_time
        )
        
    except Exception as e:
        return HealthCheck(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            services={"error": str(e)},
            uptime_seconds=time.time() - start_time
        )


async def check_redis_health():
    """Check Redis connection health"""
    try:
        import redis
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        return "healthy"
    except Exception:
        return "unhealthy"


async def check_minio_health():
    """Check MinIO connection health"""
    try:
        from minio import Minio
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        # Simple bucket list check
        client.list_buckets()
        return "healthy"
    except Exception:
        return "unhealthy"


@router.get("/health/ready")
async def readiness_check():
    """Readiness probe for Kubernetes"""
    
    # Check if the application is ready to serve traffic
    ready = True
    
    # Add any readiness checks here
    # For example: database migrations, model loading, etc.
    
    return {"ready": ready, "timestamp": datetime.utcnow()}


@router.get("/health/live")
async def liveness_check():
    """Liveness probe for Kubernetes"""
    
    # Check if the application is alive
    alive = True
    
    # Add any liveness checks here
    # For example: check if critical components are responsive
    
    return {"alive": alive, "timestamp": datetime.utcnow()}


@router.get("/metrics")
async def get_metrics():
    """Detailed system metrics for monitoring"""
    
    # System metrics
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Process-specific metrics
    process = psutil.Process()
    process_memory = process.memory_info()
    process_cpu = process.cpu_percent()
    
    # Network metrics
    network = psutil.net_io_counters()
    
    return {
        "timestamp": datetime.utcnow(),
        "uptime_seconds": time.time() - start_time,
        "system": {
            "cpu_percent": cpu,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        },
        "process": {
            "pid": process.pid,
            "memory_rss": process_memory.rss,
            "memory_vms": process_memory.vms,
            "cpu_percent": process_cpu,
            "num_threads": process.num_threads(),
            "create_time": process.create_time()
        }
    }