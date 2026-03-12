"""Global error handler middleware"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from exceptions import (
    EmailAssistantException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ResourceNotFoundError,
    QuotaExceededError,
    ExternalServiceError
)

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    
    # Log error
    logger.error(f"Error processing request {request.url}: {exc}", exc_info=True)
    
    # Handle custom exceptions
    if isinstance(exc, AuthenticationError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": exc.code, "message": exc.message}
        )
    
    elif isinstance(exc, AuthorizationError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": exc.code, "message": exc.message}
        )
    
    elif isinstance(exc, ValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": exc.code,
                "message": exc.message,
                "field": exc.field
            }
        )
    
    elif isinstance(exc, ResourceNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": exc.code, "message": exc.message}
        )
    
    elif isinstance(exc, QuotaExceededError):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": exc.code, "message": exc.message}
        )
    
    elif isinstance(exc, ExternalServiceError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": exc.code, "message": exc.message}
        )
    
    elif isinstance(exc, EmailAssistantException):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": exc.code, "message": exc.message}
        )
    
    # Handle validation errors from Pydantic
    elif isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors()
            }
        )
    
    # Handle unexpected errors
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": exc.errors()
        }
    )
