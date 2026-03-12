import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timezone, datetime

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

class Config:
    # MongoDB
    MONGO_URL = os.environ['MONGO_URL']
    DB_NAME = os.environ.get('DB_NAME', 'email_assistant_db')
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # JWT
    JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24 * 7  # 7 days
    
    # Dynamic APP_URL (for Codespaces or other environments)
    APP_URL = os.environ.get('APP_URL', '')
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    # Use APP_URL if available, otherwise use GOOGLE_REDIRECT_URI from .env
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:3000/oauth/google/callback')
    
    # Microsoft OAuth
    MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID', '')
    MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET', '')
    MICROSOFT_TENANT_ID = os.environ.get('MICROSOFT_TENANT_ID', 'common')
    MICROSOFT_REDIRECT_URI = os.environ.get('MICROSOFT_REDIRECT_URI', 'http://localhost:3000/oauth/microsoft/callback')
    
    @staticmethod
    def get_dynamic_redirect_uri(provider: str = 'google') -> str:
        """Get dynamic redirect URI based on APP_URL if available"""
        # If APP_URL is set, use it for OAuth redirects (for Codespaces)
        if Config.APP_URL:
            return f"{Config.APP_URL}/api/oauth/{provider}/callback"
        # Otherwise use the configured redirect URI
        if provider == 'google':
            return Config.GOOGLE_REDIRECT_URI
        elif provider == 'microsoft':
            return Config.MICROSOFT_REDIRECT_URI
        return ''
    
    # AI APIs
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')
    COHERE_API_KEY = os.environ.get('COHERE_API_KEY', '')
    EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
    
    # LLM Provider Selection
    PRIMARY_LLM_PROVIDER = os.environ.get('PRIMARY_LLM_PROVIDER', 'groq')  # groq or claude
    FALLBACK_LLM_PROVIDER = os.environ.get('FALLBACK_LLM_PROVIDER', 'claude')  # claude or groq
    
    # Groq Models (cost-effective)
    GROQ_DRAFT_MODEL = 'llama-3.3-70b-versatile'  # Good balance of quality and cost
    GROQ_VALIDATION_MODEL = 'llama-3.3-70b-versatile'
    GROQ_CALENDAR_MODEL = 'llama-3.3-70b-versatile'
    
    # Claude Models (high quality)
    CLAUDE_DRAFT_MODEL = 'claude-3-5-sonnet-20241022'  # Current available model
    CLAUDE_VALIDATION_MODEL = 'claude-3-5-sonnet-20241022'
    CLAUDE_CALENDAR_MODEL = 'claude-3-5-sonnet-20241022'
    
    # Cohere Model
    COHERE_CLASSIFICATION_MODEL = 'embed-english-v3.0'
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Email Polling
    EMAIL_POLL_INTERVAL = 60  # seconds
    FOLLOW_UP_CHECK_INTERVAL = 300  # 5 minutes
    REMINDER_CHECK_INTERVAL = 3600  # 1 hour
    
    # Business Hours (for follow-ups)
    BUSINESS_HOURS_START = 9  # 9 AM
    BUSINESS_HOURS_END = 17  # 5 PM
    
    # Token Tracking
    ENABLE_TOKEN_TRACKING = True
    
    # Quota (per user)
    DEFAULT_QUOTA = 100  # emails per day
    
    # Meeting Detection
    MEETING_CONFIDENCE_THRESHOLD = 0.6
    
    @staticmethod
    def get_current_datetime():
        """Returns current datetime with timezone info for AI agents"""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def get_datetime_string():
        """Returns formatted datetime string for AI agents"""
        now = Config.get_current_datetime()
        return now.strftime('%Y-%m-%d %H:%M:%S %Z')

config = Config()
