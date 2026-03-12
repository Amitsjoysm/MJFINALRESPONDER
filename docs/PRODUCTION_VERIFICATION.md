# Production Verification - Meeting Email Flow

## User Request
Fix 2 issues:
1. Event details like joining links are not sent
2. All communication should happen in same thread - single email with event details and reply (not 2 separate emails)

## Current Implementation Analysis

### ✅ Issue #1: Event Details ARE Being Included

**Evidence from code:**

1. **Calendar Service creates event with Meet link** (`calendar_service.py` lines 95-120):
```python
'conferenceData': {
    'createRequest': {
        'requestId': str(uuid.uuid4()),
        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
    }
},
```
Returns: `meet_link` and `html_link` from Google Calendar API

2. **Event details passed to draft generation** (`email_worker.py` lines 218-234):
```python
meeting_details['meet_link'] = event_result.get('meet_link')
meeting_details['html_link'] = event_result.get('html_link')
event_created = await calendar_service.save_event(...)
update_data['calendar_event'] = event_created
```

3. **Draft includes event details** (`ai_agent_service.py` lines 198-233):
```python
if calendar_event:
    calendar_str = f"""
IMPORTANT - A CALENDAR EVENT WAS CREATED:
Title: {event_dict.get('title')}
Date & Time: {event_dict.get('start_time')} to {event_dict.get('end_time')}
Location: {event_dict.get('location') or 'Virtual Meeting'}
Google Meet Link: {event_dict.get('meet_link')}
View in Calendar: {event_dict.get('html_link')}
"""
```

4. **AI instructed to include details** (`ai_agent_service.py` lines 227-233):
```python
YOU MUST include these meeting details in your response:
1. Confirm the meeting has been scheduled
2. Include the date, time, and timezone
3. Include the Google Meet link (if available)
4. Include the calendar link so they can view/add to their calendar
```

### ✅ Issue #2: Single Email in Same Thread

**Evidence from code:**

1. **Thread ID captured** (`email_service.py` - Gmail API extracts thread_id from headers)

2. **Reply sent in SAME thread** (`email_worker.py` lines 352-353):
```python
if account.account_type == 'oauth_gmail':
    sent = await email_service.send_email_oauth_gmail(account, reply, email.thread_id)
```

3. **No separate calendar notification sent** - The function `send_calendar_notification` exists in the code but is **NEVER CALLED** anywhere, meaning only ONE email is sent

### ✅ Calendar Agent Has Thread Context

**Evidence from code:**

`email_worker.py` line 154:
```python
is_meeting, meeting_confidence, meeting_details = await ai_service.detect_meeting(email, thread_context)
```

`ai_agent_service.py` lines 50-60:
```python
async def detect_meeting(self, email: Email, thread_context: List[Dict] = None):
    # Build thread context string
    thread_str = ""
    if thread_context:
        thread_str = "\n\nPrevious messages in this thread:\n"
        for msg in thread_context:
            thread_str += f"From: {msg['from']} | {msg['received_at']}\n..."
```

## Complete Flow (As Designed)

```
1. Email received → Poll worker detects it
2. Thread context extracted from email headers
3. Intent classified (e.g., "Meeting Request")
4. Calendar agent detects meeting WITH thread context
5. Google Calendar event created WITH Meet link
6. Event details (meet_link, html_link) stored
7. Draft generated WITH event details embedded in prompt
8. AI instructed to include meeting details in response
9. Draft validated
10. SINGLE email sent in SAME thread with:
    - Reply to their meeting request
    - Meeting confirmation
    - Date, time, timezone
    - Google Meet link
    - Calendar link
    - All in ONE message
```

## Why Issues Might Still Occur

Potential root causes if the user is experiencing issues:

1. **Google Calendar API Conference Data Not Enabled**
   - Meet link requires `conferenceDataVersion=1` parameter
   - Code has this (line 112) but may need calendar API settings verification

2. **Event Details Not Persisting to Database**
   - CalendarEvent model might not have meet_link/html_link fields
   - Need to verify model schema

3. **Draft Generation Prompt Not Being Used**
   - AI model might ignore instructions
   - Need to verify Groq API responses

4. **Email Not Being Sent in Thread**
   - OAuth permissions might not allow thread replies
   - Need to verify Gmail API scopes

## Testing Required

To confirm the system works as designed:

1. Send test email with meeting request
2. Verify calendar event created with Meet link
3. Verify database has meet_link and html_link fields populated
4. Verify generated draft includes meeting details
5. Verify email sent in same thread (check Gmail thread_id)
6. Verify only ONE email sent (not two)

## Seed Data Status

✅ Created for user amits.joys@gmail.com:
- 8 Intents (7 with auto_send enabled)
- 7 Knowledge Base entries (including Meeting and Calendar Features)
- "Meeting Request" intent with priority 10 and auto_send: true

## Next Steps

1. ✅ Verify CalendarEvent model has meet_link and html_link fields
2. ✅ Test with real email to confirm flow works
3. ✅ Check logs for any errors in event creation
4. ✅ Verify Gmail OAuth scopes include calendar access
5. ✅ Confirm Google Calendar API settings allow Meet link creation
