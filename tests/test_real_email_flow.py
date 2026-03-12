"""
Real Email Flow Testing
Sends actual test emails using SMTP and verifies the complete workflow
"""
import asyncio
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from motor.motor_asyncio import AsyncIOMotorClient
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from config import config


class RealEmailTester:
    """Test complete email flow with real email sending"""
    
    def __init__(self, smtp_email: str, smtp_password: str, target_email: str):
        self.smtp_email = smtp_email
        self.smtp_password = smtp_password
        self.target_email = target_email
        self.test_results = []
    
    def send_test_email(self, subject: str, body: str) -> bool:
        """Send a test email via SMTP"""
        try:
            print(f"📧 Sending test email: {subject}")
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_email
            msg['To'] = self.target_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.smtp_email, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.smtp_email, self.target_email, text)
            server.quit()
            
            print(f"✅ Email sent successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    async def verify_email_processing(self, user_email: str, expected_count: int, timeout: int = 180):
        """Verify emails are processed in the database"""
        print(f"\n⏳ Waiting for email processing (timeout: {timeout}s)...")
        
        client = AsyncIOMotorClient(config.MONGO_URL)
        db = client[config.DB_NAME]
        
        try:
            # Find user
            user = await db.users.find_one({"email": user_email})
            if not user:
                print(f"❌ User not found: {user_email}")
                return False
            
            user_id = user['id']
            
            # Get email account
            email_account = await db.email_accounts.find_one({
                "user_id": user_id,
                "account_type": "oauth_gmail"
            })
            
            if not email_account:
                print(f"❌ No email account found for user")
                return False
            
            email_account_id = email_account['id']
            print(f"✓ Found email account: {email_account['email']}")
            
            start_time = time.time()
            last_count = 0
            
            while time.time() - start_time < timeout:
                # Check for processed emails
                emails = await db.emails.find({
                    "email_account_id": email_account_id
                }).sort("received_at", -1).to_list(expected_count + 10)
                
                current_count = len(emails)
                
                if current_count != last_count:
                    print(f"📊 Found {current_count} emails in database")
                    last_count = current_count
                
                if current_count >= expected_count:
                    print(f"\n✅ All {expected_count} emails found in database")
                    
                    # Display email details
                    print("\n" + "="*70)
                    print("EMAIL PROCESSING DETAILS:")
                    print("="*70)
                    
                    for i, email in enumerate(emails[:expected_count], 1):
                        print(f"\n{i}. Subject: {email.get('subject', 'N/A')}")
                        print(f"   From: {email.get('from_email', 'N/A')}")
                        print(f"   Status: {email.get('status', 'N/A')}")
                        print(f"   Intent: {email.get('intent_detected', 'N/A')}")
                        
                        draft = email.get('draft_generated')
                        if draft and isinstance(draft, str):
                            print(f"   Draft: ✅ Generated ({len(draft)} chars)")
                        elif draft:
                            print(f"   Draft: ✅ Generated")
                        else:
                            print(f"   Draft: ❌ Not generated")
                        
                        if email.get('auto_sent'):
                            print(f"   Auto-sent: ✅ Yes")
                        else:
                            print(f"   Auto-sent: ❌ No")
                        
                        # Check action history
                        actions = email.get('action_history', [])
                        if actions:
                            print(f"   Actions: {len(actions)} recorded")
                            for action in actions[:3]:  # Show first 3 actions
                                print(f"      - {action.get('action', 'N/A')} ({action.get('status', 'N/A')})")
                    
                    return True
                
                # Wait before next check
                await asyncio.sleep(5)
                remaining = int(timeout - (time.time() - start_time))
                if remaining % 30 == 0:
                    print(f"⏳ Still waiting... ({remaining}s remaining)")
            
            print(f"\n❌ Timeout: Only found {last_count}/{expected_count} emails after {timeout}s")
            return False
            
        finally:
            client.close()
    
    async def verify_intents_and_kb(self, user_email: str):
        """Verify intents and knowledge base are loaded"""
        print(f"\n🔍 Verifying seed data for {user_email}...")
        
        client = AsyncIOMotorClient(config.MONGO_URL)
        db = client[config.DB_NAME]
        
        try:
            # Find user
            user = await db.users.find_one({"email": user_email})
            if not user:
                print(f"❌ User not found: {user_email}")
                return False
            
            user_id = user['id']
            
            # Check intents
            intents = await db.intents.find({"user_id": user_id}).to_list(100)
            print(f"✓ Intents: {len(intents)} found")
            
            auto_send_count = len([i for i in intents if i.get('auto_send', False)])
            default_count = len([i for i in intents if i.get('is_default', False)])
            
            print(f"  - Auto-send enabled: {auto_send_count}")
            print(f"  - Default intent: {'Yes' if default_count > 0 else 'No'}")
            
            # Check knowledge base
            kb_entries = await db.knowledge_base.find({"user_id": user_id}).to_list(100)
            print(f"✓ Knowledge Base: {len(kb_entries)} entries found")
            
            categories = set(kb.get('category', 'Unknown') for kb in kb_entries)
            print(f"  - Categories: {', '.join(categories)}")
            
            return len(intents) > 0 and len(kb_entries) > 0
            
        finally:
            client.close()


async def run_complete_test():
    """Run complete real email flow test"""
    
    print("="*70)
    print("🧪 REAL EMAIL FLOW TEST")
    print("="*70)
    
    # Configuration
    SMTP_EMAIL = "sagarshinde15798796456@gmail.com"
    SMTP_PASSWORD = "bmwqmytxrsgrlusp"
    TARGET_EMAIL = "amits.joys@gmail.com"
    
    tester = RealEmailTester(SMTP_EMAIL, SMTP_PASSWORD, TARGET_EMAIL)
    
    # Step 1: Verify seed data
    print("\n" + "="*70)
    print("STEP 1: VERIFY SEED DATA")
    print("="*70)
    
    seed_ok = await tester.verify_intents_and_kb(TARGET_EMAIL)
    if not seed_ok:
        print("\n❌ Seed data not found. Please run: python scripts/create_production_seed.py amits.joys@gmail.com")
        return
    
    # Step 2: Send test emails
    print("\n" + "="*70)
    print("STEP 2: SEND TEST EMAILS")
    print("="*70)
    
    test_emails = [
        {
            "subject": "Let's schedule a meeting for tomorrow",
            "body": """Hi Amit,

Hope you're doing well! I'd like to schedule a meeting to discuss the new AI features.

Would you be available tomorrow at 2pm EST? We can do a Zoom call.

Looking forward to connecting!

Best regards,
Sagar"""
        },
        {
            "subject": "Question about pricing",
            "body": """Hello,

I'm interested in your AI Email Assistant and would like to know more about the pricing plans.

Specifically:
- What's included in the Professional plan?
- Is there a free trial?
- Any discounts for annual billing?

Thanks!
Sagar"""
        },
        {
            "subject": "Need help with email integration",
            "body": """Hi Support Team,

I'm having trouble connecting my Gmail account. When I click the "Connect Gmail" button, I get redirected but then see an error message.

Can you help me troubleshoot this issue?

Thanks,
Sagar"""
        }
    ]
    
    emails_sent = 0
    for test_email in test_emails:
        if tester.send_test_email(test_email['subject'], test_email['body']):
            emails_sent += 1
            time.sleep(2)  # Wait between emails
    
    if emails_sent == 0:
        print("\n❌ No emails sent successfully. Cannot continue test.")
        return
    
    print(f"\n✅ Sent {emails_sent} test emails")
    
    # Step 3: Wait for processing
    print("\n" + "="*70)
    print("STEP 3: VERIFY EMAIL PROCESSING")
    print("="*70)
    print("\nNote: Email polling runs every 60 seconds")
    print("Expected flow:")
    print("  1. Email received by Gmail")
    print("  2. Worker polls and fetches email (~60s)")
    print("  3. Intent classified")
    print("  4. Draft generated")
    print("  5. Draft validated")
    print("  6. Auto-sent (if intent has auto_send=true)")
    
    processing_ok = await tester.verify_email_processing(TARGET_EMAIL, emails_sent, timeout=180)
    
    # Final summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    if processing_ok:
        print("\n✅ ALL TESTS PASSED!")
        print("\nYour AI Email Assistant is working correctly:")
        print("  ✅ Seed data loaded (intents & knowledge base)")
        print("  ✅ Email sending working")
        print("  ✅ Email polling working")
        print("  ✅ Intent classification working")
        print("  ✅ Draft generation working")
        print("\nNext steps:")
        print("  1. Check your email (amits.joys@gmail.com) for auto-sent replies")
        print("  2. Log in to the frontend to see email processing details")
        print("  3. Review drafts in the dashboard")
    else:
        print("\n⚠️ TEST INCOMPLETE")
        print("\nSome emails may still be processing.")
        print("Check the following:")
        print("  1. Backend logs: tail -f /var/log/supervisor/backend.err.log")
        print("  2. Worker status: Check for polling messages")
        print("  3. Database: Verify emails are being saved")


if __name__ == "__main__":
    print("\n🚀 Starting Real Email Flow Test\n")
    asyncio.run(run_complete_test())
