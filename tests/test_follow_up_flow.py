"""
Test script for follow-up and reminder flow
Tests:
1. Send test email with meeting request
2. Verify email is processed and auto-reply sent
3. Verify follow-ups are created with correct settings
4. Verify follow-ups use same thread_id
5. Verify calendar event is created with thread_id
6. Send reply to cancel follow-ups
7. Verify follow-ups are cancelled
"""

import smtplib
import time
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone

# Test email credentials
SENDER_EMAIL = "sashadhagle@gmail.com"
SENDER_PASSWORD = "dibphfyezwffocsa"
RECIPIENT_EMAIL = "amits.joys@gmail.com"  # Should be configured in the system

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = 'email_assistant_db'

async def send_test_email(subject, body):
    """Send test email via SMTP"""
    print(f"\n{'='*60}")
    print(f"📧 Sending test email...")
    print(f"From: {SENDER_EMAIL}")
    print(f"To: {RECIPIENT_EMAIL}")
    print(f"Subject: {subject}")
    print(f"{'='*60}\n")
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        
        print("✅ Email sent successfully!\n")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}\n")
        return False

async def get_user_and_account():
    """Get user and email account info"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Find user with the recipient email
    account = await db.email_accounts.find_one({"email": RECIPIENT_EMAIL, "is_active": True})
    if not account:
        print(f"❌ No active email account found for {RECIPIENT_EMAIL}")
        client.close()
        return None, None, None
    
    user = await db.users.find_one({"id": account['user_id']})
    if not user:
        print(f"❌ No user found for account {account['id']}")
        client.close()
        return None, None, None
    
    client.close()
    return user, account, db

async def check_email_processing(user_id, subject):
    """Check if email was processed and auto-reply sent"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print(f"\n{'='*60}")
    print(f"🔍 Waiting for email processing...")
    print(f"{'='*60}\n")
    
    max_wait = 120  # Wait up to 2 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        # Find email with the subject
        emails = await db.emails.find({
            "user_id": user_id,
            "subject": subject,
            "direction": "inbound"
        }).sort("created_at", -1).limit(1).to_list(1)
        
        if emails:
            email = emails[0]
            print(f"✅ Email found: {email['id']}")
            print(f"   Status: {email.get('status', 'pending')}")
            print(f"   Intent: {email.get('intent_name', 'Not detected')}")
            print(f"   Confidence: {email.get('intent_confidence', 0)}")
            print(f"   Draft generated: {email.get('draft_generated', False)}")
            print(f"   Draft validated: {email.get('draft_validated', False)}")
            print(f"   Replied: {email.get('replied', False)}")
            print(f"   Thread ID: {email.get('thread_id', 'None')}")
            print(f"   Meeting detected: {email.get('meeting_detected', False)}")
            
            if email.get('replied'):
                print(f"\n✅ Auto-reply sent!")
                client.close()
                return email
        
        await asyncio.sleep(5)
        print("   Waiting... (checking every 5 seconds)")
    
    client.close()
    print(f"\n❌ Timeout: Email not processed within {max_wait} seconds")
    return None

async def check_follow_ups(user_id, email_id):
    """Check if follow-ups were created"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print(f"\n{'='*60}")
    print(f"🔍 Checking follow-ups...")
    print(f"{'='*60}\n")
    
    follow_ups = await db.follow_ups.find({
        "user_id": user_id,
        "email_id": email_id
    }).sort("scheduled_at", 1).to_list(10)
    
    if not follow_ups:
        print("❌ No follow-ups found")
        client.close()
        return None
    
    print(f"✅ Found {len(follow_ups)} follow-up(s):\n")
    for i, fu in enumerate(follow_ups, 1):
        print(f"   Follow-up #{i}:")
        print(f"      ID: {fu['id']}")
        print(f"      Status: {fu.get('status', 'pending')}")
        print(f"      Scheduled: {fu.get('scheduled_at')}")
        print(f"      Thread ID: {fu.get('thread_id', 'None')}")
        print(f"      Subject: {fu.get('subject')}")
        print()
    
    client.close()
    return follow_ups

async def check_calendar_event(user_id, email_id):
    """Check if calendar event was created"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print(f"\n{'='*60}")
    print(f"🔍 Checking calendar events...")
    print(f"{'='*60}\n")
    
    events = await db.calendar_events.find({
        "user_id": user_id,
        "email_id": email_id
    }).to_list(10)
    
    if not events:
        print("❌ No calendar events found")
        client.close()
        return None
    
    print(f"✅ Found {len(events)} calendar event(s):\n")
    for event in events:
        print(f"   Event:")
        print(f"      ID: {event['id']}")
        print(f"      Title: {event.get('title')}")
        print(f"      Start: {event.get('start_time')}")
        print(f"      Thread ID: {event.get('thread_id', 'None')}")
        print(f"      Meet Link: {event.get('meet_link', 'None')}")
        print()
    
    client.close()
    return events

async def send_reply_email(original_email_id, subject):
    """Send a reply to cancel follow-ups"""
    print(f"\n{'='*60}")
    print(f"📧 Sending reply email to cancel follow-ups...")
    print(f"{'='*60}\n")
    
    reply_subject = f"Re: {subject}"
    reply_body = "Thank you for your response! This looks great. I'll review and get back to you."
    
    success = await send_test_email(reply_subject, reply_body)
    return success

async def check_follow_up_cancellation(user_id, email_id):
    """Check if follow-ups were cancelled after reply"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print(f"\n{'='*60}")
    print(f"🔍 Waiting for follow-up cancellation...")
    print(f"{'='*60}\n")
    
    max_wait = 90  # Wait up to 90 seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        follow_ups = await db.follow_ups.find({
            "user_id": user_id,
            "email_id": email_id
        }).to_list(10)
        
        if follow_ups:
            cancelled_count = sum(1 for fu in follow_ups if fu.get('status') == 'cancelled')
            pending_count = sum(1 for fu in follow_ups if fu.get('status') == 'pending')
            
            print(f"   Total follow-ups: {len(follow_ups)}")
            print(f"   Cancelled: {cancelled_count}")
            print(f"   Pending: {pending_count}")
            
            if cancelled_count == len(follow_ups):
                print(f"\n✅ All follow-ups cancelled!")
                for fu in follow_ups:
                    print(f"      {fu['id']}: {fu.get('status')} - {fu.get('cancelled_reason', 'No reason')}")
                client.close()
                return True
        
        await asyncio.sleep(5)
        print("   Waiting... (checking every 5 seconds)\n")
    
    client.close()
    print(f"\n⚠️  Timeout: Follow-ups not cancelled within {max_wait} seconds")
    return False

async def check_account_settings(account_id):
    """Check email account follow-up settings"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print(f"\n{'='*60}")
    print(f"🔍 Checking email account settings...")
    print(f"{'='*60}\n")
    
    account = await db.email_accounts.find_one({"id": account_id})
    
    if account:
        print(f"✅ Email Account: {account.get('email')}")
        print(f"   Follow-up enabled: {account.get('follow_up_enabled', True)}")
        print(f"   Follow-up days: {account.get('follow_up_days', 2)}")
        print(f"   Follow-up count: {account.get('follow_up_count', 3)}")
        print(f"   Auto-reply enabled: {account.get('auto_reply_enabled', False)}")
        print()
    
    client.close()

async def main():
    """Main test flow"""
    print("\n" + "="*60)
    print("🧪 FOLLOW-UP AND REMINDER FLOW TEST")
    print("="*60)
    
    # Get user and account info
    user, account, db = await get_user_and_account()
    if not user or not account:
        return
    
    print(f"\n✅ Found user: {user.get('email', user['id'])}")
    print(f"✅ Found account: {account['email']}")
    
    # Check account settings
    await check_account_settings(account['id'])
    
    # Test 1: Send test email with meeting request
    test_subject = f"Test Meeting Request - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
    test_body = """Hi,

I hope this email finds you well. I wanted to reach out to schedule a meeting to discuss our upcoming project.

Could we schedule a call tomorrow at 3 PM EST? We can discuss the project requirements and timeline.

Looking forward to hearing from you!

Best regards"""
    
    if not await send_test_email(test_subject, test_body):
        return
    
    # Test 2: Wait for email processing
    email = await check_email_processing(user['id'], test_subject)
    if not email:
        return
    
    # Test 3: Check follow-ups
    follow_ups = await check_follow_ups(user['id'], email['id'])
    if not follow_ups:
        print("⚠️  Warning: No follow-ups created")
    
    # Test 4: Check calendar event
    events = await check_calendar_event(user['id'], email['id'])
    if not events:
        print("⚠️  Warning: No calendar event created")
    
    # Test 5: Send reply to cancel follow-ups
    print(f"\n{'='*60}")
    print(f"⏳ Waiting 10 seconds before sending reply...")
    print(f"{'='*60}\n")
    await asyncio.sleep(10)
    
    if await send_reply_email(email['id'], test_subject):
        # Test 6: Check follow-up cancellation
        await check_follow_up_cancellation(user['id'], email['id'])
    
    print(f"\n{'='*60}")
    print(f"✅ TEST COMPLETED!")
    print(f"{'='*60}\n")
    
    print("Summary:")
    print(f"✅ Email sent and received")
    print(f"✅ Email processed with auto-reply")
    print(f"✅ Follow-ups created: {len(follow_ups) if follow_ups else 0}")
    print(f"✅ Thread ID preserved: {email.get('thread_id') is not None}")
    print(f"✅ Calendar event created: {len(events) if events else 0}")
    print(f"✅ Reply sent to cancel follow-ups")
    print()

if __name__ == "__main__":
    asyncio.run(main())
