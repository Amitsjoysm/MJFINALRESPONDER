"""
Autonomous Calendar Agent Service
Intelligently handles all calendar operations with timezone awareness and availability checking
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pytz
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

class AutonomousCalendarAgent:
    """
    Autonomous Calendar Agent that handles all calendar-related requests
    - Timezone-aware scheduling (preserves user's intended time)
    - Availability checking
    - Conflict detection
    - Rescheduling
    - Cancellation
    - Smart outlier case handling
    """
    
    def __init__(self, db):
        self.db = db
    
    async def detect_calendar_action(
        self,
        email_content: str,
        subject: str
    ) -> Dict[str, Any]:
        """
        Detect what calendar action is being requested
        
        Returns:
            {
                "action": "schedule" | "reschedule" | "cancel" | "check_availability" | "none",
                "confidence": 0.0-1.0,
                "details": {...}
            }
        """
        content_lower = (subject + " " + email_content).lower()
        
        # Reschedule detection
        reschedule_keywords = ['reschedule', 'change time', 'move meeting', 'different time', 
                               'change meeting', 'update meeting', 'postpone', 'push back']
        if any(kw in content_lower for kw in reschedule_keywords):
            return {
                "action": "reschedule",
                "confidence": 0.9,
                "details": {"keywords_matched": [kw for kw in reschedule_keywords if kw in content_lower]}
            }
        
        # Cancellation detection
        cancel_keywords = ['cancel meeting', 'cancel our call', 'can\'t make it', 'need to cancel',
                          'have to cancel', 'cancel appointment', 'won\'t be able to']
        if any(kw in content_lower for kw in cancel_keywords):
            return {
                "action": "cancel",
                "confidence": 0.9,
                "details": {"keywords_matched": [kw for kw in cancel_keywords if kw in content_lower]}
            }
        
        # Availability check
        availability_keywords = ['available', 'free on', 'open on', 'when can', 'what time works']
        if any(kw in content_lower for kw in availability_keywords):
            return {
                "action": "check_availability",
                "confidence": 0.8,
                "details": {"keywords_matched": [kw for kw in availability_keywords if kw in content_lower]}
            }
        
        # Schedule new meeting
        schedule_keywords = ['schedule', 'meeting', 'call', 'zoom', 'meet', 'discuss']
        if any(kw in content_lower for kw in schedule_keywords):
            return {
                "action": "schedule",
                "confidence": 0.7,
                "details": {"keywords_matched": [kw for kw in schedule_keywords if kw in content_lower]}
            }
        
        return {"action": "none", "confidence": 0.0, "details": {}}
    
    async def check_availability(
        self,
        user_id: str,
        requested_time: datetime,
        duration_minutes: int = 60
    ) -> Tuple[bool, List[str]]:
        """
        Check if user is available at the requested time
        
        Returns:
            Tuple of (is_available, conflicts)
        """
        try:
            # Get user's timezone and working hours
            user = await self.db.users.find_one({"id": user_id})
            if not user:
                return True, []  # Default to available if no user found
            
            user_tz = user.get('timezone', 'UTC')
            working_start = user.get('working_hours_start', '09:00')
            working_end = user.get('working_hours_end', '17:00')
            working_days = user.get('working_days', [1, 2, 3, 4, 5])  # Mon-Fri
            
            # Convert requested time to user's timezone
            user_timezone = ZoneInfo(user_tz)
            local_time = requested_time.astimezone(user_timezone)
            
            conflicts = []
            
            # Check if within working hours
            time_str = local_time.strftime('%H:%M')
            if time_str < working_start or time_str > working_end:
                conflicts.append(f"Outside working hours ({working_start}-{working_end} {user_tz})")
            
            # Check if working day
            weekday = local_time.isoweekday()  # 1=Monday, 7=Sunday
            if weekday not in working_days:
                day_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 
                           5: "Friday", 6: "Saturday", 7: "Sunday"}
                conflicts.append(f"Not a working day ({day_names.get(weekday, 'Unknown')})")
            
            # Check for existing calendar events (conflicts)
            end_time = requested_time + timedelta(minutes=duration_minutes)
            
            existing_events = await self.db.calendar_events.find({
                "user_id": user_id,
                "start_time": {
                    "$lt": end_time.isoformat(),
                    "$gt": (requested_time - timedelta(hours=1)).isoformat()
                }
            }).to_list(100)
            
            if existing_events:
                for event in existing_events:
                    event_start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                    event_end = datetime.fromisoformat(event['end_time'].replace('Z', '+00:00'))
                    
                    # Check for overlap
                    if (requested_time < event_end and end_time > event_start):
                        conflicts.append(f"Conflicts with: {event.get('title', 'Existing event')}")
            
            is_available = len(conflicts) == 0
            
            return is_available, conflicts
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return True, []  # Default to available on error
    
    async def parse_time_with_timezone(
        self,
        time_string: str,
        user_id: str,
        reference_date: Optional[datetime] = None
    ) -> Tuple[datetime, str]:
        """
        Parse time string and convert to UTC while preserving user's intent
        
        Args:
            time_string: e.g., "Tuesday 2 PM", "tomorrow at 3pm EST"
            user_id: User ID to get timezone preference
            reference_date: Reference date for relative times
            
        Returns:
            Tuple of (utc_datetime, user_timezone_str)
        """
        try:
            # Get user's timezone preference
            user = await self.db.users.find_one({"id": user_id})
            user_tz_str = user.get('timezone', 'UTC') if user else 'UTC'
            user_tz = ZoneInfo(user_tz_str)
            
            # Import date parser
            from services.date_parser_service import DateParserService
            date_parser = DateParserService()
            
            # Parse the time string
            parsed_time = date_parser.parse_date_reference(time_string, reference_date)
            
            if not parsed_time:
                return None, user_tz_str
            
            # If parsed_time is naive (no timezone), assume it's in user's timezone
            if parsed_time.tzinfo is None:
                # Create datetime in user's timezone
                local_time = parsed_time.replace(tzinfo=user_tz)
            else:
                # Already has timezone, convert to user's timezone first to verify
                local_time = parsed_time.astimezone(user_tz)
            
            # Convert to UTC for storage (but preserve the user's intended time)
            utc_time = local_time.astimezone(ZoneInfo('UTC'))
            
            logger.info(f"Time parsing: '{time_string}' → {local_time.strftime('%Y-%m-%d %H:%M %Z')} → UTC: {utc_time.isoformat()}")
            
            return utc_time, user_tz_str
            
        except Exception as e:
            logger.error(f"Error parsing time with timezone: {e}")
            return None, "UTC"
    
    async def create_event_with_availability_check(
        self,
        user_id: str,
        event_details: Dict[str, Any],
        skip_availability_check: bool = False
    ) -> Dict[str, Any]:
        """
        Create calendar event with availability checking
        
        Returns:
            {
                "success": bool,
                "event_id": str,
                "conflicts": List[str],
                "warnings": List[str],
                "event": {...}
            }
        """
        try:
            title = event_details.get('title', 'Meeting')
            start_time_str = event_details.get('start_time')
            duration = event_details.get('duration', 60)
            attendees = event_details.get('attendees', [])
            
            # Parse time with timezone awareness
            if isinstance(start_time_str, str):
                start_time, user_tz = await self.parse_time_with_timezone(
                    start_time_str,
                    user_id
                )
            else:
                start_time = start_time_str
                user = await self.db.users.find_one({"id": user_id})
                user_tz = user.get('timezone', 'UTC') if user else 'UTC'
            
            if not start_time:
                return {
                    "success": False,
                    "error": "Could not parse meeting time",
                    "conflicts": [],
                    "warnings": ["Time parsing failed"]
                }
            
            # Check availability
            conflicts = []
            warnings = []
            
            if not skip_availability_check:
                is_available, conflicts = await self.check_availability(
                    user_id,
                    start_time,
                    duration
                )
                
                if conflicts:
                    warnings.extend(conflicts)
            
            # Create event even if conflicts exist (but warn user)
            import uuid
            event_id = str(uuid.uuid4())
            
            end_time = start_time + timedelta(minutes=duration)
            
            event = {
                "id": event_id,
                "user_id": user_id,
                "title": title,
                "description": event_details.get('description', ''),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "timezone": user_tz,
                "duration_minutes": duration,
                "attendees": attendees,
                "meet_link": f"https://meet.google.com/test-{uuid.uuid4().hex[:8]}",
                "status": "confirmed",
                "created_at": datetime.now(datetime.timezone.utc).isoformat()
            }
            
            # Store in database
            await self.db.calendar_events.insert_one(event)
            
            return {
                "success": True,
                "event_id": event_id,
                "conflicts": conflicts,
                "warnings": warnings,
                "event": event
            }
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return {
                "success": False,
                "error": str(e),
                "conflicts": [],
                "warnings": []
            }
    
    async def reschedule_event(
        self,
        user_id: str,
        event_id: str,
        new_time: datetime,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reschedule an existing event
        """
        try:
            # Get existing event
            event = await self.db.calendar_events.find_one({
                "id": event_id,
                "user_id": user_id
            })
            
            if not event:
                return {"success": False, "error": "Event not found"}
            
            old_start = event['start_time']
            
            # Check availability at new time
            duration = event.get('duration_minutes', 60)
            is_available, conflicts = await self.check_availability(
                user_id,
                new_time,
                duration
            )
            
            # Update event
            end_time = new_time + timedelta(minutes=duration)
            
            await self.db.calendar_events.update_one(
                {"id": event_id},
                {"$set": {
                    "start_time": new_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "updated_at": datetime.now(datetime.timezone.utc).isoformat(),
                    "reschedule_reason": reason
                }}
            )
            
            logger.info(f"Event {event_id} rescheduled: {old_start} → {new_time.isoformat()}")
            
            return {
                "success": True,
                "event_id": event_id,
                "old_time": old_start,
                "new_time": new_time.isoformat(),
                "conflicts": conflicts,
                "warnings": conflicts
            }
            
        except Exception as e:
            logger.error(f"Error rescheduling event: {e}")
            return {"success": False, "error": str(e)}
    
    async def cancel_event(
        self,
        user_id: str,
        event_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel a calendar event
        """
        try:
            # Update event status
            result = await self.db.calendar_events.update_one(
                {"id": event_id, "user_id": user_id},
                {"$set": {
                    "status": "cancelled",
                    "cancelled_at": datetime.now(datetime.timezone.utc).isoformat(),
                    "cancellation_reason": reason or "Cancelled by request"
                }}
            )
            
            if result.modified_count == 0:
                return {"success": False, "error": "Event not found"}
            
            logger.info(f"Event {event_id} cancelled: {reason}")
            
            return {
                "success": True,
                "event_id": event_id,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error cancelling event: {e}")
            return {"success": False, "error": str(e)}
    
    async def find_event_from_context(
        self,
        user_id: str,
        thread_id: Optional[str] = None,
        attendee_email: Optional[str] = None,
        recent_days: int = 14
    ) -> Optional[Dict]:
        """
        Find relevant calendar event from context (thread or attendee)
        """
        try:
            query = {
                "user_id": user_id,
                "status": {"$ne": "cancelled"}
            }
            
            # If we have thread_id, look for events in this thread
            if thread_id:
                query["thread_id"] = thread_id
            elif attendee_email:
                query["attendees"] = attendee_email
            
            # Find recent events (within last 14 days or future)
            cutoff = datetime.now(datetime.timezone.utc) - timedelta(days=recent_days)
            query["start_time"] = {"$gte": cutoff.isoformat()}
            
            events = await self.db.calendar_events.find(query).sort("start_time", -1).to_list(10)
            
            if events:
                return events[0]  # Return most recent
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding event from context: {e}")
            return None
    
    async def suggest_alternative_times(
        self,
        user_id: str,
        requested_time: datetime,
        duration_minutes: int = 60,
        num_suggestions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Suggest alternative times if requested time has conflicts
        """
        try:
            user = await self.db.users.find_one({"id": user_id})
            user_tz_str = user.get('timezone', 'UTC') if user else 'UTC'
            user_tz = ZoneInfo(user_tz_str)
            
            suggestions = []
            current_check = requested_time
            
            # Try next 7 days
            for day_offset in range(7):
                check_date = requested_time + timedelta(days=day_offset)
                
                # Try different times: same time, +1hr, +2hr, -1hr
                for hour_offset in [0, 1, 2, -1]:
                    check_time = check_date + timedelta(hours=hour_offset)
                    
                    is_available, conflicts = await self.check_availability(
                        user_id,
                        check_time,
                        duration_minutes
                    )
                    
                    if is_available:
                        # Convert to user's timezone for display
                        local_time = check_time.astimezone(user_tz)
                        
                        suggestions.append({
                            "time_utc": check_time.isoformat(),
                            "time_local": local_time.strftime('%A, %B %d at %I:%M %p %Z'),
                            "timezone": user_tz_str,
                            "available": True
                        })
                        
                        if len(suggestions) >= num_suggestions:
                            return suggestions
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting alternative times: {e}")
            return []
    
    async def process_calendar_request(
        self,
        user_id: str,
        email_content: str,
        subject: str,
        from_email: str,
        thread_id: Optional[str] = None,
        meeting_details: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        MAIN AUTONOMOUS PROCESSOR for calendar requests
        
        Handles all calendar actions automatically:
        - Schedule new events
        - Reschedule existing events
        - Cancel events
        - Check availability
        - Suggest alternatives
        
        Returns complete result with actions taken
        """
        try:
            # Detect what calendar action is requested
            action_result = await self.detect_calendar_action(email_content, subject)
            action = action_result['action']
            
            logger.info(f"Calendar action detected: {action} (confidence: {action_result['confidence']:.2f})")
            
            result = {
                "action_detected": action,
                "confidence": action_result['confidence'],
                "success": False
            }
            
            if action == "schedule":
                # Create new event
                if meeting_details:
                    event_result = await self.create_event_with_availability_check(
                        user_id,
                        meeting_details
                    )
                    result.update(event_result)
                    
                    # If conflicts, suggest alternatives
                    if event_result.get('conflicts'):
                        start_time_str = meeting_details.get('start_time')
                        if isinstance(start_time_str, str):
                            start_time, _ = await self.parse_time_with_timezone(start_time_str, user_id)
                            if start_time:
                                alternatives = await self.suggest_alternative_times(
                                    user_id,
                                    start_time,
                                    meeting_details.get('duration', 60)
                                )
                                result['alternative_times'] = alternatives
                
            elif action == "reschedule":
                # Find existing event
                event = await self.find_event_from_context(
                    user_id,
                    thread_id,
                    from_email
                )
                
                if event and meeting_details:
                    # Parse new time
                    new_time_str = meeting_details.get('start_time')
                    if new_time_str:
                        new_time, _ = await self.parse_time_with_timezone(new_time_str, user_id)
                        
                        if new_time:
                            reschedule_result = await self.reschedule_event(
                                user_id,
                                event['id'],
                                new_time,
                                reason="Requested by attendee"
                            )
                            result.update(reschedule_result)
                else:
                    result['error'] = "No existing event found to reschedule"
            
            elif action == "cancel":
                # Find and cancel event
                event = await self.find_event_from_context(
                    user_id,
                    thread_id,
                    from_email
                )
                
                if event:
                    cancel_result = await self.cancel_event(
                        user_id,
                        event['id'],
                        reason="Cancelled by request"
                    )
                    result.update(cancel_result)
                else:
                    result['error'] = "No event found to cancel"
            
            elif action == "check_availability":
                # Check availability and suggest times
                if meeting_details:
                    start_time_str = meeting_details.get('start_time')
                    if start_time_str:
                        start_time, _ = await self.parse_time_with_timezone(start_time_str, user_id)
                        
                        if start_time:
                            is_available, conflicts = await self.check_availability(
                                user_id,
                                start_time,
                                meeting_details.get('duration', 60)
                            )
                            
                            result['success'] = True
                            result['available'] = is_available
                            result['conflicts'] = conflicts
                            
                            if not is_available:
                                alternatives = await self.suggest_alternative_times(
                                    user_id,
                                    start_time,
                                    meeting_details.get('duration', 60)
                                )
                                result['alternative_times'] = alternatives
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing calendar request: {e}")
            return {
                "action_detected": "none",
                "success": False,
                "error": str(e)
            }
