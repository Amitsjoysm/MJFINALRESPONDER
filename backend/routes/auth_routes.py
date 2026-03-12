from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from datetime import datetime, timezone
import logging
import traceback

from services.auth_service import AuthService
from models.user import UserCreate, UserLogin, TokenResponse, UserResponse, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

async def get_db():
    from server import db
    return db

async def get_current_user_from_token(authorization: Optional[str] = Header(None), db: AsyncIOMotorDatabase = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    auth_service = AuthService(db)
    return await auth_service.get_current_user(token)

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Register new user"""
    auth_service = AuthService(db)
    user = await auth_service.register(user_data)
    token = auth_service.create_access_token(user.id)
    
    return TokenResponse(
        access_token=token,
        user=auth_service.user_to_response(user)
    )

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Login user"""
    auth_service = AuthService(db)
    token, user = await auth_service.login(credentials)
    
    return TokenResponse(
        access_token=token,
        user=auth_service.user_to_response(user)
    )

@router.get("/me", response_model=UserResponse)
async def get_profile(user = Depends(get_current_user_from_token), db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get current user profile"""
    auth_service = AuthService(db)
    return auth_service.user_to_response(user)

@router.get("/quota")
async def check_quota(user = Depends(get_current_user_from_token), db: AsyncIOMotorDatabase = Depends(get_db)):
    """Check user quota"""
    auth_service = AuthService(db)
    has_quota = await auth_service.check_quota(user.id)
    
    return {
        "has_quota": has_quota,
        "quota": user.quota,
        "quota_used": user.quota_used,
        "quota_remaining": user.quota - user.quota_used
    }

class UserSettingsUpdate(BaseModel):
    """Update user settings (lead qualification & nurturing)"""
    global_lead_qualification_enabled: Optional[bool] = None
    global_lead_nurturing_enabled: Optional[bool] = None
    default_qualification_criteria_id: Optional[str] = None
    default_nurturing_config_id: Optional[str] = None

@router.put("/settings", response_model=UserResponse)
async def update_settings(
    settings: UserSettingsUpdate,
    user = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update user settings for lead qualification and nurturing"""
    try:
        users_collection = db['users']
        
        # Prepare update data
        update_data = {
            k: v for k, v in settings.model_dump(exclude_unset=True).items()
            if v is not None
        }
        
        if update_data:
            update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            await users_collection.update_one(
                {"id": user.id},
                {"$set": update_data}
            )
        
        # Get updated user
        updated_user_dict = await users_collection.find_one({"id": user.id})
        
        if not updated_user_dict:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Convert dict to User model
        try:
            updated_user = User(**updated_user_dict)
            auth_service = AuthService(db)
            return auth_service.user_to_response(updated_user)
        except Exception as model_error:
            # Fallback: return UserResponse directly from dict
            return UserResponse(
                id=updated_user_dict['id'],
                email=updated_user_dict['email'],
                full_name=updated_user_dict.get('full_name', ''),
                quota=updated_user_dict.get('quota', 100),
                quota_used=updated_user_dict.get('quota_used', 0),
                quota_reset_date=updated_user_dict.get('quota_reset_date', datetime.now(timezone.utc).isoformat()),
                created_at=updated_user_dict.get('created_at', datetime.now(timezone.utc).isoformat()),
                role=updated_user_dict.get('role', 'user'),
                is_active=updated_user_dict.get('is_active', True),
                hubspot_enabled=updated_user_dict.get('hubspot_enabled', False),
                hubspot_connected=updated_user_dict.get('hubspot_connected', False),
                hubspot_portal_id=updated_user_dict.get('hubspot_portal_id'),
                hubspot_auto_sync=updated_user_dict.get('hubspot_auto_sync', False),
                global_lead_qualification_enabled=updated_user_dict.get('global_lead_qualification_enabled', False),
                global_lead_nurturing_enabled=updated_user_dict.get('global_lead_nurturing_enabled', False),
                default_qualification_criteria_id=updated_user_dict.get('default_qualification_criteria_id'),
                default_nurturing_config_id=updated_user_dict.get('default_nurturing_config_id')
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user settings: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")
