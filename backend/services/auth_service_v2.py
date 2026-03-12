"""Refactored Auth Service with SOLID principles"""
from typing import Optional, Tuple
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import logging

from config import config
from models.user import User, UserCreate, UserLogin, UserResponse
from repositories.base_repository import GenericRepository
from exceptions import AuthenticationError, ValidationError, QuotaExceededError
from utils.validators import EmailValidator

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordHasher:
    """Single Responsibility: Password hashing"""
    
    @staticmethod
    def hash(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

class TokenManager:
    """Single Responsibility: JWT token management"""
    
    def __init__(self, secret: str, algorithm: str, expiration_hours: int):
        self.secret = secret
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours
    
    def create_token(self, user_id: str) -> str:
        """Create JWT token"""
        expire = datetime.now(timezone.utc) + timedelta(hours=self.expiration_hours)
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> str:
        """Decode and validate token"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid token payload")
            return user_id
        except JWTError as e:
            logger.warning(f"Token decode error: {e}")
            raise AuthenticationError("Invalid or expired token")

class QuotaManager:
    """Single Responsibility: Quota management"""
    
    def __init__(self, repository: GenericRepository):
        self.repository = repository
    
    async def check_quota(self, user_id: str) -> Tuple[bool, int]:
        """Check if user has quota available"""
        user_doc = await self.repository.find_by_id(user_id)
        if not user_doc:
            return False, 0
        
        user = User(**user_doc)
        
        # Reset quota if new day
        quota_reset = datetime.fromisoformat(user.quota_reset_date)
        now = datetime.now(timezone.utc)
        
        if now.date() > quota_reset.date():
            # Reset quota
            await self.repository.update(user_id, {
                "quota_used": 0,
                "quota_reset_date": now.isoformat()
            })
            return True, user.quota
        
        remaining = user.quota - user.quota_used
        return remaining > 0, remaining
    
    async def increment_quota(self, user_id: str) -> bool:
        """Increment quota usage"""
        user_doc = await self.repository.find_by_id(user_id)
        if not user_doc:
            return False
        
        user = User(**user_doc)
        new_usage = user.quota_used + 1
        
        if new_usage > user.quota:
            raise QuotaExceededError()
        
        await self.repository.update(user_id, {"quota_used": new_usage})
        return True

class AuthService:
    """Authentication service with dependency injection"""
    
    def __init__(self, repository: GenericRepository):
        self.repository = repository
        self.password_hasher = PasswordHasher()
        self.token_manager = TokenManager(
            config.JWT_SECRET,
            config.JWT_ALGORITHM,
            config.JWT_EXPIRATION_HOURS
        )
        self.quota_manager = QuotaManager(repository)
    
    async def register(self, user_data: UserCreate) -> User:
        """Register new user"""
        # Validate email
        try:
            email = EmailValidator.validate_email(user_data.email)
        except ValidationError:
            raise
        
        # Validate password
        try:
            EmailValidator.validate_password(user_data.password)
        except ValidationError:
            raise
        
        # Check if user exists
        existing = await self.repository.find_one({"email": email})
        if existing:
            raise ValidationError("Email already registered", "email")
        
        # Create user
        user = User(
            email=email,
            password_hash=self.password_hasher.hash(user_data.password),
            full_name=user_data.full_name
        )
        
        doc = user.model_dump()
        await self.repository.create(doc)
        
        logger.info(f"User registered: {email}")
        return user
    
    async def login(self, credentials: UserLogin) -> Tuple[str, User]:
        """Login user"""
        email = EmailValidator.validate_email(credentials.email)
        
        user_doc = await self.repository.find_one({"email": email})
        if not user_doc:
            raise AuthenticationError("Invalid email or password")
        
        user = User(**user_doc)
        
        if not self.password_hasher.verify(credentials.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        
        token = self.token_manager.create_token(user.id)
        logger.info(f"User logged in: {email}")
        
        return token, user
    
    async def get_current_user(self, token: str) -> User:
        """Get user from token"""
        user_id = self.token_manager.decode_token(token)
        
        user_doc = await self.repository.find_by_id(user_id)
        if not user_doc:
            raise AuthenticationError("User not found")
        
        return User(**user_doc)
    
    async def check_quota(self, user_id: str) -> Tuple[bool, int]:
        """Check user quota"""
        return await self.quota_manager.check_quota(user_id)
    
    async def increment_quota(self, user_id: str) -> bool:
        """Increment quota usage"""
        return await self.quota_manager.increment_quota(user_id)
    
    def user_to_response(self, user: User) -> UserResponse:
        """Convert user to response model"""
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            quota=user.quota,
            quota_used=user.quota_used,
            quota_reset_date=user.quota_reset_date,
            created_at=user.created_at
        )
