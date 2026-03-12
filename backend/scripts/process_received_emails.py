#!/usr/bin/env python3
"""
Manually process emails that are stuck in 'received' status
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from motor.motor_asyncio import AsyncIOMotorClient
from config import config

async def process_received_emails():
    """Process all emails in 'received' status"""
    
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    # Import the process_email function from worker
    from workers.email_worker import process_email
    
    # Find user
    user = await db.users.find_one({"email": "amits.joys@gmail.com"})
    if not user:
        print("❌ User not found!")
        return
    
    user_id = user.get('id')
    print(f"✅ Found user: {user['email']}\n")
    
    # Find emails in 'received' status
    emails = await db.emails.find({
        "user_id": user_id,
        "status": "received"
    }).to_list(100)
    
    print(f"📧 Found {len(emails)} emails in 'received' status\n")
    
    if not emails:
        print("✅ No emails to process!")
        return
    
    # Process each email
    processed = 0
    errors = 0
    
    for email in emails:
        try:
            print(f"Processing: {email.get('subject', 'No subject')[:60]}...")
            await process_email(email['id'])
            processed += 1
            # Small delay to avoid rate limiting
            await asyncio.sleep(2)
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
            errors += 1
    
    print(f"\n" + "="*70)
    print(f"✅ Processed: {processed}")
    print(f"❌ Errors: {errors}")
    print("="*70)
    
    # Show final status
    all_emails = await db.emails.find({"user_id": user_id}).to_list(100)
    
    from collections import Counter
    statuses = Counter([e.get('status', 'unknown') for e in all_emails])
    print(f"\nFinal Status Breakdown:")
    for status, count in statuses.most_common():
        print(f"  {status}: {count}")
    
    # Check intents
    intents = [e.get('intent_name') for e in all_emails if e.get('intent_name')]
    print(f"\nIntents Detected: {len(intents)}/{len(all_emails)}")
    if intents:
        intent_counts = Counter(intents)
        for intent, count in intent_counts.most_common():
            print(f"  {intent}: {count}")
    
    # Check leads
    leads = await db.inbound_leads.find({"user_id": user_id}).to_list(100)
    print(f"\nInbound Leads Created: {len(leads)}")
    if leads:
        for lead in leads[:5]:
            print(f"  - {lead.get('lead_email')} ({lead.get('intent_name', 'N/A')})")
    
    client.close()

if __name__ == "__main__":
    print("="*70)
    print("MANUAL EMAIL PROCESSING")
    print("="*70 + "\n")
    
    try:
        asyncio.run(process_received_emails())
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
