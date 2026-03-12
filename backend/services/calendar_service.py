from typing import List, Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta
import logging
import asyncio
import uuid
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import httpx

from config import config
from models.calendar import CalendarProvider, CalendarEvent, CalendarEventCreate
from services.oauth_service import OAuthService

logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.oauth_service = OAuthService(db)
    
    async def ensure_token_valid(self, provider: CalendarProvider) -> CalendarProvider:
        """Check and refresh OAuth token if expired"""
        if not provider.token_expires_at or not provider.refresh_token:
            return provider
        
        try:
            # Parse token expiry
            from dateutil import parser
            expires_at = parser.isoparse(provider.token_expires_at)
            now = datetime.now(timezone.utc)
            
            # Check if token expires within next 5 minutes
            if expires_at <= now:
                logger.info(f"Token expired for calendar provider {provider.email}, refreshing...")
                
                # Refresh token
                new_tokens = await self.oauth_service.refresh_google_token(provider.refresh_token)
                if new_tokens:
                    # Update provider with new tokens
                    await self.db.calendar_providers.update_one(
                        {"id": provider.id},
                        {"$set": {
                            "access_token": new_tokens['access_token'],
                            "token_expires_at": new_tokens['token_expires_at'],
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    
                    # Update provider object
                    provider.access_token = new_tokens['access_token']
                    provider.token_expires_at = new_tokens['token_expires_at']
                    
                    logger.info(f"Token refreshed successfully for {provider.email}")
                else:
                    logger.error(f"Failed to refresh token for {provider.email}")
                    raise Exception("Token refresh failed")
        except Exception as e:
            logger.error(f"Error checking/refreshing token: {e}")
            raise
        
        return provider
    
    async def create_event_google(self, provider: CalendarProvider, event_data: Dict) -> Optional[str]:
        """Create calendar event in Google Calendar"""
        try:
            # Ensure token is valid
            provider = await self.ensure_token_valid(provider)
            
            creds = Credentials(
                token=provider.access_token,
                refresh_token=provider.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=config.GOOGLE_CLIENT_ID,
                client_secret=config.GOOGLE_CLIENT_SECRET
            )
            
            # Build service in thread-safe manner
            def _create_event():
                service = build('calendar', 'v3', credentials=creds)
                
                event = {
                    'summary': event_data.get('title'),
                    'description': event_data.get('description', ''),
                    'location': event_data.get('location', ''),
                    'start': {
                        'dateTime': event_data.get('start_time'),
                        'timeZone': event_data.get('timezone', 'UTC'),
                    },
                    'end': {
                        'dateTime': event_data.get('end_time'),
                        'timeZone': event_data.get('timezone', 'UTC'),
                    },
                    'attendees': [{'email': email} for email in event_data.get('attendees', [])],
                    'conferenceData': {
                        'createRequest': {
                            'requestId': str(uuid.uuid4()),
                            'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                        }
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 60},
                        ],
                    },
                }
                
                result = service.events().insert(
                    calendarId='primary', 
                    body=event,
                    conferenceDataVersion=1  # Required for Google Meet link
                ).execute()
                
                return {
                    'event_id': result.get('id'),
                    'meet_link': result.get('hangoutLink'),
                    'html_link': result.get('htmlLink'),
                    'status': result.get('status')
                }
            
            # Run synchronous Google API call in executor
            event_result = await asyncio.to_thread(_create_event)
            logger.info(f"Successfully created calendar event: {event_result['event_id']} with Meet link: {event_result.get('meet_link')}")
            return event_result
        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {e}", exc_info=True)
            return None
    
    async def update_event_google(self, provider: CalendarProvider, event_id: str, event_data: Dict) -> bool:
        """Update calendar event in Google Calendar"""
        try:
            # Ensure token is valid
            provider = await self.ensure_token_valid(provider)
            
            creds = Credentials(
                token=provider.access_token,
                refresh_token=provider.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=config.GOOGLE_CLIENT_ID,
                client_secret=config.GOOGLE_CLIENT_SECRET
            )
            
            # Build service in thread-safe manner
            def _update_event():
                service = build('calendar', 'v3', credentials=creds)
                
                event = {
                    'summary': event_data.get('title'),
                    'description': event_data.get('description', ''),
                    'location': event_data.get('location', ''),
                    'start': {
                        'dateTime': event_data.get('start_time'),
                        'timeZone': event_data.get('timezone', 'UTC'),
                    },
                    'end': {
                        'dateTime': event_data.get('end_time'),
                        'timeZone': event_data.get('timezone', 'UTC'),
                    },
                    'attendees': [{'email': email} for email in event_data.get('attendees', [])],
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 60},
                        ],
                    },
                }
                
                service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
                return True
            
            # Run synchronous Google API call in executor
            success = await asyncio.to_thread(_update_event)
            logger.info(f"Successfully updated calendar event: {event_id}")
            return success
        except Exception as e:
            logger.error(f"Error updating Google Calendar event: {e}", exc_info=True)
            return False
    
    # ==================== MICROSOFT OUTLOOK CALENDAR METHODS ====================
    
    async def ensure_token_valid_outlook(self, provider: CalendarProvider) -> CalendarProvider:
        """Check and refresh Microsoft OAuth token if expired"""
        if not provider.token_expires_at or not provider.refresh_token:
            return provider
        
        try:
            from dateutil import parser
            expires_at = parser.isoparse(provider.token_expires_at)
            now = datetime.now(timezone.utc)
            
            if expires_at <= now:
                logger.info(f"Microsoft calendar token expired for {provider.email}, refreshing...")
                
                new_tokens = await self.oauth_service.refresh_microsoft_token(provider.refresh_token)
                if new_tokens:
                    await self.db.calendar_providers.update_one(
                        {"id": provider.id},
                        {"$set": {
                            "access_token": new_tokens['access_token'],
                            "token_expires_at": new_tokens['token_expires_at'],
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    
                    provider.access_token = new_tokens['access_token']
                    provider.token_expires_at = new_tokens['token_expires_at']
                    
                    logger.info(f"Microsoft calendar token refreshed successfully for {provider.email}")
                else:
                    logger.error(f"Failed to refresh Microsoft calendar token for {provider.email}")
                    raise Exception("Microsoft token refresh failed")
        except Exception as e:
            logger.error(f"Error checking/refreshing Microsoft calendar token: {e}")
            raise
        
        return provider
    
    async def create_event_outlook(self, provider: CalendarProvider, event_data: Dict) -> Optional[Dict]:
        """Create calendar event in Outlook Calendar"""
        try:
            # Ensure token is valid
            provider = await self.ensure_token_valid_outlook(provider)
            
            import httpx
            
            headers = {
                'Authorization': f'Bearer {provider.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Build event data for Microsoft Graph API
            event = {
                'subject': event_data.get('title'),
                'body': {
                    'contentType': 'HTML',
                    'content': event_data.get('description', '')
                },
                'start': {
                    'dateTime': event_data.get('start_time'),
                    'timeZone': event_data.get('timezone', 'UTC')
                },
                'end': {
                    'dateTime': event_data.get('end_time'),
                    'timeZone': event_data.get('timezone', 'UTC')
                },
                'location': {
                    'displayName': event_data.get('location', '')
                },
                'attendees': [
                    {
                        'emailAddress': {
                            'address': email,
                            'name': email
                        },
                        'type': 'required'
                    } for email in event_data.get('attendees', [])
                ],
                'isOnlineMeeting': True,
                'onlineMeetingProvider': 'teamsForBusiness'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://graph.microsoft.com/v1.0/me/events',
                    headers=headers,
                    json=event
                )
            
            if response.status_code in [200, 201]:
                result = response.json()
                
                event_result = {
                    'event_id': result.get('id'),
                    'meet_link': result.get('onlineMeeting', {}).get('joinUrl'),
                    'html_link': result.get('webLink'),
                    'status': 'confirmed'
                }
                
                logger.info(f"Successfully created Outlook calendar event: {event_result['event_id']}")
                return event_result
            else:
                logger.error(f"Failed to create Outlook calendar event: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Outlook Calendar event: {e}", exc_info=True)
            return None
    
    async def update_event_outlook(self, provider: CalendarProvider, event_id: str, event_data: Dict) -> bool:
        """Update calendar event in Outlook Calendar"""
        try:
            # Ensure token is valid
            provider = await self.ensure_token_valid_outlook(provider)
            
            import httpx
            
            headers = {
                'Authorization': f'Bearer {provider.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Build event data for Microsoft Graph API
            event = {
                'subject': event_data.get('title'),
                'body': {
                    'contentType': 'HTML',
                    'content': event_data.get('description', '')
                },
                'start': {
                    'dateTime': event_data.get('start_time'),
                    'timeZone': event_data.get('timezone', 'UTC')
                },
                'end': {
                    'dateTime': event_data.get('end_time'),
                    'timeZone': event_data.get('timezone', 'UTC')
                },
                'location': {
                    'displayName': event_data.get('location', '')
                },
                'attendees': [
                    {
                        'emailAddress': {
                            'address': email,
                            'name': email
                        },
                        'type': 'required'
                    } for email in event_data.get('attendees', [])
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f'https://graph.microsoft.com/v1.0/me/events/{event_id}',
                    headers=headers,
                    json=event
                )
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully updated Outlook calendar event: {event_id}")
                return True
            else:
                logger.error(f"Failed to update Outlook calendar event: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating Outlook Calendar event: {e}", exc_info=True)
            return False

    
    async def check_conflicts(self, provider_id: str, start_time: str, end_time: str) -> List[CalendarEvent]:
        """Check for calendar conflicts"""
        try:
            # Get all events for this provider in the time range
            events = await self.db.calendar_events.find({
                "calendar_provider_id": provider_id,
                "$or": [
                    # New event starts during existing event
                    {"start_time": {"$lte": start_time}, "end_time": {"$gt": start_time}},
                    # New event ends during existing event
                    {"start_time": {"$lt": end_time}, "end_time": {"$gte": end_time}},
                    # New event encompasses existing event
                    {"start_time": {"$gte": start_time}, "end_time": {"$lte": end_time}}
                ]
            }).to_list(100)
            
            return [CalendarEvent(**doc) for doc in events]
        except Exception as e:
            logger.error(f"Error checking conflicts: {e}")
            return []
    
    async def save_event(self, user_id: str, provider_id: str, event_data: Dict, email_id: Optional[str] = None, thread_id: Optional[str] = None) -> CalendarEvent:
        """Save calendar event to database"""
        event = CalendarEvent(
            user_id=user_id,
            calendar_provider_id=provider_id,
            email_id=email_id,
            thread_id=thread_id,  # Store thread_id for reminder sending
            event_id=event_data.get('event_id', str(uuid.uuid4())),
            title=event_data['title'],
            description=event_data.get('description'),
            location=event_data.get('location'),
            start_time=event_data['start_time'],
            end_time=event_data['end_time'],
            timezone=event_data.get('timezone', 'UTC'),
            attendees=event_data.get('attendees', []),
            meet_link=event_data.get('meet_link'),
            html_link=event_data.get('html_link'),
            detected_from_email=event_data.get('detected_from_email', False),
            confidence=event_data.get('confidence')
        )
        
        doc = event.model_dump()
        await self.db.calendar_events.insert_one(doc)
        
        return event
    
    async def get_upcoming_events(self, user_id: str, hours: int = 24) -> List[CalendarEvent]:
        """Get upcoming events in next N hours"""
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=hours)
        
        events = await self.db.calendar_events.find({
            "user_id": user_id,
            "start_time": {
                "$gte": now.isoformat(),
                "$lte": future.isoformat()
            }
        }).to_list(100)
        
        return [CalendarEvent(**doc) for doc in events]
    
    async def send_reminder(self, event: CalendarEvent, email_service, user_id: str):
        """Send reminder for calendar event"""
        try:
            # Get user's email accounts
            accounts = await self.db.email_accounts.find({
                "user_id": user_id,
                "is_active": True
            }).limit(1).to_list(1)
            
            if not accounts:
                logger.error(f"No active email account for user {user_id}")
                return
            
            account_id = accounts[0]['id']
            
            # Create reminder email
            from models.email import EmailSend
            
            # Get account email
            account = await email_service.get_account(account_id)
            if not account:
                return
            
            reminder_email = EmailSend(
                email_account_id=account_id,
                to_email=[account.email],  # Send to self
                subject=f"Reminder: {event.title} in 1 hour",
                body=f"""Hi,

This is a reminder that you have the following meeting in 1 hour:

Title: {event.title}
Time: {event.start_time}
Location: {event.location or 'Not specified'}
Description: {event.description or 'No description'}

Best regards,
Your Email Assistant
"""
            )
            
            # Send reminder in same thread as original email if thread_id exists
            if account.account_type == 'oauth_gmail':
                result = await email_service.send_email_oauth_gmail(account, reminder_email, event.thread_id)
                sent = result.get("success", False)
            elif account.account_type == 'oauth_outlook':
                result = await email_service.send_email_oauth_outlook(account, reminder_email, event.thread_id)
                sent = result.get("success", False)
            else:
                sent = await email_service.send_email_smtp(account, reminder_email)
            
            if sent:
                # Mark reminder as sent
                await self.db.calendar_events.update_one(
                    {"id": event.id},
                    {"$set": {
                        "reminder_sent": True,
                        "reminder_sent_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                logger.info(f"Reminder sent for event {event.id}")
        except Exception as e:
            logger.error(f"Error sending reminder: {e}")

import uuid
