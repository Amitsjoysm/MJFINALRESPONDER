"""
Global Error Handler and Logger
Implements strict error tracking to prevent silent failures in production
"""
import logging
import traceback
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from functools import wraps
import asyncio

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/app_errors.log')
    ]
)

logger = logging.getLogger(__name__)

class ErrorTracker:
    """Track and log all errors in production"""
    
    @staticmethod
    def log_error(
        error: Exception,
        context: str,
        user_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Log error with full context"""
        error_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "user_id": user_id,
            "traceback": traceback.format_exc(),
            "additional_data": additional_data or {}
        }
        
        # Log to file
        logger.error(f"PRODUCTION ERROR: {context}", extra=error_data)
        
        # In production, you would also:
        # - Send to error tracking service (Sentry, Rollbar, etc.)
        # - Store in database for admin review
        # - Send alerts for critical errors
        
        return error_data
    
    @staticmethod
    def log_warning(message: str, context: str, additional_data: Optional[Dict] = None):
        """Log warnings that might indicate issues"""
        logger.warning(f"WARNING [{context}]: {message}", extra=additional_data or {})
    
    @staticmethod
    def log_info(message: str, context: str):
        """Log important information"""
        logger.info(f"INFO [{context}]: {message}")


def handle_errors(context: str):
    """Decorator to handle errors in functions"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                ErrorTracker.log_error(
                    e,
                    context=f"{context} - {func.__name__}",
                    additional_data={
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ErrorTracker.log_error(
                    e,
                    context=f"{context} - {func.__name__}",
                    additional_data={
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }
                )
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def safe_dict_access(dictionary: Dict, key: str, default: Any = None, context: str = "unknown") -> Any:
    """Safely access dictionary with logging"""
    try:
        return dictionary.get(key, default)
    except Exception as e:
        ErrorTracker.log_error(
            e,
            context=f"safe_dict_access - {context}",
            additional_data={"key": key, "has_key": key in dictionary}
        )
        return default


def safe_model_parse(model_class, data: Dict, context: str = "unknown"):
    """Safely parse Pydantic model with detailed error logging"""
    try:
        return model_class(**data)
    except Exception as e:
        ErrorTracker.log_error(
            e,
            context=f"model_parse - {model_class.__name__} - {context}",
            additional_data={
                "data_keys": list(data.keys()) if isinstance(data, dict) else "not a dict",
                "model_fields": list(model_class.model_fields.keys()) if hasattr(model_class, 'model_fields') else "no fields"
            }
        )
        raise
