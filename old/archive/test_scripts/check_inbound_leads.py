"""
Check inbound leads tracking and identify issues
"""

import asyncio
import sys
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from config import config
from datetime import datetime, timezone

async def check_leads_system():
    """Check the entire leads tracking system"""
    
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    print("="*80)
    print("🔍 INBOUND LEADS SYSTEM DIAGNOSTIC")
    print("="*80)
    
    # Get user
    user_doc = await db.users.find_one({"email": "amits.joys@gmail.com"})
    if not user_doc:
        print("❌ User not found")
        return
    
    user_id = user_doc['id']
    print(f"\n✅ User: {user_doc['email']} (ID: {user_id})")
    
    # Check intents with is_inbound_lead flag
    print(f"\n{'='*80}")
    print("📋 CHECKING INTENTS WITH LEAD TRACKING")
    print("="*80)
    
    intents = await db.intents.find({"user_id": user_id}).to_list(100)
    lead_intents = [i for i in intents if i.get('is_inbound_lead', False)]
    
    print(f"\nTotal Intents: {len(intents)}")
    print(f"Lead-Tracking Intents: {len(lead_intents)}")
    
    if lead_intents:
        print(f"\n🎯 INTENTS MARKED FOR LEAD TRACKING:")
        for intent in lead_intents:
            print(f"   • {intent['name']} (Priority: {intent.get('priority', 0)})")
            print(f"     Keywords: {', '.join(intent.get('keywords', [])[:5])}")
            print(f"     Auto-send: {intent.get('auto_send', False)}")
    else:
        print("\n⚠️  NO INTENTS MARKED FOR LEAD TRACKING!")
        print("   This is likely why leads are not being created.")
    
    # Check emails that matched lead intents
    print(f"\n{'='*80}")
    print("📧 CHECKING EMAILS MATCHING LEAD INTENTS")
    print("="*80)
    
    if lead_intents:
        lead_intent_ids = [i['id'] for i in lead_intents]
        emails_with_lead_intents = await db.emails.find({
            "user_id": user_id,
            "intent_detected": {"$in": lead_intent_ids}
        }).to_list(100)
        
        print(f"\nEmails matching lead intents: {len(emails_with_lead_intents)}")
        
        if emails_with_lead_intents:
            print(f"\n📨 RECENT EMAILS WITH LEAD INTENTS:")
            for email in emails_with_lead_intents[:5]:
                print(f"\n   • Subject: {email['subject']}")
                print(f"     From: {email['from_email']}")
                print(f"     Intent: {email.get('intent_name', 'N/A')}")
                print(f"     Date: {email['received_at']}")
                
                # Check action history for lead creation
                if email.get('action_history'):
                    lead_actions = [a for a in email['action_history'] if 'lead' in a['action'].lower()]
                    if lead_actions:
                        print(f"     Lead Actions:")
                        for action in lead_actions:
                            print(f"       - {action['action']} ({action.get('status', 'N/A')})")
                    else:
                        print(f"     ⚠️  NO LEAD ACTIONS in action_history")
    else:
        print("\nSkipping email check (no lead intents configured)")
    
    # Check inbound_leads collection
    print(f"\n{'='*80}")
    print("🎯 CHECKING INBOUND LEADS COLLECTION")
    print("="*80)
    
    leads = await db.inbound_leads.find({"user_id": user_id}).to_list(100)
    print(f"\nTotal Leads in Database: {len(leads)}")
    
    if leads:
        print(f"\n📊 LEAD DETAILS:")
        for lead in leads[:10]:
            print(f"\n   • {lead.get('lead_name', 'N/A')} ({lead.get('lead_email', 'N/A')})")
            print(f"     Company: {lead.get('company_name', 'N/A')}")
            print(f"     Stage: {lead.get('stage', 'N/A')}")
            print(f"     Score: {lead.get('score', 'N/A')}")
            print(f"     Source: {lead.get('source', 'N/A')}")
            print(f"     Created: {lead.get('created_at', 'N/A')}")
            print(f"     Active: {lead.get('is_active', False)}")
    else:
        print("\n❌ NO LEADS FOUND IN DATABASE")
        print("   Leads are not being created from incoming emails")
    
    # Check lead_agent_service existence
    print(f"\n{'='*80}")
    print("🔧 CHECKING LEAD SERVICE IMPLEMENTATION")
    print("="*80)
    
    try:
        from services.lead_agent_service import LeadAgentService
        print("✅ LeadAgentService exists")
        
        # Check if service has required methods
        service = LeadAgentService(db)
        methods = ['is_inbound_lead', 'extract_lead_data', 'create_lead']
        for method in methods:
            if hasattr(service, method):
                print(f"   ✅ Method '{method}' exists")
            else:
                print(f"   ❌ Method '{method}' MISSING")
    except ImportError as e:
        print(f"❌ LeadAgentService NOT FOUND: {e}")
    except Exception as e:
        print(f"⚠️  Error checking service: {e}")
    
    # Check email worker integration
    print(f"\n{'='*80}")
    print("⚙️  CHECKING EMAIL WORKER LEAD INTEGRATION")
    print("="*80)
    
    try:
        with open('/app/backend/workers/email_worker.py', 'r') as f:
            worker_code = f.read()
            
        # Check for lead service import
        has_lead_import = 'from services.lead_agent_service import LeadAgentService' in worker_code
        has_lead_check = 'is_inbound_lead' in worker_code
        has_lead_creation = 'create_lead' in worker_code
        
        print(f"   LeadAgentService imported: {'✅' if has_lead_import else '❌'}")
        print(f"   Lead detection check: {'✅' if has_lead_check else '❌'}")
        print(f"   Lead creation logic: {'✅' if has_lead_creation else '❌'}")
        
    except Exception as e:
        print(f"⚠️  Could not check worker code: {e}")
    
    # Recommendations
    print(f"\n{'='*80}")
    print("💡 DIAGNOSTIC SUMMARY & RECOMMENDATIONS")
    print("="*80)
    
    issues = []
    
    if not lead_intents:
        issues.append("NO intents marked with is_inbound_lead=true")
        print("\n❌ ISSUE 1: No lead-tracking intents configured")
        print("   FIX: Update intents to set is_inbound_lead=true for relevant intents")
        print("   Example: Pricing Request, Demo Request should track leads")
    
    if len(leads) == 0 and len(lead_intents) > 0:
        issues.append("Lead intents exist but no leads created")
        print("\n❌ ISSUE 2: Lead intents configured but no leads being created")
        print("   Possible causes:")
        print("   - LeadAgentService not functioning properly")
        print("   - Email worker not calling lead creation")
        print("   - Lead extraction failing")
    
    if not issues:
        print("\n✅ System appears to be configured correctly")
        print("   Leads should be created when emails match lead intents")
    else:
        print(f"\n⚠️  Found {len(issues)} issue(s) preventing lead tracking")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(check_leads_system())
