"""Check draft content to see if event details are being sent"""

import asyncio
import sys
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from config import config

async def check_drafts():
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    # Get recent emails
    emails = await db.emails.find({
        "from_email": "rohushanshinde@gmail.com"
    }).sort("received_at", -1).limit(10).to_list(10)
    
    print("="*80)
    print("📧 DRAFT CONTENT ANALYSIS")
    print("="*80)
    
    for email in emails:
        print(f"\n{'='*80}")
        print(f"📨 Subject: {email['subject']}")
        print(f"Meeting Detected: {email.get('meeting_detected', False)}")
        print(f"Has calendar_event in data: {'calendar_event' in email}")
        
        if email.get('draft_content'):
            draft = email['draft_content']
            print(f"\n📝 DRAFT CONTENT ({len(draft)} chars):")
            print("-"*80)
            print(draft)
            print("-"*80)
            
            # Check if draft contains event details
            has_meet_link = 'meet.google.com' in draft.lower() or 'google meet' in draft.lower()
            has_calendar_link = 'calendar.google.com' in draft.lower()
            has_event_time = any(word in draft.lower() for word in ['scheduled', 'meeting time', 'at 2 pm', 'at 3 pm'])
            
            print(f"\n🔍 ANALYSIS:")
            print(f"   Contains Meet link: {has_meet_link}")
            print(f"   Contains Calendar link: {has_calendar_link}")
            print(f"   Contains event time details: {has_event_time}")
            
            # Critical check: If no calendar event was created but draft has event details
            if not email.get('calendar_event') and (has_meet_link or has_calendar_link):
                print(f"   ⚠️  WARNING: Draft contains event details but no calendar event was created!")
            elif email.get('calendar_event') and (has_meet_link or has_calendar_link):
                print(f"   ✅ GOOD: Calendar event exists and details included in draft")
            elif email.get('calendar_event') and not (has_meet_link or has_calendar_link):
                print(f"   ⚠️  WARNING: Calendar event exists but details NOT included in draft!")
            else:
                print(f"   ℹ️  No calendar event - draft is a general response")
        else:
            print(f"\n📝 No draft content found")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    asyncio.run(check_drafts())
