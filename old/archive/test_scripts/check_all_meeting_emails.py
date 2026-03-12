"""Check all emails with meeting_detected=true to see if any have issues"""

import asyncio
import sys
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from config import config

async def check_all_meeting_emails():
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    # Get all emails where meeting was detected
    emails = await db.emails.find({
        "meeting_detected": True
    }).sort("received_at", -1).to_list(100)
    
    print("="*80)
    print(f"🔍 CHECKING ALL EMAILS WITH MEETING DETECTED")
    print(f"Total emails with meeting_detected=True: {len(emails)}")
    print("="*80)
    
    issue_count = 0
    success_count = 0
    
    for email in emails:
        has_calendar_event = 'calendar_event' in email and email['calendar_event'] is not None
        has_draft = email.get('draft_content') is not None
        
        if has_draft:
            draft = email['draft_content']
            has_meet_link = 'meet.google.com' in draft.lower()
            has_calendar_mention = any(word in draft.lower() for word in ['scheduled', 'calendar', 'meeting'])
            
            # Issue: Draft mentions calendar/meeting but no event was created
            if (has_meet_link or has_calendar_mention) and not has_calendar_event:
                issue_count += 1
                print(f"\n❌ ISSUE FOUND:")
                print(f"   Subject: {email['subject']}")
                print(f"   From: {email['from_email']}")
                print(f"   Date: {email['received_at']}")
                print(f"   Meeting Detected: {email.get('meeting_detected', False)}")
                print(f"   Calendar Event Created: {has_calendar_event}")
                print(f"   Draft mentions meeting/calendar: {has_calendar_mention}")
                print(f"   Draft contains Meet link: {has_meet_link}")
                print(f"   Draft excerpt: {draft[:200]}...")
            elif has_calendar_event and (has_meet_link or has_calendar_mention):
                success_count += 1
    
    print(f"\n{'='*80}")
    print(f"📊 SUMMARY:")
    print(f"   ✅ Correct (event created + details in draft): {success_count}")
    print(f"   ❌ Issues (details in draft but no event): {issue_count}")
    print(f"   Total meeting emails: {len(emails)}")
    
    if issue_count == 0:
        print(f"\n🎉 NO ISSUES FOUND! All meeting emails are handled correctly.")
    else:
        print(f"\n⚠️  Found {issue_count} emails with incorrect handling")
    
    print("="*80)

if __name__ == "__main__":
    asyncio.run(check_all_meeting_emails())
