from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
import uuid
import jwt

from routes.auth_routes import get_current_user_from_token, get_db
from services.calendar_service import CalendarService
from services.oauth_service import OAuthService
from models.calendar import CalendarProvider, CalendarEvent, CalendarEventCreate, CalendarEventResponse
from models.user import User
from config import config

router = APIRouter(prefix="/calendar", tags=["calendar"])

@router.get("/oauth/google")
async def start_google_calendar_oauth(
    request: Request,
    token: str = Query(..., description='JWT token for authentication'),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Start Google Calendar OAuth flow"""
    try:
        # Validate token and get user
        from services.auth_service import AuthService
        auth_service = AuthService(db)
        user = await auth_service.get_current_user(token)
        
        # Get frontend URL from request (base URL only, no paths)
        from urllib.parse import urlparse
        frontend_url = request.headers.get('origin')
        if not frontend_url:
            referer = request.headers.get('referer')
            if referer:
                parsed = urlparse(referer)
                frontend_url = f"{parsed.scheme}://{parsed.netloc}"
            else:
                frontend_url = config.APP_URL
        
        if frontend_url and frontend_url.endswith('/'):
            frontend_url = frontend_url[:-1]
        
        # Generate state for OAuth
        oauth_service = OAuthService(db)
        state = str(uuid.uuid4())
        
        # Store state in DB for verification with frontend_url
        await db.oauth_states.insert_one({
            "state": state,
            "user_id": user.id,
            "provider": "google",
            "account_type": "calendar",
            "frontend_url": frontend_url,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Get OAuth URL
        auth_url = oauth_service.get_google_auth_url(state)
        
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth: {str(e)}")

@router.get("/oauth/microsoft")
async def start_microsoft_calendar_oauth(
    request: Request,
    token: str = Query(..., description='JWT token for authentication'),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Start Microsoft Calendar OAuth flow"""
    try:
        # Validate token and get user
        from services.auth_service import AuthService
        auth_service = AuthService(db)
        user = await auth_service.get_current_user(token)
        
        # Get frontend URL from request (base URL only, no paths)
        from urllib.parse import urlparse
        frontend_url = request.headers.get('origin')
        if not frontend_url:
            referer = request.headers.get('referer')
            if referer:
                parsed = urlparse(referer)
                frontend_url = f"{parsed.scheme}://{parsed.netloc}"
            else:
                frontend_url = config.APP_URL
        
        if frontend_url and frontend_url.endswith('/'):
            frontend_url = frontend_url[:-1]
        
        # Generate state for OAuth
        oauth_service = OAuthService(db)
        state = str(uuid.uuid4())
        
        # Store state in DB for verification with frontend_url
        await db.oauth_states.insert_one({
            "state": state,
            "user_id": user.id,
            "provider": "microsoft",
            "account_type": "calendar",
            "frontend_url": frontend_url,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Get OAuth URL
        auth_url = oauth_service.get_microsoft_auth_url(state)
        
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth: {str(e)}")

@router.get("/providers")
async def list_calendar_providers(
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List calendar providers"""
    providers = await db.calendar_providers.find({"user_id": user.id}).to_list(100)
    
    return [
        {
            "id": p['id'],
            "provider": p['provider'],
            "email": p['email'],
            "is_active": p['is_active'],
            "last_sync": p.get('last_sync'),
            "created_at": p['created_at']
        }
        for p in providers
    ]

@router.delete("/providers/{provider_id}")
async def delete_calendar_provider(
    provider_id: str,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete calendar provider"""
    result = await db.calendar_providers.delete_one({"id": provider_id, "user_id": user.id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return {"message": "Provider deleted successfully"}

@router.post("/events", response_model=CalendarEventResponse)
async def create_calendar_event(
    event_data: CalendarEventCreate,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create calendar event"""
    # Get provider
    provider_doc = await db.calendar_providers.find_one({
        "id": event_data.calendar_provider_id,
        "user_id": user.id
    })
    
    if not provider_doc:
        raise HTTPException(status_code=404, detail="Calendar provider not found")
    
    provider = CalendarProvider(**provider_doc)
    calendar_service = CalendarService(db)
    
    # Check conflicts
    conflicts = await calendar_service.check_conflicts(
        provider.id,
        event_data.start_time,
        event_data.end_time
    )
    
    if conflicts:
        raise HTTPException(
            status_code=409,
            detail=f"Conflict with {len(conflicts)} existing event(s)"
        )
    
    # Create event in calendar provider (Google or Microsoft)
    event_dict = {
        'title': event_data.title,
        'description': event_data.description,
        'location': event_data.location,
        'start_time': event_data.start_time,
        'end_time': event_data.end_time,
        'timezone': event_data.timezone,
        'attendees': event_data.attendees
    }
    
    # Create event based on provider type
    if provider.provider == 'google':
        event_result = await calendar_service.create_event_google(provider, event_dict)
    elif provider.provider == 'microsoft':
        event_result = await calendar_service.create_event_outlook(provider, event_dict)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported calendar provider: {provider.provider}")
    
    if not event_result:
        raise HTTPException(status_code=500, detail="Failed to create event")
    
    # Save to DB
    event_dict.update(event_result)  # Add event_id, meet_link, html_link from provider
    event = await calendar_service.save_event(user.id, provider.id, event_dict)
    
    return CalendarEventResponse(
        id=event.id,
        calendar_provider_id=event.calendar_provider_id,
        title=event.title,
        description=event.description,
        location=event.location,
        start_time=event.start_time,
        end_time=event.end_time,
        attendees=event.attendees,
        detected_from_email=event.detected_from_email,
        created_at=event.created_at
    )

@router.get("/events", response_model=List[CalendarEventResponse])
async def list_calendar_events(
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List calendar events"""
    events = await db.calendar_events.find({"user_id": user.id}).sort("start_time", 1).to_list(100)
    
    return [
        CalendarEventResponse(
            id=e['id'],
            calendar_provider_id=e['calendar_provider_id'],
            title=e['title'],
            description=e.get('description'),
            location=e.get('location'),
            start_time=e['start_time'],
            end_time=e['end_time'],
            attendees=e['attendees'],
            detected_from_email=e['detected_from_email'],
            created_at=e['created_at']
        )
        for e in events
    ]

@router.get("/events/upcoming")
async def get_upcoming_events(
    hours: int = 24,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get upcoming events"""
    calendar_service = CalendarService(db)
    events = await calendar_service.get_upcoming_events(user.id, hours)
    
    return [
        CalendarEventResponse(
            id=e.id,
            calendar_provider_id=e.calendar_provider_id,
            title=e.title,
            description=e.description,
            location=e.location,
            start_time=e.start_time,
            end_time=e.end_time,
            attendees=e.attendees,
            detected_from_email=e.detected_from_email,
            created_at=e.created_at
        )
        for e in events
    ]


@router.put("/events/{event_id}", response_model=CalendarEventResponse)
async def update_calendar_event(
    event_id: str,
    event_data: CalendarEventCreate,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update calendar event"""
    # Get existing event
    event_doc = await db.calendar_events.find_one({"id": event_id, "user_id": user.id})
    if not event_doc:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get provider
    provider_doc = await db.calendar_providers.find_one({
        "id": event_doc['calendar_provider_id'],
        "user_id": user.id
    })
    
    if not provider_doc:
        raise HTTPException(status_code=404, detail="Calendar provider not found")
    
    from models.calendar import CalendarProvider
    provider = CalendarProvider(**provider_doc)
    calendar_service = CalendarService(db)
    
    # Check conflicts (excluding current event)
    conflicts = await calendar_service.check_conflicts(
        provider.id,
        event_data.start_time,
        event_data.end_time
    )
    conflicts = [c for c in conflicts if c.id != event_id]
    
    if conflicts:
        raise HTTPException(
            status_code=409,
            detail=f"Conflict with {len(conflicts)} existing event(s)"
        )
    
    # Update event in Google Calendar
    event_dict = {
        'title': event_data.title,
        'description': event_data.description,
        'location': event_data.location,
        'start_time': event_data.start_time,
        'end_time': event_data.end_time,
        'timezone': event_data.timezone,
        'attendees': event_data.attendees
    }
    
    # Update event based on provider type
    if provider.provider == 'google':
        success = await calendar_service.update_event_google(provider, event_doc['event_id'], event_dict)
    elif provider.provider == 'microsoft':
        success = await calendar_service.update_event_outlook(provider, event_doc['event_id'], event_dict)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported calendar provider: {provider.provider}")
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update event in calendar")
    
    # Update in DB
    await db.calendar_events.update_one(
        {"id": event_id},
        {"$set": {
            "title": event_data.title,
            "description": event_data.description,
            "location": event_data.location,
            "start_time": event_data.start_time,
            "end_time": event_data.end_time,
            "timezone": event_data.timezone,
            "attendees": event_data.attendees,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Get updated event
    updated_event = await db.calendar_events.find_one({"id": event_id})
    
    return CalendarEventResponse(
        id=updated_event['id'],
        calendar_provider_id=updated_event['calendar_provider_id'],
        title=updated_event['title'],
        description=updated_event.get('description'),
        location=updated_event.get('location'),
        start_time=updated_event['start_time'],
        end_time=updated_event['end_time'],
        attendees=updated_event['attendees'],
        detected_from_email=updated_event['detected_from_email'],
        created_at=updated_event['created_at']
    )

@router.delete("/events/{event_id}")
async def delete_calendar_event(
    event_id: str,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete calendar event"""
    result = await db.calendar_events.delete_one({"id": event_id, "user_id": user.id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {"message": "Event deleted successfully"}
