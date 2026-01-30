import structlog
from datetime import datetime
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..core.models import SystemLog

logger = structlog.get_logger()


class LoggingService:
    """Service for system logging and monitoring"""
    
    def __init__(self):
        self.initialized = False
    
    async def initialize(self):
        """Initialize logging service"""
        self.initialized = True
        logger.info("Logging service initialized")
    
    async def log_request(
        self,
        request_id: str,
        model_type: str,
        image_filename: str,
        user_id: str = None,
        ip_address: str = None
    ):
        """Log assessment request"""
        await self._write_log(
            level="INFO",
            message=f"Assessment request: {model_type} model for {image_filename}",
            module="assessments",
            function="create_assessment",
            request_id=request_id,
            user_id=user_id,
            ip_address=ip_address,
            context={
                "model_type": model_type,
                "image_filename": image_filename
            }
        )
    
    async def log_completion(
        self,
        request_id: str,
        assessment_id: int,
        success: bool
    ):
        """Log assessment completion"""
        level = "INFO" if success else "ERROR"
        message = f"Assessment {'completed' if success else 'failed'} for ID: {assessment_id}"
        
        await self._write_log(
            level=level,
            message=message,
            module="assessments",
            function="create_assessment",
            request_id=request_id,
            context={
                "assessment_id": assessment_id,
                "success": success
            }
        )
    
    async def log_error(
        self,
        request_id: str,
        error_message: str,
        error_type: str,
        module: str = "unknown",
        function: str = "unknown",
        context: dict = None
    ):
        """Log error with context"""
        await self._write_log(
            level="ERROR",
            message=f"Error in {module}.{function}: {error_message}",
            module=module,
            function=function,
            request_id=request_id,
            context={
                "error_message": error_message,
                "error_type": error_type,
                **(context or {})
            }
        )
    
    async def log_model_performance(
        self,
        model_type: str,
        processing_time_ms: float,
        confidence: float,
        prediction: str
    ):
        """Log model performance metrics"""
        await self._write_log(
            level="INFO",
            message=f"Model performance: {model_type}",
            module="models",
            function="inference",
            context={
                "model_type": model_type,
                "processing_time_ms": processing_time_ms,
                "confidence": confidence,
                "prediction": prediction
            }
        )
    
    async def log_system_event(
        self,
        level: str,
        message: str,
        module: str,
        function: str = None,
        context: dict = None
    ):
        """Log general system events"""
        await self._write_log(
            level=level,
            message=message,
            module=module,
            function=function,
            context=context
        )
    
    async def _write_log(
        self,
        level: str,
        message: str,
        module: str,
        function: str = None,
        request_id: str = None,
        user_id: str = None,
        ip_address: str = None,
        context: dict = None
    ):
        """Write log entry to database and console"""
        
        # Console logging (structured)
        log_data = {
            "level": level,
            "message": message,
            "module": module,
            "function": function,
            "request_id": request_id,
            "user_id": user_id,
            "ip_address": ip_address,
            "context": context
        }
        
        # Remove None values to clean up log
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        # Log to console based on level
        if level == "DEBUG":
            logger.debug("Application log", **log_data)
        elif level == "INFO":
            logger.info("Application log", **log_data)
        elif level == "WARNING":
            logger.warning("Application log", **log_data)
        elif level == "ERROR":
            logger.error("Application log", **log_data)
        elif level == "CRITICAL":
            logger.critical("Application log", **log_data)
        
        # Write to database for ERROR and WARNING levels
        if level in ["ERROR", "WARNING", "CRITICAL"] and self.initialized:
            try:
                db = SessionLocal()
                db_log = SystemLog(
                    level=level,
                    message=message,
                    module=module,
                    function=function,
                    request_id=request_id,
                    user_id=user_id,
                    ip_address=ip_address,
                    context=context
                )
                db.add(db_log)
                db.commit()
                db.close()
            except Exception as e:
                logger.error("Failed to write log to database", error=str(e))
    
    async def get_logs(
        self,
        level: str = None,
        module: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> list:
        """Retrieve logs from database"""
        if not self.initialized:
            return []
        
        try:
            db = SessionLocal()
            query = db.query(SystemLog)
            
            if level:
                query = query.filter(SystemLog.level == level)
            if module:
                query = query.filter(SystemLog.module == module)
            
            logs = query.order_by(SystemLog.created_at.desc()).offset(offset).limit(limit).all()
            
            result = []
            for log in logs:
                result.append({
                    "id": log.id,
                    "level": log.level,
                    "message": log.message,
                    "module": log.module,
                    "function": log.function,
                    "request_id": log.request_id,
                    "user_id": log.user_id,
                    "ip_address": log.ip_address,
                    "context": log.context,
                    "created_at": log.created_at
                })
            
            db.close()
            return result
            
        except Exception as e:
            logger.error("Failed to retrieve logs", error=str(e))
            return []


# Global logging service instance
logging_service = LoggingService()