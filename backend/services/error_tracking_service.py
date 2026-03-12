"""
Error Tracking Service
Ensures no tasks fail silently - all errors are logged, tracked, and reported
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import traceback

logger = logging.getLogger(__name__)

class ErrorTrackingService:
    """Track and report all system errors to prevent silent failures"""
    
    def __init__(self, db):
        self.db = db
        self.error_log_collection = db['error_logs']
    
    async def log_error(
        self,
        error_type: str,
        error_message: str,
        context: Dict[str, Any],
        severity: str = "error",
        user_id: Optional[str] = None,
        email_id: Optional[str] = None
    ) -> str:
        """
        Log error to database for tracking
        
        Args:
            error_type: Type of error (e.g., "draft_generation_failed", "validation_failed")
            error_message: Error message
            context: Additional context (stack trace, input data, etc.)
            severity: "critical", "error", "warning", "info"
            user_id: User ID if applicable
            email_id: Email ID if applicable
            
        Returns:
            error_log_id
        """
        try:
            import uuid
            error_log_id = str(uuid.uuid4())
            
            error_doc = {
                "id": error_log_id,
                "error_type": error_type,
                "error_message": error_message,
                "severity": severity,
                "context": context,
                "user_id": user_id,
                "email_id": email_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "resolved": False
            }
            
            await self.error_log_collection.insert_one(error_doc)
            
            # Also log to application logs
            log_level = {
                "critical": logger.critical,
                "error": logger.error,
                "warning": logger.warning,
                "info": logger.info
            }.get(severity, logger.error)
            
            log_level(f"[{error_type}] {error_message} | Context: {context}")
            
            return error_log_id
            
        except Exception as e:
            # Even error logging failed - use fallback
            logger.critical(f"CRITICAL: Error logging failed: {e} | Original error: {error_message}")
            return None
    
    async def log_exception(
        self,
        exc: Exception,
        error_type: str,
        context: Dict[str, Any],
        user_id: Optional[str] = None,
        email_id: Optional[str] = None
    ) -> str:
        """
        Log exception with full stack trace
        """
        error_message = str(exc)
        stack_trace = traceback.format_exc()
        
        context['stack_trace'] = stack_trace
        context['exception_type'] = type(exc).__name__
        
        return await self.log_error(
            error_type=error_type,
            error_message=error_message,
            context=context,
            severity="error",
            user_id=user_id,
            email_id=email_id
        )
    
    async def get_recent_errors(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> list:
        """Get recent errors for monitoring"""
        try:
            query = {}
            if user_id:
                query['user_id'] = user_id
            
            errors = await self.error_log_collection.find(query).sort(
                "created_at", -1
            ).limit(limit).to_list(limit)
            
            return errors
            
        except Exception as e:
            logger.error(f"Failed to get recent errors: {e}")
            return []
    
    async def mark_error_resolved(self, error_log_id: str) -> bool:
        """Mark an error as resolved"""
        try:
            result = await self.error_log_collection.update_one(
                {"id": error_log_id},
                {"$set": {
                    "resolved": True,
                    "resolved_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to mark error as resolved: {e}")
            return False


class TaskMonitor:
    """Monitor task execution to ensure nothing fails silently"""
    
    def __init__(self, db, error_tracker: ErrorTrackingService):
        self.db = db
        self.error_tracker = error_tracker
    
    async def track_task(
        self,
        task_name: str,
        task_func,
        context: Dict[str, Any],
        user_id: Optional[str] = None,
        email_id: Optional[str] = None,
        retry_count: int = 0,
        max_retries: int = 2
    ):
        """
        Execute task with comprehensive error tracking
        
        Ensures:
        - All errors are logged
        - Retries are attempted
        - Failures are reported
        - Status is tracked
        """
        try:
            # Execute task
            result = await task_func()
            
            # Log success
            logger.info(f"✓ Task succeeded: {task_name}")
            
            return {"success": True, "result": result, "error": None}
            
        except Exception as e:
            # Log failure
            error_log_id = await self.error_tracker.log_exception(
                exc=e,
                error_type=f"{task_name}_failed",
                context={
                    **context,
                    "retry_count": retry_count,
                    "max_retries": max_retries
                },
                user_id=user_id,
                email_id=email_id
            )
            
            # Retry if allowed
            if retry_count < max_retries:
                logger.warning(f"⚠ Task failed, retrying: {task_name} (attempt {retry_count + 1}/{max_retries})")
                return await self.track_task(
                    task_name=task_name,
                    task_func=task_func,
                    context=context,
                    user_id=user_id,
                    email_id=email_id,
                    retry_count=retry_count + 1,
                    max_retries=max_retries
                )
            else:
                # Max retries reached
                logger.error(f"✗ Task failed after {max_retries} retries: {task_name}")
                
                # Update email status if applicable
                if email_id:
                    await self.db.emails.update_one(
                        {"id": email_id},
                        {"$set": {
                            "status": "error",
                            "error_message": str(e),
                            "error_log_id": error_log_id,
                            "failed_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                
                return {
                    "success": False,
                    "result": None,
                    "error": str(e),
                    "error_log_id": error_log_id
                }


async def ensure_no_silent_failures(db, operation_name: str, operation_func, **kwargs):
    """
    Wrapper function to ensure operations don't fail silently
    
    Usage:
        result = await ensure_no_silent_failures(
            db=db,
            operation_name="draft_generation",
            operation_func=lambda: ai_service.generate_draft(...),
            user_id=user_id,
            email_id=email_id
        )
    """
    error_tracker = ErrorTrackingService(db)
    monitor = TaskMonitor(db, error_tracker)
    
    return await monitor.track_task(
        task_name=operation_name,
        task_func=operation_func,
        context=kwargs,
        user_id=kwargs.get('user_id'),
        email_id=kwargs.get('email_id')
    )
