"""Input validation utilities using Pydantic"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator, EmailStr
import re

from exceptions import ValidationError

class EmailValidator:
    """Email validation utilities"""
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise ValidationError("Invalid email format", "email")
        return email.lower()
    
    @staticmethod
    def validate_password(password: str) -> str:
        """Validate password strength"""
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters", "password")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain uppercase letter", "password")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain lowercase letter", "password")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain number", "password")
        return password

class TextSanitizer:
    """Text sanitization to prevent injection attacks"""
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove HTML tags"""
        import html
        return html.escape(text)
    
    @staticmethod
    def sanitize_email_body(text: str) -> str:
        """Sanitize email body"""
        # Remove potentially dangerous patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
        ]
        for pattern in dangerous_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        return text

class RateLimiter:
    """Simple in-memory rate limiter (use Redis in production)"""
    
    def __init__(self):
        self.requests = {}
    
    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if rate limit is exceeded"""
        import time
        current_time = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < window
        ]
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        self.requests[key].append(current_time)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()
