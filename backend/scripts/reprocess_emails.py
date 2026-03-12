#!/usr/bin/env python3
"""
Reprocess emails that failed or have no intent detected
"""
from pymongo import MongoClient
from datetime import datetime, timezone

client = MongoClient("mongodb://localhost:27017")
db = client["email_assistant_db"]

user = db.users.find_one({"email": "amits.joys@gmail.com"})
if not user:
    print("❌ User not found!")
    exit(1)

user_id = user.get('id')
print(f"✅ Found user: {user['email']}\n")

# Find emails to reprocess
query = {
    "user_id": user_id,
    "$or": [
        {"status": "error"},
        {"intent_id": None},
        {"intent_id": {"$exists": False}}
    ]
}

emails_to_reprocess = list(db.emails.find(query))
print(f"📧 Found {len(emails_to_reprocess)} emails to reprocess\n")

if not emails_to_reprocess:
    print("✅ No emails need reprocessing!")
    exit(0)

# Reset emails to 'received' status
count = 0
for email in emails_to_reprocess:
    print(f"  - {email.get('subject', 'No subject')[:60]}...")
    
    update = {
        "$set": {
            "status": "received",
            "error_message": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        "$push": {
            "action_history": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "reset_for_reprocessing",
                "details": {"reason": "Intents added after initial processing"},
                "status": "success"
            }
        }
    }
    
    db.emails.update_one({"id": email['id']}, update)
    count += 1

print(f"\n✅ Reset {count} emails to 'received' status")
print("   Worker will reprocess them in next poll (~60 seconds)")

client.close()
