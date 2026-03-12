# Meeting Cancellation & Rescheduling Flow

**Current Implementation Status**  
**Date**: March 12, 2026

---

## 🔍 Current System Capabilities

### ✅ Implemented Features

**1. Cancellation Detection**
- Keywords: "cancel meeting", "cancel our call", "can't make it", "need to cancel", "have to cancel"
- Confidence: 0.9 when detected
- **File**: `/app/backend/services/autonomous_calendar_agent.py` (Lines 54-62)

**2. Rescheduling Detection**
- Keywords: "reschedule", "change time", "move meeting", "different time", "update meeting", "postpone", "push back"
- Confidence: 0.9 when detected
- **File**: `/app/backend/services/autonomous_calendar_agent.py` (Lines 44-52)

**3. Calendar Event Updates**
- Methods exist: `update_event_google()`, `update_event_outlook()`
- Can modify existing calendar events
- **File**: `/app/backend/services/calendar_service.py`

---

## ⚠️ Current Limitations

### Issues Found

1. **Autonomous Calendar Agent Not Integrated** ❌
   - Detection logic exists but NOT called in email worker
   - Email worker doesn't check for cancellation/rescheduling
   - Events are not automatically updated or cancelled

2. **No Delete Event Methods** ❌
   - No `delete_event_google()` or `delete_event_outlook()` methods
   - Cannot cancel events programmatically
   - Manual deletion required

3. **Draft Generation Doesn't Handle These Cases** ❌
   - No special prompts for cancellation responses
   - No special prompts for rescheduling responses
   - Generic responses instead of context-aware

---

## 📋 What SHOULD Happen (Ideal Flow)

### Scenario 1: User Cancels Meeting

**Email from User:**
```
Subject: Re: Meeting Tomorrow
Body: Sorry, I need to cancel our meeting tomorrow. Something urgent came up.
```

**Ideal System Behavior:**
1. ✅ Detect cancellation request (confidence: 0.9)
2. ✅ Find related calendar event
3. ✅ Delete/cancel the calendar event
4. ✅ Send cancellation to attendees
5. ✅ Respond with understanding and offer to reschedule

**Expected Response:**
```
Hi John,

No problem at all! I've cancelled our meeting scheduled for tomorrow. 

Would you like to reschedule for another time? Let me know what works best for you.

Best regards
```

---

### Scenario 2: User Wants to Reschedule

**Email from User:**
```
Subject: Re: Friday Meeting
Body: Can we reschedule Friday's 3 PM meeting to next Monday at the same time?
```

**Ideal System Behavior:**
1. ✅ Detect rescheduling request (confidence: 0.9)
2. ✅ Find existing calendar event (Friday 3 PM)
3. ✅ Extract new time (Monday 3 PM)
4. ✅ Update calendar event with new date/time
5. ✅ Send update to attendees
6. ✅ Confirm the change

**Expected Response:**
```
Hi Sarah,

Perfect! I've rescheduled our meeting from Friday at 3 PM to Monday at 3 PM. 

I've updated the calendar invite with the new time. The Google Meet link remains the same.

Looking forward to our discussion!

Best regards
```

---

### Scenario 3: User Proposes Different Time (Without Specific Event Reference)

**Email from User:**
```
Subject: Re: Meeting Request
Body: Actually, can we do Thursday instead of Wednesday?
```

**Ideal System Behavior:**
1. ✅ Check thread context for mentioned meeting
2. ✅ Find Wednesday meeting in thread
3. ✅ Detect reschedule request
4. ✅ Ask for specific time on Thursday
5. ✅ Wait for confirmation before updating

**Expected Response:**
```
Hi Mike,

Sure! What time on Thursday would work best for you? Our Wednesday meeting was at 2 PM - would the same time work, or would you prefer a different time?

Let me know and I'll update the calendar invite.

Best regards
```

---

## 🔧 What Needs to Be Implemented

### Priority 1: Integration (HIGH PRIORITY) 🔴

**Task**: Integrate `AutonomousCalendarAgent` into email worker

**Changes Needed:**
1. Import and initialize `AutonomousCalendarAgent` in email worker
2. Call `detect_calendar_action()` for each email
3. Handle detected actions before draft generation

**File**: `/app/backend/workers/email_worker.py`

**Pseudocode:**
```python
# In process_email function, after intent classification

# Check for calendar actions
calendar_agent = AutonomousCalendarAgent(db)
calendar_action = await calendar_agent.detect_calendar_action(
    email.body,
    email.subject
)

if calendar_action['action'] == 'cancel':
    # Handle cancellation
    await handle_meeting_cancellation(email, calendar_action)
    
elif calendar_action['action'] == 'reschedule':
    # Handle rescheduling
    await handle_meeting_reschedule(email, calendar_action)
```

---

### Priority 2: Delete Event Methods (HIGH PRIORITY) 🔴

**Task**: Implement event deletion for Google and Outlook

**File**: `/app/backend/services/calendar_service.py`

**Methods to Add:**

```python
async def delete_event_google(
    self, 
    provider: CalendarProvider, 
    event_id: str
) -> bool:
    """Delete/cancel event from Google Calendar"""
    try:
        provider = await self.ensure_token_valid(provider)
        
        def _delete_event():
            service = build('calendar', 'v3', credentials=creds)
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
        
        await asyncio.to_thread(_delete_event)
        logger.info(f"Deleted Google Calendar event: {event_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting Google Calendar event: {e}")
        return False


async def delete_event_outlook(
    self,
    provider: CalendarProvider,
    event_id: str
) -> bool:
    """Delete/cancel event from Outlook Calendar"""
    try:
        provider = await self.ensure_token_valid_outlook(provider)
        
        headers = {
            'Authorization': f'Bearer {provider.access_token}'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f'https://graph.microsoft.com/v1.0/me/events/{event_id}',
                headers=headers
            )
        
        if response.status_code == 204:
            logger.info(f"Deleted Outlook Calendar event: {event_id}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error deleting Outlook Calendar event: {e}")
        return False
```

---

### Priority 3: Enhanced Draft Prompts (MEDIUM PRIORITY) 🟡

**Task**: Add special handling for cancellation/rescheduling in draft generation

**File**: `/app/backend/services/ai_agent_service.py`

**Add to draft generation:**

```python
# In generate_draft function

# Add cancellation handling
if calendar_action and calendar_action.get('action') == 'cancel':
    prompt += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 MEETING CANCELLATION REQUEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User requested to cancel the meeting.
Calendar event has been cancelled.

YOUR RESPONSE SHOULD:
1. Acknowledge the cancellation graciously
2. Express understanding (no judgment)
3. Confirm the meeting has been cancelled
4. Offer to reschedule: "Would you like to reschedule for another time?"
5. Keep tone warm and supportive
6. Keep brief (80-120 words)

Example:
"Hi [Name],

No problem at all! I've cancelled our meeting scheduled for [date/time].

If you'd like to reschedule, just let me know what time works better for you, and I'll send a new invite.

Looking forward to connecting when it's convenient!

Best regards"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# Add rescheduling handling
elif calendar_action and calendar_action.get('action') == 'reschedule':
    new_time = calendar_action.get('details', {}).get('new_time')
    
    if new_time:
        prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 MEETING RESCHEDULE REQUEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User wants to reschedule to: {new_time}
Calendar event has been updated.

YOUR RESPONSE SHOULD:
1. Confirm the reschedule positively
2. State OLD time → NEW time clearly
3. Mention calendar updated
4. Confirm Meet link stays the same
5. Keep enthusiastic tone
6. Keep brief (100-130 words)

Example:
"Hi [Name],

Perfect! I've rescheduled our meeting from [old time] to {new_time}.

The calendar invite has been updated with the new time. The Google Meet link remains the same, so you can use the existing invite.

Looking forward to our discussion!

Best regards"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    else:
        prompt += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 MEETING RESCHEDULE REQUEST - TIME NEEDED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User wants to reschedule but didn't specify new time.

YOUR RESPONSE SHOULD:
1. Acknowledge reschedule request
2. Ask for new preferred date/time
3. Optionally suggest 2 time options
4. Keep helpful and accommodating tone
5. Keep brief (90-120 words)

Example:
"Hi [Name],

I'd be happy to reschedule our meeting!

Would either of these times work better for you?
• [Option 1]
• [Option 2]

Or please let me know what date and time would be most convenient, and I'll update the calendar invite.

Looking forward to connecting!

Best regards"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
```

---

### Priority 4: Find Related Event (MEDIUM PRIORITY) 🟡

**Task**: Match cancellation/reschedule request to existing calendar event

**Logic Needed:**
1. Check thread context for previous meeting discussions
2. Search calendar events by:
   - Date mentioned in email
   - Subject similarity
   - Attendees (sender email)
3. Return matching event(s)

**Function:**
```python
async def find_related_event(
    user_id: str,
    email: Email,
    thread_context: List[Dict]
) -> Optional[Dict]:
    """Find calendar event related to this email"""
    
    # Strategy 1: Check thread for event ID
    # Strategy 2: Match by date mentioned
    # Strategy 3: Match by sender email
    # Strategy 4: Match by subject keywords
    
    # Return best match or None
```

---

## 📊 Complete Flow Diagrams

### Cancellation Flow

```
User sends: "Need to cancel our meeting tomorrow"
    ↓
Email Worker receives email
    ↓
Autonomous Calendar Agent detects: action="cancel", confidence=0.9
    ↓
Find related calendar event (tomorrow's meeting)
    ↓
IF event found:
    → Delete event from Google/Outlook Calendar
    → Mark event as "cancelled" in database
    → Generate draft with cancellation acknowledgment
    → Send response offering to reschedule
ELSE:
    → Generate draft asking for clarification
    → "Which meeting did you want to cancel?"
```

---

### Rescheduling Flow

```
User sends: "Can we move Friday's meeting to Monday at 2 PM?"
    ↓
Email Worker receives email
    ↓
Autonomous Calendar Agent detects: action="reschedule", confidence=0.9
    ↓
Extract: old_time="Friday", new_time="Monday 2 PM"
    ↓
Find related calendar event (Friday's meeting)
    ↓
IF event found AND new_time clear:
    → Update event in Google/Outlook Calendar
    → Update event in database
    → Generate draft confirming reschedule
    → Send response with updated details
ELSE IF event found BUT new_time unclear:
    → Generate draft asking for specific time
    → Wait for confirmation
ELSE:
    → Generate draft asking for clarification
    → "Which meeting would you like to reschedule?"
```

---

## 🚀 Implementation Plan

### Phase 1: Basic Integration (2-3 hours)
1. ✅ Integrate `AutonomousCalendarAgent` into email worker
2. ✅ Detect cancellation/reschedule requests
3. ✅ Add special draft prompts for these cases
4. ✅ Test with mock scenarios

### Phase 2: Event Management (3-4 hours)
1. ✅ Implement `delete_event_google()` and `delete_event_outlook()`
2. ✅ Implement event finding logic
3. ✅ Connect detection → action → response
4. ✅ Test with real calendar events

### Phase 3: Refinement (1-2 hours)
1. ✅ Handle edge cases (multiple events, unclear requests)
2. ✅ Improve event matching accuracy
3. ✅ Add confirmation flow for ambiguous requests
4. ✅ Test end-to-end scenarios

---

## ✅ Summary

**Current State:**
- ✅ Detection logic exists (unused)
- ✅ Update methods exist
- ❌ Delete methods missing
- ❌ Integration missing
- ❌ Special prompts missing

**What Works:**
- Keyword detection for cancel/reschedule
- Calendar event creation
- Calendar event updates

**What Doesn't Work:**
- Automatic cancellation
- Automatic rescheduling
- Context-aware responses
- Event deletion

**To Make It Work:**
1. Add delete event methods (30 min)
2. Integrate calendar agent into email worker (1 hour)
3. Add cancellation/reschedule prompts (30 min)
4. Test and refine (1 hour)

**Total Effort: ~3 hours**

---

**Would you like me to implement these features now?**

I can:
1. ✅ Add delete event methods
2. ✅ Integrate autonomous calendar agent
3. ✅ Add special draft prompts
4. ✅ Test the complete flow

This will enable automatic meeting cancellation and rescheduling with context-aware responses!
