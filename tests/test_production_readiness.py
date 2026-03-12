#!/usr/bin/env python3
"""
Comprehensive Production Readiness Tests

Tests the following critical features:
1. Auto draft/reply function working in same thread
2. Auto follow-up task creation and automatic cancellation when user responds
3. Intelligent system detecting and responding in same threads
4. Meeting intent detection and calendar event creation with links
5. Meeting reminders and rescheduling
6. Inbound leads tracking with status
7. Campaigns and follow-ups with personalization
"""
import asyncio
import sys
import uuid
import smtplib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import redis

# Test configuration
USER_EMAIL = "amits.joys@gmail.com"
USER_ID = "fa274be2-5628-49f4-916a-f86d3e98c76a"

# Test email account
TEST_EMAIL = "rohushanshinde@gmail.com"
TEST_PASSWORD = "pajbdmcpcegppguz"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Recipients (these should be in the email accounts)
RECIPIENT_EMAIL = "amits.joys@gmail.com"

# Test tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}


def log_test(test_name, passed, message=""):
    """Log test result"""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        print(f"✅ {test_name}: PASSED")
        if message:
            print(f"   {message}")
    else:
        test_results["failed"] += 1
        test_results["errors"].append(f"{test_name}: {message}")
        print(f"❌ {test_name}: FAILED")
        print(f"   {message}")


async def send_test_email(subject, body, reply_to_message_id=None, in_reply_to=None, references=None):
    """Send a test email via SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = TEST_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        
        if reply_to_message_id:
            msg['In-Reply-To'] = reply_to_message_id
            msg['References'] = references or reply_to_message_id
        
        # Generate unique message ID
        message_id = f"<{uuid.uuid4()}@gmail.com>"
        msg['Message-ID'] = message_id
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(TEST_EMAIL, TEST_PASSWORD)
            server.send_message(msg)
        
        print(f"📧 Sent email: {subject}")
        return message_id
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return None


async def test_1_infrastructure_check(db, redis_client):
    """Test 1: Infrastructure Check"""
    print("\n" + "=" * 70)
    print("TEST 1: Infrastructure Check")
    print("=" * 70)
    
    # Check MongoDB
    try:
        await db.command('ping')
        log_test("MongoDB Connection", True, "MongoDB is accessible")
    except Exception as e:
        log_test("MongoDB Connection", False, f"MongoDB error: {e}")
    
    # Check Redis
    try:
        redis_client.ping()
        log_test("Redis Connection", True, "Redis is accessible")
    except Exception as e:
        log_test("Redis Connection", False, f"Redis error: {e}")
    
    # Check user exists
    user = await db.users.find_one({"id": USER_ID})
    if user:
        log_test("User Exists", True, f"User: {user['email']}")
    else:
        log_test("User Exists", False, "User not found")
    
    # Check email account
    email_account = await db.email_accounts.find_one({"user_id": USER_ID})
    if email_account and email_account.get('is_active'):
        log_test("Email Account Connected", True, f"Account: {email_account['email']}")
    else:
        log_test("Email Account Connected", False, "No active email account")
    
    # Check calendar provider
    calendar_provider = await db.calendar_providers.find_one({"user_id": USER_ID})
    if calendar_provider and calendar_provider.get('is_active'):
        log_test("Calendar Provider Connected", True, f"Provider: {calendar_provider['provider']}")
    else:
        log_test("Calendar Provider Connected", False, "No active calendar provider")
    
    # Check intents
    intents_count = await db.intents.count_documents({"user_id": USER_ID, "is_active": True})
    if intents_count > 0:
        log_test("Intents Configured", True, f"{intents_count} active intents")
    else:
        log_test("Intents Configured", False, "No active intents")
    
    # Check knowledge base
    kb_count = await db.knowledge_base.count_documents({"user_id": USER_ID, "is_active": True})
    if kb_count > 0:
        log_test("Knowledge Base Populated", True, f"{kb_count} active entries")
    else:
        log_test("Knowledge Base Populated", False, "No knowledge base entries")


async def test_2_send_initial_emails(db):
    """Test 2: Send Initial Test Emails"""
    print("\n" + "=" * 70)
    print("TEST 2: Sending Initial Test Emails")
    print("=" * 70)
    
    test_emails = [
        {
            "subject": "Meeting Request - Next Week",
            "body": "Hi,\n\nI would like to schedule a meeting with you next week to discuss our AI email assistant platform. Are you available for a 30-minute call on Tuesday or Wednesday?\n\nLooking forward to hearing from you!\n\nBest regards"
        },
        {
            "subject": "Follow-up on Previous Discussion",
            "body": "Hi,\n\nJust following up on our previous discussion about the email automation platform. Do you have any updates or questions?\n\nThanks!"
        },
        {
            "subject": "Support Needed - Integration Issue",
            "body": "Hello,\n\nI'm having some trouble integrating the calendar feature. Can you help me troubleshoot this issue?\n\nThanks for your assistance!"
        }
    ]
    
    sent_count = 0
    for email_data in test_emails:
        message_id = await send_test_email(email_data["subject"], email_data["body"])
        if message_id:
            sent_count += 1
            await asyncio.sleep(2)
    
    log_test("Initial Emails Sent", sent_count == len(test_emails), 
             f"Sent {sent_count}/{len(test_emails)} emails")
    
    # Store message IDs for later reference
    return sent_count


async def test_3_email_processing(db):
    """Test 3: Email Processing and Intent Classification"""
    print("\n" + "=" * 70)
    print("TEST 3: Email Processing and Intent Classification")
    print("=" * 70)
    print("⏳ Waiting 90 seconds for email polling and processing...")
    
    await asyncio.sleep(90)
    
    # Check if emails were received
    emails = await db.emails.find(
        {"user_id": USER_ID},
        sort=[("created_at", -1)]
    ).limit(10).to_list(10)
    
    if len(emails) > 0:
        log_test("Emails Received", True, f"Found {len(emails)} recent emails")
        
        # Check intent classification
        classified_count = sum(1 for e in emails if e.get('intent_detected'))
        log_test("Intent Classification", classified_count > 0,
                f"{classified_count}/{len(emails)} emails classified")
        
        # Check draft generation
        draft_count = sum(1 for e in emails if e.get('draft_content'))
        log_test("Draft Generation", draft_count > 0,
                f"{draft_count}/{len(emails)} drafts generated")
        
        # Check thread IDs
        thread_count = sum(1 for e in emails if e.get('thread_id'))
        log_test("Thread ID Extraction", thread_count > 0,
                f"{thread_count}/{len(emails)} emails have thread IDs")
        
        return emails
    else:
        log_test("Emails Received", False, "No emails found in database")
        return []


async def test_4_auto_reply_in_same_thread(db, processed_emails):
    """Test 4: Auto Reply in Same Thread"""
    print("\n" + "=" * 70)
    print("TEST 4: Auto Reply in Same Thread")
    print("=" * 70)
    
    if not processed_emails:
        log_test("Auto Reply Test", False, "No processed emails to test")
        return
    
    # Check for sent emails
    sent_emails = [e for e in processed_emails if e.get('status') == 'sent']
    
    if len(sent_emails) > 0:
        log_test("Auto-Send Functionality", True,
                f"{len(sent_emails)} emails auto-sent")
        
        # Verify thread continuity
        for email in sent_emails:
            if email.get('thread_id'):
                log_test(f"Thread Continuity - {email.get('subject', 'Unknown')[:30]}", 
                        True, f"Thread ID: {email['thread_id']}")
            else:
                log_test(f"Thread Continuity - {email.get('subject', 'Unknown')[:30]}", 
                        False, "No thread ID found")
    else:
        log_test("Auto-Send Functionality", False, 
                "No emails were auto-sent. Check intent auto_send configuration")


async def test_5_follow_up_creation(db, processed_emails):
    """Test 5: Follow-up Creation"""
    print("\n" + "=" * 70)
    print("TEST 5: Follow-up Creation")
    print("=" * 70)
    
    if not processed_emails:
        log_test("Follow-up Creation Test", False, "No processed emails to test")
        return
    
    # Check follow-ups
    total_followups = 0
    for email in processed_emails:
        followups = await db.follow_ups.find(
            {"email_id": email['id']}
        ).to_list(10)
        total_followups += len(followups)
    
    if total_followups > 0:
        log_test("Follow-up Creation", True,
                f"{total_followups} follow-ups created")
        
        # Check follow-up status
        pending_followups = await db.follow_ups.count_documents({
            "user_id": USER_ID,
            "status": "pending"
        })
        log_test("Pending Follow-ups", pending_followups > 0,
                f"{pending_followups} pending follow-ups")
    else:
        log_test("Follow-up Creation", False, "No follow-ups created")


async def test_6_meeting_detection_and_calendar(db, processed_emails):
    """Test 6: Meeting Detection and Calendar Event Creation"""
    print("\n" + "=" * 70)
    print("TEST 6: Meeting Detection and Calendar Event Creation")
    print("=" * 70)
    
    # Check for meeting-related emails
    meeting_emails = [e for e in processed_emails 
                     if e.get('meeting_detected') or 
                     'meeting' in e.get('subject', '').lower()]
    
    if len(meeting_emails) > 0:
        log_test("Meeting Detection", True,
                f"{len(meeting_emails)} meeting requests detected")
        
        # Check calendar events
        calendar_events = await db.calendar_events.find(
            {"user_id": USER_ID}
        ).sort([("created_at", -1)]).limit(5).to_list(5)
        
        if len(calendar_events) > 0:
            log_test("Calendar Event Creation", True,
                    f"{len(calendar_events)} calendar events created")
            
            # Check for meeting links
            events_with_links = [e for e in calendar_events 
                               if e.get('meet_link') or e.get('html_link')]
            log_test("Meeting Links Generated", len(events_with_links) > 0,
                    f"{len(events_with_links)} events have meeting links")
        else:
            log_test("Calendar Event Creation", False, "No calendar events found")
    else:
        log_test("Meeting Detection", False, "No meeting requests detected in test emails")


async def test_7_reply_detection_and_follow_up_cancellation(db):
    """Test 7: Reply Detection and Follow-up Cancellation"""
    print("\n" + "=" * 70)
    print("TEST 7: Reply Detection and Follow-up Cancellation")
    print("=" * 70)
    
    # Get an email with follow-ups
    email_with_followups = await db.emails.find_one({
        "user_id": USER_ID,
        "status": "sent"
    })
    
    if not email_with_followups:
        log_test("Reply Detection Test", False, "No sent emails found for testing")
        return
    
    # Check if there are pending follow-ups
    followups = await db.follow_ups.find({
        "email_id": email_with_followups['id'],
        "status": "pending"
    }).to_list(10)
    
    if len(followups) > 0:
        print(f"📧 Found {len(followups)} pending follow-ups")
        
        # Simulate reply by sending email in same thread
        if email_with_followups.get('thread_id'):
            print("📧 Sending reply to test follow-up cancellation...")
            reply_id = await send_test_email(
                f"Re: {email_with_followups.get('subject', 'Test')}",
                "Thank you for your response! This looks great.",
                reply_to_message_id=email_with_followups.get('message_id'),
                references=email_with_followups.get('thread_id')
            )
            
            if reply_id:
                print("⏳ Waiting 60 seconds for reply detection...")
                await asyncio.sleep(60)
                
                # Check if follow-ups were cancelled
                cancelled_followups = await db.follow_ups.count_documents({
                    "email_id": email_with_followups['id'],
                    "status": "cancelled"
                })
                
                log_test("Follow-up Cancellation on Reply", cancelled_followups > 0,
                        f"{cancelled_followups} follow-ups cancelled after reply")
            else:
                log_test("Follow-up Cancellation on Reply", False, "Failed to send reply")
        else:
            log_test("Follow-up Cancellation on Reply", False, "No thread ID to reply to")
    else:
        log_test("Follow-up Cancellation on Reply", False, "No pending follow-ups found")


async def test_8_inbound_leads_tracking(db):
    """Test 8: Inbound Leads Tracking"""
    print("\n" + "=" * 70)
    print("TEST 8: Inbound Leads Tracking")
    print("=" * 70)
    
    # Check inbound leads
    leads = await db.inbound_leads.find(
        {"user_id": USER_ID}
    ).to_list(20)
    
    if len(leads) > 0:
        log_test("Inbound Leads Created", True, f"Found {len(leads)} inbound leads")
        
        # Check lead stages
        stages = {}
        for lead in leads:
            stage = lead.get('stage', 'unknown')
            stages[stage] = stages.get(stage, 0) + 1
        
        print(f"   Lead Stages Distribution:")
        for stage, count in stages.items():
            print(f"      - {stage.upper()}: {count} leads")
        
        # Check lead activities
        leads_with_activities = [l for l in leads if l.get('activities')]
        log_test("Lead Activities Tracked", len(leads_with_activities) > 0,
                f"{len(leads_with_activities)} leads have activity tracking")
        
        # Check lead scoring
        leads_with_scores = [l for l in leads if l.get('score')]
        log_test("Lead Scoring", len(leads_with_scores) > 0,
                f"{len(leads_with_scores)} leads have scores")
    else:
        log_test("Inbound Leads Created", False, "No inbound leads found")


async def test_9_campaign_functionality(db):
    """Test 9: Campaign Functionality"""
    print("\n" + "=" * 70)
    print("TEST 9: Campaign Functionality")
    print("=" * 70)
    
    # Check campaign templates
    templates = await db.campaign_templates.find(
        {"user_id": USER_ID, "is_active": True}
    ).to_list(20)
    
    if len(templates) > 0:
        log_test("Campaign Templates Created", True, f"Found {len(templates)} templates")
        
        # Check template personalization
        templates_with_tags = [t for t in templates 
                              if '{{' in t.get('body', '') or '{{' in t.get('subject', '')]
        log_test("Template Personalization", len(templates_with_tags) > 0,
                f"{len(templates_with_tags)} templates have personalization tags")
    else:
        log_test("Campaign Templates Created", False, "No campaign templates found")
    
    # Check contact lists
    contact_lists = await db.contact_lists.find(
        {"user_id": USER_ID}
    ).to_list(20)
    
    if len(contact_lists) > 0:
        log_test("Contact Lists Created", True, f"Found {len(contact_lists)} contact lists")
        
        # Check for specific list
        topleaders_list = await db.contact_lists.find_one({
            "user_id": USER_ID,
            "name": "Topleaders"
        })
        
        if topleaders_list:
            log_test("Topleaders List Exists", True,
                    f"List has {len(topleaders_list.get('contact_ids', []))} contacts")
        else:
            log_test("Topleaders List Exists", False,
                    "List 'Topleaders' not found - User needs to create it")
    else:
        log_test("Contact Lists Created", False, "No contact lists found")
    
    # Check campaigns
    campaigns = await db.campaigns.find(
        {"user_id": USER_ID}
    ).to_list(20)
    
    if len(campaigns) > 0:
        log_test("Campaigns Created", True, f"Found {len(campaigns)} campaigns")
        
        # Check campaign status
        active_campaigns = [c for c in campaigns if c.get('status') in ['running', 'scheduled']]
        log_test("Active Campaigns", len(active_campaigns) > 0,
                f"{len(active_campaigns)} active campaigns")
    else:
        log_test("Campaigns Created", False, "No campaigns found")


async def test_10_thread_intelligence(db):
    """Test 10: Thread Intelligence - Responding in Same Thread"""
    print("\n" + "=" * 70)
    print("TEST 10: Thread Intelligence")
    print("=" * 70)
    
    # Check for emails with thread tracking
    emails_with_threads = await db.emails.find({
        "user_id": USER_ID,
        "thread_id": {"$exists": True, "$ne": None}
    }).to_list(20)
    
    if len(emails_with_threads) > 0:
        log_test("Thread Tracking", True,
                f"{len(emails_with_threads)} emails have thread tracking")
        
        # Check for thread continuity
        thread_groups = {}
        for email in emails_with_threads:
            thread_id = email.get('thread_id')
            if thread_id:
                if thread_id not in thread_groups:
                    thread_groups[thread_id] = []
                thread_groups[thread_id].append(email)
        
        multi_email_threads = {tid: emails for tid, emails in thread_groups.items() 
                               if len(emails) > 1}
        
        log_test("Thread Continuity", len(multi_email_threads) > 0,
                f"{len(multi_email_threads)} threads with multiple emails")
    else:
        log_test("Thread Tracking", False, "No emails with thread tracking found")


async def run_all_tests():
    """Run all production readiness tests"""
    print("\n" + "=" * 70)
    print("🚀 PRODUCTION READINESS TEST SUITE")
    print("=" * 70)
    print(f"User: {USER_EMAIL}")
    print(f"Test Email: {TEST_EMAIL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(Config.MONGO_URL)
    db = client[Config.DB_NAME]
    
    # Connect to Redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    try:
        # Run tests
        await test_1_infrastructure_check(db, redis_client)
        
        sent_count = await test_2_send_initial_emails(db)
        
        if sent_count > 0:
            processed_emails = await test_3_email_processing(db)
            
            await test_4_auto_reply_in_same_thread(db, processed_emails)
            await test_5_follow_up_creation(db, processed_emails)
            await test_6_meeting_detection_and_calendar(db, processed_emails)
            await test_7_reply_detection_and_follow_up_cancellation(db)
            await test_10_thread_intelligence(db)
        
        await test_8_inbound_leads_tracking(db)
        await test_9_campaign_functionality(db)
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {test_results['total']}")
        print(f"✅ Passed: {test_results['passed']}")
        print(f"❌ Failed: {test_results['failed']}")
        
        if test_results['failed'] > 0:
            print(f"\n❌ Failed Tests:")
            for error in test_results['errors']:
                print(f"   - {error}")
        
        success_rate = (test_results['passed'] / test_results['total'] * 100) if test_results['total'] > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n✅ SYSTEM IS PRODUCTION READY!")
        elif success_rate >= 60:
            print("\n⚠️  SYSTEM NEEDS ATTENTION - Some features require fixes")
        else:
            print("\n❌ SYSTEM NOT READY - Critical issues need resolution")
        
        print("=" * 70)
        
    finally:
        client.close()
        redis_client.close()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
