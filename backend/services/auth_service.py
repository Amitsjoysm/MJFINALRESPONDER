from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from typing import Optional

from config import config
from models.user import User, UserCreate, UserLogin, UserResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, user_id: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(hours=config.JWT_EXPIRATION_HOURS)
        to_encode = {"sub": user_id, "exp": expire}
        return jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    
    async def register(self, user_data: UserCreate) -> User:
        # Check if user exists
        existing = await self.db.users.find_one({"email": user_data.email})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        user = User(
            email=user_data.email,
            password_hash=self.hash_password(user_data.password),
            full_name=user_data.full_name
        )
        
        doc = user.model_dump()
        await self.db.users.insert_one(doc)
        
        return user
    
    async def login(self, credentials: UserLogin) -> tuple[str, User]:
        user_doc = await self.db.users.find_one({"email": credentials.email})
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        user = User(**user_doc)
        
        if not self.verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        token = self.create_access_token(user.id)
        return token, user
    
    async def get_current_user(self, token: str) -> User:
        try:
            payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user_doc = await self.db.users.find_one({"id": user_id})
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return User(**user_doc)
    
    async def check_quota(self, user_id: str) -> bool:
        """Check if user has quota available"""
        user_doc = await self.db.users.find_one({"id": user_id})
        if not user_doc:
            return False
        
        user = User(**user_doc)
        
        # Reset quota if new day
        quota_reset = datetime.fromisoformat(user.quota_reset_date)
        now = datetime.now(timezone.utc)
        
        if now.date() > quota_reset.date():
            # Reset quota
            await self.db.users.update_one(
                {"id": user_id},
                {"$set": {
                    "quota_used": 0,
                    "quota_reset_date": now.isoformat()
                }}
            )
            return True
        
        return user.quota_used < user.quota
    
    async def increment_quota(self, user_id: str):
        """Increment quota usage"""
        await self.db.users.update_one(
            {"id": user_id},
            {"$inc": {"quota_used": 1}}
        )
    
    def user_to_response(self, user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            quota=user.quota,
            quota_used=user.quota_used,
            quota_reset_date=user.quota_reset_date,
            created_at=user.created_at,
            role=user.role,
            is_active=user.is_active,
            hubspot_enabled=user.hubspot_enabled,
            hubspot_connected=user.hubspot_connected,
            hubspot_portal_id=user.hubspot_portal_id,
            hubspot_auto_sync=user.hubspot_auto_sync,
            global_lead_qualification_enabled=user.global_lead_qualification_enabled,
            global_lead_nurturing_enabled=user.global_lead_nurturing_enabled,
            default_qualification_criteria_id=user.default_qualification_criteria_id,
            default_nurturing_config_id=user.default_nurturing_config_id
        )
