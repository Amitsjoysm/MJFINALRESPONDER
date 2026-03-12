"""
Test lead tracking by sending emails that should trigger lead creation
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

# Test email credentials
TEST_EMAIL = "rohushanshinde@gmail.com"
TEST_PASSWORD = "pajbdmcpcegppguz"
RECIPIENT_EMAIL = "amits.joys@gmail.com"

def send_test_email(subject, body):
    """Send test email using SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = TEST_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
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

async def check_leads_after_test(user_id):
    """Check if leads were created"""
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    # Check emails
    emails = await db.emails.find({
        "user_id": user_id,
        "from_email": TEST_EMAIL
    }).sort("received_at", -1).limit(5).to_list(5)
    
    print(f"\n📧 Emails from test sender: {len(emails)}")
    
    for email in emails:
        print(f"\n{'='*70}")
        print(f"📨 Subject: {email['subject']}")
        print(f"   Intent: {email.get('intent_name', 'N/A')} (ID: {email.get('intent_detected', 'N/A')})")
        print(f"   Confidence: {email.get('intent_confidence', 'N/A')}")
        print(f"   Processed: {email.get('processed', False)}")
        
        # Check if lead actions in history
        if email.get('action_history'):
            lead_actions = [a for a in email['action_history'] if 'lead' in a['action'].lower()]
            if lead_actions:
                print(f"   Lead Actions:")
                for action in lead_actions:
                    print(f"     • {action['action']} - {action.get('status', 'N/A')}")
                    if action.get('details'):
                        print(f"       Details: {action['details']}")
            else:
                print(f"   ⚠️  No lead actions found in history")
                print(f"   Total actions: {len(email['action_history'])}")
                # Show last few actions
                for action in email['action_history'][-3:]:
                    print(f"     • {action['action']}")
    
    # Check leads
    leads = await db.inbound_leads.find({
        "user_id": user_id,
        "lead_email": TEST_EMAIL
    }).to_list(10)
    
    print(f"\n{'='*70}")
    print(f"🎯 Leads created from test email: {len(leads)}")
    
    if leads:
        for lead in leads:
            print(f"\n   • {lead.get('lead_name', 'N/A')}")
            print(f"     Email: {lead.get('lead_email', 'N/A')}")
            print(f"     Company: {lead.get('company_name', 'N/A')}")
            print(f"     Stage: {lead.get('stage', 'N/A')}")
            print(f"     Score: {lead.get('score', 'N/A')}")
            print(f"     Source Intent: {lead.get('source_intent', 'N/A')}")
            print(f"     Created: {lead.get('created_at', 'N/A')}")
    else:
        print(f"   ❌ No leads created")
    
    # Check intents to see which one should match
    intents = await db.intents.find({
        "user_id": user_id,
        "is_inbound_lead": True
    }).to_list(10)
    
    print(f"\n{'='*70}")
    print(f"🎯 Lead-tracking intents:")
    for intent in intents:
        print(f"   • {intent['name']} (Priority: {intent.get('priority', 0)})")
        print(f"     Keywords: {', '.join(intent.get('keywords', []))}")

async def main():
    print("="*70)
    print("🎯 LEAD TRACKING TEST")
    print("="*70)
    
    # Get user
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    user_doc = await db.users.find_one({"email": RECIPIENT_EMAIL})
    if not user_doc:
        print("❌ User not found")
        return
    
    user_id = user_doc['id']
    print(f"✅ User: {user_doc['email']} (ID: {user_id})")
    
    # Send test emails that should trigger lead creation
    print(f"\n📧 Sending test emails for lead tracking...")
    
    test_emails = [
        {
            "subject": "Interested in pricing for your product",
            "body": """Hi there,

I'm John Smith from Acme Corp and I'm interested in learning more about your pricing plans.

We're a team of 50 people looking for an email automation solution. Can you provide details about your Enterprise pricing?

Best regards,
John Smith
VP of Sales, Acme Corp
john.smith@acmecorp.com
+1-555-0123"""
        },
        {
            "subject": "Request for product demo",
            "body": """Hello,

I'd like to schedule a demo of your product. We're evaluating different email automation tools for our company.

Company: TechStartup Inc
My name: Sarah Johnson
Role: CTO
Phone: +1-555-9876

Looking forward to seeing what you can do!

Thanks,
Sarah"""
        }
    ]
    
    for test_email in test_emails:
        send_test_email(test_email['subject'], test_email['body'])
        time.sleep(2)
    
    print(f"\n⏳ Waiting 90 seconds for processing...")
    await asyncio.sleep(90)
    
    print(f"\n📊 Checking results...")
    await check_leads_after_test(user_id)
    
    print(f"\n{'='*70}")
    print("✅ Test Complete")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
