"""
Production Email Flow Test
Tests the complete email automation flow with REAL email sending
"""
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import time

# Test configuration
USER_EMAIL = "amits.joys@gmail.com"
TEST_SMTP_EMAIL = "sagarshinde15798796456@gmail.com"
TEST_SMTP_PASSWORD = "bmwqmytxrsgrlusp"
TARGET_EMAIL = "amits.joys@gmail.com"  # Where to send test emails

# Test email scenarios
TEST_SCENARIOS = [
    {
        "name": "Meeting Request",
        "subject": "Can we schedule a meeting next week?",
        "body": "Hi,\n\nI would like to schedule a meeting to discuss the project status. Would next Tuesday at 2 PM work for you?\n\nBest regards"
    },
    {
        "name": "Support Request",
        "subject": "Need help with login issue",
        "body": "Hi,\n\nI'm having trouble logging into my account. I keep getting an error message when I try to sign in. Can you help?\n\nThanks"
    },
    {
        "name": "General Inquiry",
        "subject": "Question about pricing plans",
        "body": "Hello,\n\nI'm interested in your service and would like to know more about your pricing plans. What features are included in each plan?\n\nRegards"
    },
    {
        "name": "Simple Acknowledgment",
        "subject": "Re: Project Update",
        "body": "Thanks for the update!"
    }
]

def send_test_email(subject: str, body: str, to_email: str) -> bool:
    """Send a test email via SMTP"""
    try:
        message = MIMEMultipart()
        message['From'] = TEST_SMTP_EMAIL
        message['To'] = to_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(TEST_SMTP_EMAIL, TEST_SMTP_PASSWORD)
        server.send_message(message)
        server.quit()
        
        print(f"   ✅ Sent: {subject}")
        return True
    except Exception as e:
        print(f"   ❌ Failed to send: {e}")
        return False

async def verify_user_and_accounts():
    """Verify user exists and has email/calendar accounts connected"""
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['email_assistant_db']
    
    # Check user
    user = await db.users.find_one({"email": USER_EMAIL})
    if not user:
        print(f"❌ User {USER_EMAIL} not found")
        client.close()
        return False, None
    
    user_id = user['id']
    print(f"✅ User found: {USER_EMAIL} (ID: {user_id})")
    
    # Check email account
    email_account = await db.email_accounts.find_one({"user_id": user_id, "is_active": True})
    if not email_account:
        print(f"❌ No active email account found for user")
        client.close()
        return False, None
    
    print(f"✅ Email account: {email_account['email']} (Type: {email_account['account_type']})")
    
    # Check calendar provider
    calendar = await db.calendar_providers.find_one({"user_id": user_id, "is_active": True})
    if calendar:
        provider_email = calendar.get('provider_email') or calendar.get('email') or 'Unknown'
        provider_type = calendar.get('provider_type') or calendar.get('type') or 'Unknown'
        print(f"✅ Calendar provider: {provider_email} (Type: {provider_type})")
    else:
        print(f"⚠️  No calendar provider connected")
    
    # Check intents
    intents = await db.intents.find({"user_id": user_id, "is_active": True}).to_list(100)
    print(f"✅ Intents loaded: {len(intents)}")
    auto_send_count = sum(1 for i in intents if i.get('auto_send', False))
    print(f"   - {auto_send_count}/{len(intents)} intents with auto_send enabled")
    
    # Check knowledge base
    kb_entries = await db.knowledge_base.find({"user_id": user_id, "is_active": True}).to_list(100)
    print(f"✅ Knowledge base entries: {len(kb_entries)}")
    
    client.close()
    return True, user_id

async def wait_for_processing(user_id: str, wait_seconds: int = 90):
    """Wait for emails to be processed and check results"""
    print(f"\n⏳ Waiting {wait_seconds} seconds for email processing...")
    
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['email_assistant_db']
    
    # Show countdown
    for i in range(wait_seconds, 0, -10):
        print(f"   {i} seconds remaining...")
        await asyncio.sleep(10)
    
    print("\n📊 Checking Results...")
    print("="*60)
    
    # Get all emails processed in this session
    emails = await db.emails.find({
        "user_id": user_id,
        "created_at": {"$gte": datetime.now().isoformat()[:10]}  # Today
    }).sort("created_at", -1).limit(10).to_list(10)
    
    print(f"\n✅ Found {len(emails)} recent emails")
    
    for i, email in enumerate(emails, 1):
        print(f"\n{i}. Email: {email.get('subject', 'No subject')}")
        print(f"   From: {email.get('from_email', 'Unknown')}")
        print(f"   Status: {email.get('status', 'unknown')}")
        print(f"   Intent: {email.get('intent_name', 'No intent')}")
        confidence = email.get('intent_confidence') or 0
        print(f"   Confidence: {confidence if isinstance(confidence, (int, float)) else 0:.2f}")
        print(f"   Auto-sent: {'Yes' if email.get('replied', False) else 'No'}")
        
        # Check for follow-ups
        follow_ups = await db.follow_ups.find({"email_id": email['id']}).to_list(100)
        if follow_ups:
            print(f"   Follow-ups: {len(follow_ups)} created")
            for fu in follow_ups:
                print(f"      - Scheduled: {fu.get('scheduled_at', 'N/A')[:10]} | Status: {fu.get('status', 'unknown')}")
        else:
            print(f"   Follow-ups: None")
        
        # Check for meeting
        if email.get('meeting_detected'):
            print(f"   Meeting detected: Yes (confidence: {email.get('meeting_confidence', 0):.2f})")
            # Check calendar events
            events = await db.calendar_events.find({"user_id": user_id}).to_list(100)
            if events:
                print(f"   Calendar events created: {len(events)}")
        else:
            print(f"   Meeting detected: No")
    
    # Summary statistics
    print("\n" + "="*60)
    print("📈 SUMMARY STATISTICS")
    print("="*60)
    
    total_emails = len(emails)
    auto_sent = sum(1 for e in emails if e.get('replied', False))
    with_intent = sum(1 for e in emails if e.get('intent_detected'))
    meetings = sum(1 for e in emails if e.get('meeting_detected'))
    
    print(f"Total emails processed: {total_emails}")
    print(f"Auto-sent replies: {auto_sent}/{total_emails} ({auto_sent/total_emails*100 if total_emails > 0 else 0:.0f}%)")
    print(f"Intent classified: {with_intent}/{total_emails} ({with_intent/total_emails*100 if total_emails > 0 else 0:.0f}%)")
    print(f"Meetings detected: {meetings}")
    
    # Follow-up statistics
    all_follow_ups = await db.follow_ups.find({"user_id": user_id}).to_list(1000)
    recent_follow_ups = [f for f in all_follow_ups if f.get('created_at', '')[:10] == datetime.now().isoformat()[:10]]
    
    print(f"\nFollow-ups created today: {len(recent_follow_ups)}")
    pending = sum(1 for f in recent_follow_ups if f.get('status') == 'pending')
    automated = sum(1 for f in recent_follow_ups if f.get('is_automated', False))
    print(f"   - Pending: {pending}")
    print(f"   - Automated (time-based): {automated}")
    print(f"   - Standard: {len(recent_follow_ups) - automated}")
    
    client.close()

async def main():
    """Run the complete production test"""
    print("="*60)
    print("🚀 PRODUCTION EMAIL FLOW TEST")
    print("="*60)
    print(f"Test sender: {TEST_SMTP_EMAIL}")
    print(f"Target: {TARGET_EMAIL}")
    print(f"User: {USER_EMAIL}")
    print("="*60)
    
    # Phase 1: Verify setup
    print("\n📋 PHASE 1: Verify Setup")
    print("-"*60)
    verified, user_id = await verify_user_and_accounts()
    if not verified:
        print("\n❌ Setup verification failed. Please ensure:")
        print("   1. User is registered and logged in")
        print("   2. Email account is connected")
        print("   3. Calendar provider is connected")
        print("   4. Intents and knowledge base are populated")
        return
    
    # Phase 2: Send test emails
    print("\n📧 PHASE 2: Send Test Emails")
    print("-"*60)
    sent_count = 0
    for scenario in TEST_SCENARIOS:
        print(f"\nSending: {scenario['name']}")
        if send_test_email(scenario['subject'], scenario['body'], TARGET_EMAIL):
            sent_count += 1
            time.sleep(2)  # Wait 2 seconds between emails
    
    print(f"\n✅ Sent {sent_count}/{len(TEST_SCENARIOS)} test emails")
    
    # Phase 3: Wait and verify
    print("\n⏳ PHASE 3: Processing & Verification")
    print("-"*60)
    await wait_for_processing(user_id, wait_seconds=90)
    
    # Final message
    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60)
    print("\n📝 Next Steps:")
    print("   1. Check your email inbox for auto-replies")
    print("   2. Verify replies are in plain text format")
    print("   3. Verify no duplicate follow-ups created")
    print("   4. Check calendar for meeting events")
    print("   5. Review database for correct intent classification")
    print("\n💡 Tips:")
    print("   - Simple acknowledgment email should have 0 follow-ups")
    print("   - Other emails should have 3 follow-ups each")
    print("   - Meeting request should create calendar event")
    print("   - All replies should be plain text (no HTML)")

if __name__ == "__main__":
    asyncio.run(main())
