"""
Test lead tracking with improved intent classification
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

async def check_latest_emails_and_leads(user_id):
    """Check latest processing results"""
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    # Check latest emails
    emails = await db.emails.find({
        "user_id": user_id,
        "from_email": TEST_EMAIL
    }).sort("received_at", -1).limit(3).to_list(3)
    
    print(f"\n{'='*80}")
    print(f"📧 LATEST EMAILS ({len(emails)} found)")
    print("="*80)
    
    for email in emails:
        print(f"\n📨 {email['subject']}")
        print(f"   Intent: {email.get('intent_name', 'N/A')} (Confidence: {email.get('intent_confidence', 'N/A')})")
        print(f"   Processed: {email.get('processed', False)}")
        
        # Check for lead actions
        if email.get('action_history'):
            lead_actions = [a for a in email['action_history'] if 'lead' in a['action'].lower()]
            if lead_actions:
                print(f"   🎯 Lead Actions Found:")
                for action in lead_actions:
                    print(f"      • {action['action']} - {action.get('status', 'N/A')}")
                    if 'lead_id' in action.get('details', {}):
                        print(f"        Lead ID: {action['details']['lead_id']}")
            else:
                print(f"   ℹ️  No lead actions")
    
    # Check all leads
    leads = await db.inbound_leads.find({
        "user_id": user_id
    }).sort("created_at", -1).to_list(10)
    
    print(f"\n{'='*80}")
    print(f"🎯 ALL LEADS IN SYSTEM: {len(leads)}")
    print("="*80)
    
    if leads:
        for i, lead in enumerate(leads, 1):
            print(f"\n{i}. {lead.get('lead_name', 'N/A')} ({lead.get('lead_email', 'N/A')})")
            print(f"   Company: {lead.get('company_name', 'N/A')}")
            print(f"   Stage: {lead.get('stage', 'N/A')} | Score: {lead.get('score', 'N/A')}")
            print(f"   Source: {lead.get('source', 'N/A')}")
            print(f"   Created: {lead.get('created_at', 'N/A')}")
            print(f"   Active: {lead.get('is_active', False)}")
    else:
        print("\n❌ No leads in system")

async def main():
    print("="*80)
    print("🎯 IMPROVED LEAD TRACKING TEST")
    print("="*80)
    
    # Get user
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    user_doc = await db.users.find_one({"email": RECIPIENT_EMAIL})
    if not user_doc:
        print("❌ User not found")
        return
    
    user_id = user_doc['id']
    print(f"✅ User: {user_doc['email']}")
    
    # Check current intents
    intents = await db.intents.find({
        "user_id": user_id,
        "is_inbound_lead": True
    }).to_list(10)
    
    print(f"\n📋 Lead-tracking intents:")
    for intent in intents:
        print(f"   • {intent['name']} (Priority: {intent.get('priority', 0)})")
        print(f"     Keywords: {', '.join(intent.get('keywords', []))}")
    
    # Send more specific test emails
    print(f"\n{'='*80}")
    print("📧 Sending test emails with clear lead indicators...")
    print("="*80)
    
    test_emails = [
        {
            "subject": "Demo request - Email automation platform",
            "body": """Hi,

I would like to see a demo of your email automation platform. We're currently evaluating tools for our sales team.

Name: Mike Chen
Company: FastGrow Systems
Role: Head of Sales Operations
Email: mike@fastgrow.io
Phone: +1-555-4321

Can you show me a demo this week?

Thanks,
Mike"""
        },
        {
            "subject": "Question about pricing and plans",
            "body": """Hello,

Our company is interested in your email solution. Can you provide pricing information for enterprise plans?

We have around 100 users.

Company: BigTech Solutions  
Contact: Lisa Anderson
Title: Procurement Manager
Email: lisa@bigtech.com

Best regards,
Lisa"""
        }
    ]
    
    for test_email in test_emails:
        send_test_email(test_email['subject'], test_email['body'])
        time.sleep(3)
    
    print(f"\n⏳ Waiting 90 seconds for processing...")
    await asyncio.sleep(90)
    
    print(f"\n📊 Checking results...")
    await check_latest_emails_and_leads(user_id)
    
    print(f"\n{'='*80}")
    print("✅ Test Complete")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
