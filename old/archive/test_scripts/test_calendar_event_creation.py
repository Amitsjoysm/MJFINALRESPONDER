"""
Test script to verify calendar event creation issue
Sends test emails and checks if calendar events are properly created
"""

import asyncio
import sys
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from config import config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from datetime import datetime, timezone

# Test email credentials provided by user
TEST_EMAIL = "rohushanshinde@gmail.com"
TEST_PASSWORD = "pajbdmcpcegppguz"
RECIPIENT_EMAIL = "amits.joys@gmail.com"

async def get_user_info():
    """Get user information"""
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    user_doc = await db.users.find_one({"email": RECIPIENT_EMAIL})
    if not user_doc:
        print(f"❌ User {RECIPIENT_EMAIL} not found")
        return None
    
    print(f"✅ Found user: {user_doc['email']} (ID: {user_doc['id']})")
    
    # Check email account
    email_account = await db.email_accounts.find_one({
        "user_id": user_doc['id'],
        "is_active": True
    })
    
    if email_account:
        print(f"✅ Email account: {email_account['email']} (Type: {email_account['account_type']})")
    else:
        print("❌ No active email account found")
    
    # Check calendar provider
    calendar_provider = await db.calendar_providers.find_one({
        "user_id": user_doc['id'],
        "is_active": True
    })
    
    if calendar_provider:
        print(f"✅ Calendar provider: {calendar_provider.get('provider', 'google')} (Email: {calendar_provider.get('email', 'N/A')})")
    else:
        print("❌ No active calendar provider found")
    
    return user_doc['id']

def send_test_email(subject, body):
    """Send test email using SMTP"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = TEST_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Send via Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(TEST_EMAIL, TEST_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Sent: {subject}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

async def check_email_processing(user_id):
    """Check if emails were processed and calendar events created"""
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    # Get recent emails
    emails = await db.emails.find({
        "user_id": user_id,
        "from_email": TEST_EMAIL
    }).sort("received_at", -1).limit(5).to_list(5)
    
    print(f"\n📧 Found {len(emails)} emails from test sender")
    
    for email in emails:
        print(f"\n" + "="*70)
        print(f"📨 Email: {email['subject']}")
        print(f"   Received: {email['received_at']}")
        print(f"   Status: {email.get('status', 'pending')}")
        print(f"   Processed: {email.get('processed', False)}")
        print(f"   Intent: {email.get('intent_name', 'N/A')} (Confidence: {email.get('intent_confidence', 'N/A')})")
        print(f"   Meeting Detected: {email.get('meeting_detected', False)} (Confidence: {email.get('meeting_confidence', 'N/A')})")
        print(f"   Draft Generated: {email.get('draft_generated', False)}")
        print(f"   Draft Validated: {email.get('draft_validated', False)}")
        print(f"   Replied: {email.get('replied', False)}")
        
        # Check if calendar event in email data
        if email.get('calendar_event'):
            print(f"   ⚠️  Calendar event in email data: {email['calendar_event'].get('title', 'N/A')}")
        
        # Check action history
        if email.get('action_history'):
            print(f"\n   📋 Action History ({len(email['action_history'])} actions):")
            for action in email['action_history'][-5:]:  # Last 5 actions
                print(f"      • {action['action']} - {action.get('status', 'N/A')}")
                if action['action'] == 'calendar_event_created':
                    print(f"        Event ID: {action['details'].get('event_id', 'N/A')}")
                    print(f"        Meet Link: {action['details'].get('meet_link', 'N/A')}")
                elif action['action'] == 'calendar_event_creation_failed':
                    print(f"        ❌ Reason: {action['details'].get('message', 'N/A')}")
    
    # Check calendar events
    events = await db.calendar_events.find({
        "user_id": user_id
    }).sort("created_at", -1).limit(5).to_list(5)
    
    print(f"\n" + "="*70)
    print(f"📅 Calendar Events: {len(events)} total events")
    
    for event in events:
        print(f"\n   • {event['title']}")
        print(f"     Start: {event['start_time']}")
        print(f"     Event ID: {event.get('event_id', 'N/A')}")
        print(f"     Meet Link: {event.get('meet_link', 'N/A')}")
        print(f"     Detected from email: {event.get('detected_from_email', False)}")
        print(f"     Email ID: {event.get('email_id', 'N/A')}")

async def main():
    print("="*70)
    print("🔬 CALENDAR EVENT CREATION TEST")
    print("="*70)
    
    # Step 1: Get user info
    print("\n📋 Step 1: Checking user and connections...")
    user_id = await get_user_info()
    if not user_id:
        return
    
    # Step 2: Send test emails
    print("\n📧 Step 2: Sending test emails...")
    print(f"From: {TEST_EMAIL}")
    print(f"To: {RECIPIENT_EMAIL}")
    
    test_emails = [
        {
            "subject": "Let's schedule a meeting next Tuesday",
            "body": "Hi,\n\nI would like to schedule a meeting with you next Tuesday at 2 PM to discuss the project.\nLooking forward to hearing from you.\n\nBest regards"
        },
        {
            "subject": "Meeting request for project discussion",
            "body": "Hello,\n\nCan we schedule a call this week? I'm available on Wednesday at 3 PM or Thursday at 10 AM.\nPlease let me know what works for you.\n\nThanks"
        }
    ]
    
    for test_email in test_emails:
        send_test_email(test_email['subject'], test_email['body'])
        time.sleep(2)  # Wait between emails
    
    # Step 3: Wait for processing
    print("\n⏳ Step 3: Waiting 90 seconds for email polling and processing...")
    await asyncio.sleep(90)
    
    # Step 4: Check results
    print("\n📊 Step 4: Checking email processing results...")
    await check_email_processing(user_id)
    
    print("\n" + "="*70)
    print("✅ Test Complete!")
    print("="*70)
    print("\n🔍 ANALYSIS:")
    print("1. If 'Meeting Detected' = True but no calendar event created:")
    print("   → Calendar creation is failing")
    print("2. If 'calendar_event' exists in email data but not in calendar_events collection:")
    print("   → Event creation API failed but data was stored in email")
    print("3. If calendar event details appear in draft even when no event created:")
    print("   → Bug in draft generation - sending event details without verification")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
