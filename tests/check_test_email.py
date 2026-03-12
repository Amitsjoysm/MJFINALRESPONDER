#!/usr/bin/env python3
"""
Check the status of the test email we created
"""

import pymongo
from datetime import datetime

# Configuration
TARGET_USER_ID = "93235fa9-9071-4e00-bcde-ea9152fef14e"

def check_test_email():
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
    db = mongo_client["email_assistant_db"]
    
    print("Checking test email status...")
    
    # Find the test email
    test_email = db.emails.find_one({
        "user_id": TARGET_USER_ID,
        "subject": "Meeting Request - Project Discussion"
    })
    
    if not test_email:
        print("❌ Test email not found")
        return
    
    print(f"✅ Test email found: {test_email['id']}")
    print(f"Status: {test_email.get('status')}")
    print(f"Meeting detected: {test_email.get('meeting_detected', False)}")
    print(f"Meeting confidence: {test_email.get('meeting_confidence', 0)}")
    print(f"Intent detected: {test_email.get('intent_detected')}")
    print(f"Draft generated: {test_email.get('draft_generated', False)}")
    
    # Check action history
    action_history = test_email.get('action_history', [])
    print(f"\nAction History ({len(action_history)} actions):")
    for i, action in enumerate(action_history):
        print(f"  {i+1}. {action.get('action')} at {action.get('timestamp')}")
        if action.get('details'):
            details = str(action.get('details'))[:100]
            print(f"     Details: {details}...")
    
    # Check if there are any calendar events
    events = list(db.calendar_events.find({"user_id": TARGET_USER_ID}))
    print(f"\nCalendar events: {len(events)}")
    
    for event in events:
        print(f"  Event: {event.get('title')}")
        print(f"    Start: {event.get('start_time')}")
        print(f"    Status: {event.get('status')}")

if __name__ == "__main__":
    check_test_email()