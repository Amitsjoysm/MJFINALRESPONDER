"""Custom exceptions for better error handling and debugging"""

class EmailAssistantException(Exception):
    """Base exception for all application errors"""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class AuthenticationError(EmailAssistantException):
    """Authentication related errors"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")

class AuthorizationError(EmailAssistantException):
    """Authorization related errors"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "AUTHZ_ERROR")

class ValidationError(EmailAssistantException):
    """Validation errors"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")

class ResourceNotFoundError(EmailAssistantException):
    """Resource not found errors"""
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with id '{identifier}' not found"
        super().__init__(message, "NOT_FOUND")

class QuotaExceededError(EmailAssistantException):
    """Quota exceeded errors"""
    def __init__(self, message: str = "Quota exceeded"):
        super().__init__(message, "QUOTA_EXCEEDED")

class ExternalServiceError(EmailAssistantException):
    """External service errors (Groq, Cohere, Gmail, etc.)"""
    def __init__(self, service: str, message: str):
        super().__init__(f"{service}: {message}", "EXTERNAL_SERVICE_ERROR")

class EmailAccountError(EmailAssistantException):
    """Email account related errors"""
    def __init__(self, message: str):
        super().__init__(message, "EMAIL_ACCOUNT_ERROR")
