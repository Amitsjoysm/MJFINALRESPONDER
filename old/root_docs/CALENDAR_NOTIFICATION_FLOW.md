# Calendar Agent Email Notification - Technical Flow

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Email Received                              │
│                     (with meeting request)                           │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Email Worker Processing                         │
│                  (run_email_worker.py → process_email)              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AI Meeting Detection                              │
│            (AIAgentService.detect_meeting + Groq API)               │
│                                                                      │
│  • Analyzes email content for meeting keywords                      │
│  • Extracts: title, start_time, end_time, duration                 │
│  • Returns confidence score (0.0 - 1.0)                            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
                        ┌───────────────┐
                        │ Confidence    │
                        │ >= 0.8 (80%)? │
                        └───────┬───────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                   YES                     NO
                    │                       │
                    ▼                       ▼
┌──────────────────────────────┐   ┌────────────────────────┐
│   Create Calendar Event      │   │ Generate draft asking  │
│   (CalendarService)          │   │ for time confirmation  │
│                              │   └────────────────────────┘
│ 1. Get user's calendar       │
│    provider (Google/Outlook) │
│ 2. Check for conflicts       │
│ 3. Create event via API      │
│ 4. Store in database        │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────────┐
│            🆕 SEND CALENDAR NOTIFICATION EMAIL                        │
│              (send_calendar_notification function)                    │
│                                                                       │
│  ** THIS WAS THE MISSING PIECE - NOW ADDED! **                      │
│                                                                       │
│  Sends email with:                                                   │
│  • Event title                                                       │
│  • Start/end time                                                    │
│  • Location                                                          │
│  • Attendees                                                         │
│  • Google Meet/Teams link                                           │
│  • Conflict warnings (if any)                                        │
│  • Reminder information                                              │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Email Sent to User │
                    │   with Event Details │
                    └──────────────────────┘
```

## Code Flow - Before vs After

### ❌ BEFORE (Not Working)

```python
# In email_worker.py, process_email function (around line 475-527)

if is_meeting and meeting_confidence >= 0.8 and meeting_details:
    # ... calendar provider setup ...
    
    # Create event in Google Calendar/Outlook
    event_result = await calendar_service.create_event_google(provider, meeting_details)
    
    if event_result and event_result.get('event_id'):
        # Save event to database
        event_created = await calendar_service.save_event(...)
        
        # Log success
        logger.info(f"Created calendar event...")
        
        # ❌ MISSING: No notification email sent!
        # ❌ User never receives event details via email!
        
        # Update lead if applicable...
```

### ✅ AFTER (Fixed - Working)

```python
# In email_worker.py, process_email function (around line 475-533)

if is_meeting and meeting_confidence >= 0.8 and meeting_details:
    # ... calendar provider setup ...
    
    # Create event in Google Calendar/Outlook
    event_result = await calendar_service.create_event_google(provider, meeting_details)
    
    if event_result and event_result.get('event_id'):
        # Save event to database
        event_created = await calendar_service.save_event(...)
        
        # Log success
        logger.info(f"Created calendar event...")
        
        # ✅ NEW: Send notification email with event details
        await send_calendar_notification(
            email,
            event_created,
            email_service,
            has_conflict=has_conflict,
            conflict_details=conflict_details
        )
        logger.info(f"Sent calendar notification email for event {event_result['event_id']}")
        
        # Update lead if applicable...
```

## Notification Email Template

```
From: user@yourdomain.com
To: customer@company.com
Subject: Calendar Event Created: [Event Title]
Thread: [Same thread as original email]

A calendar event has been created based on your email:

Event Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: Product Demo Call
Start: 2026-01-15T14:00:00Z
End: 2026-01-15T15:00:00Z
Location: Google Meet
Description: Discuss product features and pricing
Attendees: customer@company.com, sales@yourdomain.com
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[If conflicts detected]
⚠️  SCHEDULING CONFLICT DETECTED  ⚠️

The following existing event(s) conflict with this meeting:
• Team Standup
  Time: 2026-01-15T14:00:00Z to 2026-01-15T14:30:00Z

Please review and reschedule if needed.

This event has been added to your calendar. You will receive a reminder 1 hour before the meeting.

Best regards,
Your AI Email Assistant
```

## Integration Points

### 1. Calendar Service Integration
```python
class CalendarService:
    async def create_event_google(provider, event_data) → event_result
    async def create_event_outlook(provider, event_data) → event_result
    async def save_event(user_id, provider_id, event_data) → CalendarEvent
```

### 2. Email Service Integration
```python
class EmailService:
    async def send_email_oauth_gmail(account, email, thread_id) → result
    async def send_email_oauth_outlook(account, email, thread_id) → result
    async def send_email_smtp(account, email) → bool
```

### 3. AI Service Integration
```python
class AIAgentService:
    async def detect_meeting(email, thread_context) → (is_meeting, confidence, details)
```

## Configuration Requirements

### Environment Variables
```bash
GROQ_API_KEY=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
MONGO_URL=mongodb://localhost:27017
```

### User Settings Required
- Email account with OAuth connected (Google/Outlook)
- Calendar provider configured
- Active email account (is_active=true)

### Intent Configuration
- Intent must have `auto_send=true` for automatic notification
- Meeting confidence threshold: ≥ 0.8 (80%)

## Testing Scenarios

### Test Case 1: Simple Meeting Request
```
Input Email:
"Can we schedule a call tomorrow at 2 PM to discuss the project?"

Expected Output:
✅ Meeting detected (confidence: 0.85)
✅ Calendar event created
✅ Notification email sent with event details
```

### Test Case 2: Meeting with Conflict
```
Input Email:
"Let's meet on Tuesday at 2 PM"

Existing Event: "Team Meeting" at Tuesday 2 PM

Expected Output:
✅ Meeting detected (confidence: 0.82)
✅ Calendar event created
✅ Notification email sent WITH conflict warning
```

### Test Case 3: Vague Meeting Request
```
Input Email:
"Can we meet sometime next week?"

Expected Output:
✅ Meeting detected (confidence: 0.45)
❌ Calendar event NOT created (confidence too low)
✅ Draft generated asking for specific time
```

## Monitoring & Debugging

### Worker Logs
```bash
# Watch email worker processing
tail -f /var/log/email_worker.log | grep -E "(Meeting detected|calendar|notification)"

# Expected log entries:
# - "Meeting detected with HIGH confidence"
# - "Created calendar event for email"
# - "Sent calendar notification email for event"
```

### Action History in Database
```javascript
// In MongoDB emails collection, check action_history:
{
  "action_history": [
    {
      "action": "meeting_detection",
      "details": {
        "detected": true,
        "confidence": 0.85,
        "will_create_event": true
      }
    },
    {
      "action": "calendar_event_created",
      "details": {
        "event_id": "abc123",
        "meet_link": "https://meet.google.com/xyz"
      }
    },
    {
      "action": "calendar_notification_sent",  // 🆕 NEW!
      "details": {
        "event_id": "abc123",
        "event_title": "Product Demo"
      }
    }
  ]
}
```

### Health Checks
```bash
# Check Redis
redis-cli ping  # Should return PONG

# Check workers
ps aux | grep run_email_worker  # Should show running process

# Check backend
curl http://localhost:8001/api/health  # Should return healthy

# Check Groq API key
grep GROQ_API_KEY /app/backend/.env  # Should show new key
```

## Performance Considerations

- Notification emails are sent asynchronously (non-blocking)
- If notification fails, calendar event is still created
- Errors are logged but don't stop email processing
- Notification sending happens before lead updates

## Error Handling

```python
async def send_calendar_notification(...):
    try:
        # Build notification email
        # Send via appropriate service
        # Log success
    except Exception as e:
        logger.error(f"Error sending calendar notification: {e}")
        # Error logged but not raised - processing continues
```

## Rollback Plan (If Needed)

To revert the changes:
```python
# Remove these lines from email_worker.py (around line 504-512):
# await send_calendar_notification(...)
# logger.info(f"Sent calendar notification email...")
```

## Success Criteria

✅ Meeting detected from email
✅ Calendar event created in provider
✅ Event saved to database
✅ **Notification email sent automatically** (NEW!)
✅ Email includes all event details
✅ Conflicts are flagged if present
✅ Email sent in same thread as original
✅ No errors in worker logs

---

**Status**: ✅ Implementation Complete
**Deployment**: January 6, 2026
**Version**: 1.1.0 (Calendar Notifications)
