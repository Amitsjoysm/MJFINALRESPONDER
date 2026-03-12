#!/usr/bin/env python3
"""
Simple meeting detection test
"""

import pymongo
import uuid
from datetime import datetime, timedelta
import asyncio
import sys
sys.path.append('/app/backend')

# Configuration
TARGET_USER_ID = "93235fa9-9071-4e00-bcde-ea9152fef14e"
TARGET_EMAIL = "amits.joys@gmail.com"

def create_valid_test_email():
    """Create a properly formatted test email"""
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
    db = mongo_client["email_assistant_db"]
    
    # Get email account ID
    account = db.email_accounts.find_one({
        "user_id": TARGET_USER_ID,
        "email": TARGET_EMAIL
    })
    
    if not account:
        print("❌ No email account found")
        return None
    
    # Create properly formatted email
    test_email = {
        "id": str(uuid.uuid4()),
        "user_id": TARGET_USER_ID,
        "email_account_id": account["id"],
        "message_id": f"test-meeting-{uuid.uuid4()}@gmail.com",
        "thread_id": f"thread-{uuid.uuid4()}",
        "subject": "Meeting Request - Project Discussion",
        "from_email": "john.doe@example.com",
        "to_email": [TARGET_EMAIL],  # Must be a list
        "body": """Hi Amit,

Can we schedule a meeting tomorrow at 2pm for 30 minutes? I'd like to discuss the upcoming project requirements and timeline.

The meeting should cover:
- Project scope and deliverables  
- Timeline and milestones
- Resource allocation

Please let me know if this time works for you.

Best regards,
John Doe""",
        "received_at": datetime.now().isoformat(),
        "status": "pending",  # Valid status
        "replied": False,
        "draft_generated": False,
        "intent_detected": None,
        "meeting_detected": False,
        "action_history": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Insert email
    result = db.emails.insert_one(test_email)
    print(f"✅ Test email created: {test_email['id']}")
    print(f"   Subject: {test_email['subject']}")
    
    return test_email

async def process_test_email(email_id):
    """Process the test email"""
    try:
        from workers.email_worker import process_email
        await process_email(email_id)
        print("✅ Email processing completed")
        return True
    except Exception as e:
        print(f"❌ Email processing failed: {str(e)}")
        return False

def check_results():
    """Check the results of processing"""
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
    db = mongo_client["email_assistant_db"]
    
    # Find the test email
    email = db.emails.find_one({
        "user_id": TARGET_USER_ID,
        "subject": "Meeting Request - Project Discussion"
    })
    
    if not email:
        print("❌ Test email not found")
        return
    
    print(f"\n📧 EMAIL PROCESSING RESULTS:")
    print(f"Status: {email.get('status')}")
    print(f"Meeting detected: {email.get('meeting_detected', False)}")
    print(f"Meeting confidence: {email.get('meeting_confidence', 0)}")
    print(f"Intent detected: {email.get('intent_detected')}")
    print(f"Draft generated: {email.get('draft_generated', False)}")
    
    # Check action history
    actions = email.get('action_history', [])
    print(f"\n📋 ACTION HISTORY ({len(actions)} actions):")
    for i, action in enumerate(actions):
        print(f"  {i+1}. {action.get('action')} at {action.get('timestamp')}")
    
    # Check calendar events
    events = list(db.calendar_events.find({"user_id": TARGET_USER_ID}))
    print(f"\n📅 CALENDAR EVENTS: {len(events)}")
    for event in events:
        print(f"  - {event.get('title')} at {event.get('start_time')}")
    
    # Check if meeting was detected
    if email.get('meeting_detected'):
        print("\n✅ MEETING DETECTION: SUCCESS")
    else:
        print("\n❌ MEETING DETECTION: FAILED")
    
    # Check if calendar event was created
    if len(events) > 0:
        print("✅ CALENDAR EVENT CREATION: SUCCESS")
    else:
        print("❌ CALENDAR EVENT CREATION: FAILED")

def main():
    print("🧪 SIMPLE MEETING DETECTION TEST")
    print("=" * 50)
    
    # Clean up previous test emails
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
    db = mongo_client["email_assistant_db"]
    db.emails.delete_many({
        "user_id": TARGET_USER_ID,
        "from_email": "john.doe@example.com"
    })
    
    # Create test email
    test_email = create_valid_test_email()
    if not test_email:
        return
    
    # Process email
    print("\n🔄 PROCESSING EMAIL...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(process_test_email(test_email["id"]))
    loop.close()
    
    if not success:
        return
    
    # Check results
    print("\n📊 CHECKING RESULTS...")
    check_results()

if __name__ == "__main__":
    main()