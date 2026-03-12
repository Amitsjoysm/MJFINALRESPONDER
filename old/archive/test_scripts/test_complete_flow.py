#!/usr/bin/env python3
"""
Complete Production Flow Test
Sends real emails and verifies end-to-end functionality
"""
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import time

# Configuration
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "email_assistant_db"
USER_EMAIL = "amits.joys@gmail.com"

# Test email credentials
SENDER_EMAIL = "sagarshinde15798796456@gmail.com"
SENDER_PASSWORD = "bmwqmytxrsgrlusp"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_test_email(subject: str, body: str, recipient: str):
    """Send a test email via SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, recipient, text)
        server.quit()
        
        print(f"✅ Sent email: {subject}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


async def wait_for_processing(db, email_subject: str, timeout: int = 120):
    """Wait for email to be processed"""
    print(f"⏳ Waiting for email '{email_subject}' to be processed (timeout: {timeout}s)...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        email_doc = await db.emails.find_one({
            "subject": email_subject,
            "processed": True
        })
        
        if email_doc:
            print(f"✅ Email processed: {email_subject}")
            return email_doc
        
        await asyncio.sleep(5)
    
    print(f"⏱️ Timeout waiting for email: {email_subject}")
    return None


async def check_calendar_event(db, email_id: str):
    """Check if calendar event was created"""
    email_doc = await db.emails.find_one({"id": email_id})
    if email_doc and email_doc.get('calendar_event'):
        event_id = email_doc['calendar_event'].get('event_id')
        if event_id:
            event = await db.calendar_events.find_one({"event_id": event_id})
            if event:
                print(f"✅ Calendar event created: {event.get('title')}")
                print(f"   - Event ID: {event_id}")
                print(f"   - Start: {event.get('start_time')}")
                print(f"   - Meet Link: {event.get('meet_link', 'N/A')}")
                return event
    return None


async def run_comprehensive_test():
    """Run complete production flow test"""
    print("\n" + "="*70)
    print("COMPREHENSIVE PRODUCTION FLOW TEST - STARTING")
    print("="*70 + "\n")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get user and account
    user = await db.users.find_one({"email": USER_EMAIL})
    if not user:
        print(f"❌ User not found: {USER_EMAIL}")
        client.close()
        return
    
    user_id = user['id']
    print(f"✅ User: {USER_EMAIL} (ID: {user_id})")
    
    # Get email account
    account = await db.email_accounts.find_one({"user_id": user_id, "is_active": True})
    if not account:
        print("❌ No active email account found")
        client.close()
        return
    
    recipient_email = account['email']
    print(f"✅ Recipient email account: {recipient_email}")
    
    # Check intents
    intents_count = await db.intents.count_documents({"user_id": user_id})
    kb_count = await db.knowledge_base.count_documents({"user_id": user_id})
    print(f"✅ Intents configured: {intents_count}")
    print(f"✅ Knowledge base entries: {kb_count}")
    
    # Check calendar provider
    calendar_provider = await db.calendar_providers.find_one({"user_id": user_id, "is_active": True})
    if calendar_provider:
        print(f"✅ Calendar provider connected: {calendar_provider.get('provider_email')}")
    else:
        print("⚠️ No calendar provider connected - meeting creation will be skipped")
    
    print("\n" + "="*70)
    print("PHASE 1: SENDING TEST EMAILS")
    print("="*70 + "\n")
    
    # Test emails to send
    test_emails = [
        {
            "subject": "Meeting Request for Next Week",
            "body": "Hi,\n\nCan we schedule a meeting next week to discuss the project progress? Tuesday or Wednesday afternoon works best for me.\n\nLooking forward to it!\n\nBest regards",
            "expected_intent": "Meeting Request",
            "should_create_event": True
        },
        {
            "subject": "Need Help with Login Issue",
            "body": "Hello,\n\nI'm having trouble logging into my account. I keep getting an 'invalid credentials' error even though I'm sure my password is correct.\n\nCan you please help me resolve this?\n\nThank you",
            "expected_intent": "Support Request",
            "should_create_event": False
        },
        {
            "subject": "Question About Pricing",
            "body": "Hi there,\n\nI'm interested in your Professional plan. Can you provide more details about what's included and if there are any discounts for annual subscriptions?\n\nThanks!",
            "expected_intent": "General Inquiry",
            "should_create_event": False
        },
        {
            "subject": "Thanks for Your Help",
            "body": "Thank you so much for your assistance with setting up my account. Everything is working perfectly now!\n\nI really appreciate your support.",
            "expected_intent": "Thank You",
            "should_create_event": False
        }
    ]
    
    sent_emails = []
    for test_email in test_emails:
        success = send_test_email(
            test_email["subject"],
            test_email["body"],
            recipient_email
        )
        if success:
            sent_emails.append(test_email)
            time.sleep(2)  # Small delay between emails
    
    print(f"\n✅ Sent {len(sent_emails)}/{len(test_emails)} test emails")
    
    print("\n" + "="*70)
    print("PHASE 2: WAITING FOR EMAIL PROCESSING (90 seconds)")
    print("="*70 + "\n")
    
    print("⏳ Allowing time for email polling and processing...")
    await asyncio.sleep(90)  # Wait for worker to poll and process
    
    print("\n" + "="*70)
    print("PHASE 3: VERIFYING RESULTS")
    print("="*70 + "\n")
    
    results = []
    for test_email in sent_emails:
        print(f"\n🔍 Checking: {test_email['subject']}")
        print("-" * 70)
        
        # Find processed email
        email_doc = await db.emails.find_one({
            "subject": test_email["subject"],
            "from_email": SENDER_EMAIL
        })
        
        if not email_doc:
            print(f"❌ Email not found in database")
            results.append({
                "subject": test_email["subject"],
                "found": False
            })
            continue
        
        result = {
            "subject": test_email["subject"],
            "found": True,
            "processed": email_doc.get('processed', False),
            "intent_detected": email_doc.get('intent_name', 'None'),
            "draft_generated": email_doc.get('draft_generated', False),
            "replied": email_doc.get('replied', False),
            "status": email_doc.get('status', 'unknown')
        }
        
        print(f"✅ Email found in database")
        print(f"   - Processed: {result['processed']}")
        print(f"   - Intent: {result['intent_detected']} (expected: {test_email['expected_intent']})")
        print(f"   - Draft generated: {result['draft_generated']}")
        print(f"   - Status: {result['status']}")
        print(f"   - Replied: {result['replied']}")
        
        # Check draft content
        if email_doc.get('draft_content'):
            draft_preview = email_doc['draft_content'][:150] + "..." if len(email_doc['draft_content']) > 150 else email_doc['draft_content']
            print(f"   - Draft preview: {draft_preview}")
        
        # Check follow-ups
        follow_ups = await db.follow_ups.find({"email_id": email_doc['id']}).to_list(100)
        result['follow_ups_created'] = len(follow_ups)
        print(f"   - Follow-ups created: {len(follow_ups)}")
        
        # Check calendar event
        if test_email['should_create_event'] and calendar_provider:
            event = await check_calendar_event(db, email_doc['id'])
            result['calendar_event_created'] = event is not None
            if not event:
                print(f"   ⚠️ Calendar event not created (expected for meeting request)")
        
        results.append(result)
    
    # Summary
    print("\n" + "="*70)
    print("PHASE 4: TEST SUMMARY")
    print("="*70 + "\n")
    
    total_emails = len(results)
    found = sum(1 for r in results if r['found'])
    processed = sum(1 for r in results if r.get('processed', False))
    drafted = sum(1 for r in results if r.get('draft_generated', False))
    replied = sum(1 for r in results if r.get('replied', False))
    total_follow_ups = sum(r.get('follow_ups_created', 0) for r in results)
    calendar_events = sum(1 for r in results if r.get('calendar_event_created', False))
    
    print(f"📧 Emails sent: {total_emails}")
    print(f"✅ Emails found in DB: {found}/{total_emails}")
    print(f"⚙️ Emails processed: {processed}/{total_emails}")
    print(f"📝 Drafts generated: {drafted}/{total_emails}")
    print(f"📤 Auto-replied: {replied}/{total_emails}")
    print(f"🔄 Total follow-ups created: {total_follow_ups}")
    print(f"📅 Calendar events created: {calendar_events}")
    
    # Success criteria
    success_rate = (processed / total_emails * 100) if total_emails > 0 else 0
    print(f"\n{'🎉' if success_rate == 100 else '⚠️'} Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100 and replied >= processed:
        print("\n✅ ALL TESTS PASSED! System is fully operational! 🚀")
    elif success_rate >= 75:
        print("\n⚠️ Most tests passed. Some issues may need attention.")
    else:
        print("\n❌ Multiple tests failed. System needs troubleshooting.")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70 + "\n")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())
