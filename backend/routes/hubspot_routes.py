"""HubSpot integration routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import logging
import secrets

from models.user import User
from models.hubspot_credential import HubSpotCredential, HubSpotCredentialResponse, HubSpotConnectionStatus
from utils.hubspot_oauth import hubspot_oauth
from utils.encryption import get_encryption_service
from services.hubspot_service import HubSpotService
from services.auth_service import AuthService

router = APIRouter(prefix="/hubspot", tags=["HubSpot Integration"])
logger = logging.getLogger(__name__)

async def get_db():
    from server import db
    return db

async def get_current_user_from_token(authorization: Optional[str] = None, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get current user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    auth_service = AuthService(db)
    return await auth_service.get_current_user(token)

@router.get("/start-oauth")
async def start_hubspot_oauth(
    authorization: str = Query(..., alias="Authorization"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Initiate HubSpot OAuth flow"""
    user = await get_current_user_from_token(authorization, db)
    
    # Check if user has HubSpot enabled
    if not user.hubspot_enabled:
        raise HTTPException(
            status_code=403,
            detail="HubSpot integration not enabled for your account. Contact admin."
        )
    
    # Generate state token for CSRF protection
    state_token = secrets.token_urlsafe(32)
    
    # Store state token temporarily (in a real app, use Redis with expiration)
    await db.oauth_states.insert_one({
        "state": state_token,
        "user_id": user.id,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)
    })
    
    authorization_url = hubspot_oauth.get_authorization_url(state_token)
    
    logger.info(f"Starting HubSpot OAuth for user {user.id}")
    
    return {
        "authorization_url": authorization_url,
        "state": state_token
    }

@router.get("/callback")
async def hubspot_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Handle HubSpot OAuth callback"""
    logger.info(f"Received HubSpot callback with state: {state}")
    
    # Verify state token
    state_record = await db.oauth_states.find_one({"state": state})
    
    if not state_record:
        logger.error("Invalid state token")
        raise HTTPException(status_code=400, detail="Invalid or expired state token")
    
    # Check if state is expired
    if state_record["expires_at"] < datetime.now(timezone.utc):
        logger.error("Expired state token")
        await db.oauth_states.delete_one({"state": state})
        raise HTTPException(status_code=400, detail="State token expired")
    
    user_id = state_record["user_id"]
    
    # Delete state token
    await db.oauth_states.delete_one({"state": state})
    
    try:
        # Exchange code for tokens
        token_response = await hubspot_oauth.exchange_code_for_token(code)
        
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in", 3600)
        
        # Get encryption service
        encryption_service = get_encryption_service()
        
        # Encrypt tokens
        encrypted_access_token = encryption_service.encrypt(access_token)
        encrypted_refresh_token = encryption_service.encrypt(refresh_token)
        
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        
        # Get HubSpot account info
        account_info = await hubspot_oauth.get_account_info(access_token)
        portal_id = str(account_info.get("portalId", "unknown"))
        
        # Check if credential already exists
        existing_cred = await db.hubspot_credentials.find_one({"user_id": user_id})
        
        if existing_cred:
            # Update existing credential
            await db.hubspot_credentials.update_one(
                {"user_id": user_id},
                {"$set": {
                    "access_token": encrypted_access_token,
                    "refresh_token": encrypted_refresh_token,
                    "expires_in": expires_in,
                    "expires_at": expires_at.isoformat(),
                    "hubspot_portal_id": portal_id,
                    "is_enabled": True,
                    "connected_at": datetime.now(timezone.utc).isoformat(),
                    "disconnected_at": None,
                    "error_message": None,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            logger.info(f"Updated HubSpot credentials for user {user_id}")
        else:
            # Create new credential
            credential = {
                "user_id": user_id,
                "access_token": encrypted_access_token,
                "refresh_token": encrypted_refresh_token,
                "token_type": "Bearer",
                "expires_in": expires_in,
                "expires_at": expires_at.isoformat(),
                "scope": " ".join(hubspot_oauth.scopes),
                "hubspot_portal_id": portal_id,
                "is_enabled": True,
                "connected_at": datetime.now(timezone.utc).isoformat(),
                "disconnected_at": None,
                "last_sync_at": None,
                "error_message": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.hubspot_credentials.insert_one(credential)
            logger.info(f"Created HubSpot credentials for user {user_id}")
        
        # Update user's hubspot_connected field
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "hubspot_connected": True,
                "hubspot_portal_id": portal_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Redirect to frontend success page
        frontend_url = os.environ.get("REACT_APP_FRONTEND_URL", "http://localhost:3000")
        return {
            "status": "success",
            "message": "HubSpot account connected successfully",
            "redirect_url": f"{frontend_url}/settings?hubspot=connected"
        }
        
    except Exception as e:
        logger.error(f"Error during HubSpot OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete HubSpot connection: {str(e)}")

@router.get("/status")
async def get_hubspot_status(
    authorization: str = Query(..., alias="Authorization"),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> HubSpotConnectionStatus:
    """Get HubSpot connection status for current user"""
    user = await get_current_user_from_token(authorization, db)
    
    credential = await db.hubspot_credentials.find_one({"user_id": user.id})
    
    if not credential:
        return HubSpotConnectionStatus(
            connected=False,
            enabled=user.hubspot_enabled
        )
    
    return HubSpotConnectionStatus(
        connected=credential.get("is_enabled", False),
        enabled=user.hubspot_enabled,
        connected_at=credential.get("connected_at"),
        last_sync_at=credential.get("last_sync_at"),
        error_message=credential.get("error_message")
    )

@router.post("/disconnect")
async def disconnect_hubspot(
    authorization: str = Query(..., alias="Authorization"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Disconnect HubSpot account"""
    user = await get_current_user_from_token(authorization, db)
    
    result = await db.hubspot_credentials.update_one(
        {"user_id": user.id},
        {"$set": {
            "is_enabled": False,
            "disconnected_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="HubSpot connection not found")
    
    # Update user's hubspot_connected field
    await db.users.update_one(
        {"id": user.id},
        {"$set": {
            "hubspot_connected": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logger.info(f"Disconnected HubSpot for user {user.id}")
    
    return {
        "status": "success",
        "message": "HubSpot account disconnected"
    }

@router.post("/sync-leads")
async def sync_leads_to_hubspot(
    lead_ids: Optional[List[str]] = None,
    authorization: str = Query(..., alias="Authorization"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Sync leads to HubSpot (manual sync)"""
    user = await get_current_user_from_token(authorization, db)
    
    # Check if HubSpot is connected
    if not user.hubspot_connected:
        raise HTTPException(status_code=403, detail="HubSpot not connected")
    
    # Get HubSpot credentials
    credential = await db.hubspot_credentials.find_one({"user_id": user.id})
    
    if not credential or not credential.get("is_enabled"):
        raise HTTPException(status_code=403, detail="HubSpot connection not configured or disabled")
    
    # Get encryption service
    encryption_service = get_encryption_service()
    
    # Decrypt access token
    access_token = encryption_service.decrypt(credential["access_token"])
    
    # Get leads to sync
    query = {"user_id": user.id}
    if lead_ids:
        query["id"] = {"$in": lead_ids}
    else:
        # Sync only leads that haven't been synced or failed
        query["$or"] = [
            {"sync_status": {"$exists": False}},
            {"sync_status": "pending"},
            {"sync_status": "failed"}
        ]
    
    leads_cursor = db.leads.find(query)
    leads = await leads_cursor.to_list(length=1000)
    
    if not leads:
        return {
            "status": "success",
            "message": "No leads to sync",
            "synced": 0
        }
    
    # Add sync task to background
    background_tasks.add_task(
        sync_leads_background,
        user_id=user.id,
        leads=leads,
        access_token=access_token,
        db=db
    )
    
    logger.info(f"Started syncing {len(leads)} leads for user {user.id}")
    
    return {
        "status": "syncing",
        "message": f"Started syncing {len(leads)} lead(s) to HubSpot",
        "lead_count": len(leads)
    }

async def sync_leads_background(user_id: str, leads: List[dict], access_token: str, db: AsyncIOMotorDatabase):
    """Background task for syncing leads to HubSpot"""
    logger.info(f"Background sync started for {len(leads)} leads")
    
    hubspot_service = HubSpotService(access_token)
    
    successful = 0
    failed = 0
    
    for lead in leads:
        try:
            result = await hubspot_service.sync_lead_to_hubspot(lead)
            
            if result["status"] == "success":
                # Update lead with sync status
                await db.leads.update_one(
                    {"id": lead["id"]},
                    {"$set": {
                        "sync_status": "synced",
                        "hubspot_contact_id": result.get("hubspot_contact_id"),
                        "synced_at": datetime.now(timezone.utc).isoformat(),
                        "sync_error": None,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                successful += 1
            else:
                await db.leads.update_one(
                    {"id": lead["id"]},
                    {"$set": {
                        "sync_status": "failed",
                        "sync_error": result.get("message"),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                failed += 1
        except Exception as e:
            logger.error(f"Error syncing lead {lead['id']}: {e}")
            await db.leads.update_one(
                {"id": lead["id"]},
                {"$set": {
                    "sync_status": "failed",
                    "sync_error": str(e),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            failed += 1
    
    # Update last sync time
    await db.hubspot_credentials.update_one(
        {"user_id": user_id},
        {"$set": {
            "last_sync_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logger.info(f"Background sync completed: {successful} successful, {failed} failed")

# Admin routes
@router.post("/admin/enable-for-user")
async def admin_enable_hubspot_for_user(
    target_user_id: str,
    reason: Optional[str] = None,
    authorization: str = Query(..., alias="Authorization"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Admin enables HubSpot access for a user"""
    admin = await get_current_user_from_token(authorization, db)
    
    # Check if user is admin or super admin
    if admin.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only administrators can access this endpoint")
    
    # Check if target user exists
    target_user = await db.users.find_one({"id": target_user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Enable HubSpot for user
    await db.users.update_one(
        {"id": target_user_id},
        {"$set": {
            "hubspot_enabled": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log admin action
    await db.admin_audit_logs.insert_one({
        "admin_id": admin.id,
        "target_user_id": target_user_id,
        "action": "enable_hubspot",
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    logger.info(f"Admin {admin.id} enabled HubSpot for user {target_user_id}")
    
    return {
        "status": "success",
        "message": f"HubSpot access enabled for user {target_user.get('email')}"
    }

@router.post("/admin/disable-for-user")
async def admin_disable_hubspot_for_user(
    target_user_id: str,
    reason: str,
    authorization: str = Query(..., alias="Authorization"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Admin disables HubSpot access for a user"""
    admin = await get_current_user_from_token(authorization, db)
    
    # Check if user is admin or super admin
    if admin.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only administrators can access this endpoint")
    
    # Check if target user exists
    target_user = await db.users.find_one({"id": target_user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Disable HubSpot for user
    await db.users.update_one(
        {"id": target_user_id},
        {"$set": {
            "hubspot_enabled": False,
            "hubspot_connected": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Disable credential if exists
    await db.hubspot_credentials.update_one(
        {"user_id": target_user_id},
        {"$set": {
            "is_enabled": False,
            "disconnected_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log admin action
    await db.admin_audit_logs.insert_one({
        "admin_id": admin.id,
        "target_user_id": target_user_id,
        "action": "disable_hubspot",
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    logger.info(f"Admin {admin.id} disabled HubSpot for user {target_user_id}")
    
    return {
        "status": "success",
        "message": f"HubSpot access disabled for user {target_user.get('email')}"
    }

@router.get("/admin/connections")
async def admin_list_hubspot_connections(
    skip: int = 0,
    limit: int = 100,
    authorization: str = Query(..., alias="Authorization"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Admin lists all HubSpot connections"""
    admin = await get_current_user_from_token(authorization, db)
    
    # Check if user is admin or super admin
    if admin.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only administrators can access this endpoint")
    
    credentials_cursor = db.hubspot_credentials.find().skip(skip).limit(limit)
    credentials = await credentials_cursor.to_list(length=limit)
    
    # Get user info for each credential
    result = []
    for cred in credentials:
        user = await db.users.find_one({"id": cred["user_id"]})
        result.append({
            "id": cred.get("id", str(cred.get("_id"))),
            "user_id": cred["user_id"],
            "user_email": user.get("email") if user else "Unknown",
            "is_enabled": cred.get("is_enabled", False),
            "hubspot_portal_id": cred.get("hubspot_portal_id"),
            "connected_at": cred.get("connected_at"),
            "last_sync_at": cred.get("last_sync_at"),
            "error_message": cred.get("error_message")
        })
    
    return result

import os
