"""Analyze why specific emails matched specific intents"""

import asyncio
import sys
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from config import config

async def analyze_intent_matching():
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    # Get user
    user_doc = await db.users.find_one({"email": "amits.joys@gmail.com"})
    user_id = user_doc['id']
    
    # Get the problematic email
    email = await db.emails.find_one({
        "user_id": user_id,
        "subject": "Question about pricing and plans"
    })
    
    if not email:
        print("Email not found")
        return
    
    print("="*80)
    print("📧 EMAIL ANALYSIS")
    print("="*80)
    print(f"\nSubject: {email['subject']}")
    print(f"Body:\n{email['body'][:300]}...")
    
    # Create combined text
    email_text = f"{email['subject']} {email['body']}".lower()
    print(f"\n{'='*80}")
    print("🔍 KEYWORD MATCHING ANALYSIS")
    print("="*80)
    
    # Get all intents
    intents = await db.intents.find({
        "user_id": user_id,
        "is_active": True
    }).sort("priority", -1).to_list(100)
    
    # Analyze each intent
    for intent_doc in intents:
        if intent_doc.get('is_default'):
            continue
        
        matched = []
        for keyword in intent_doc.get('keywords', []):
            if keyword.lower() in email_text:
                matched.append(keyword)
        
        if matched:
            lead_flag = "🎯" if intent_doc.get('is_inbound_lead', False) else "  "
            print(f"\n{lead_flag} {intent_doc['name']} (Priority: {intent_doc.get('priority', 0)})")
            print(f"   Matched {len(matched)} keywords: {', '.join(matched)}")
    
    print(f"\n{'='*80}")
    print("💡 RECOMMENDATION")
    print("="*80)
    print("\nTo improve intent matching for lead tracking:")
    print("1. Remove broad keywords from General Inquiry (question, interested)")
    print("2. OR increase specificity by checking subject line separately")
    print("3. OR boost priority of lead-tracking intents")
    print("4. OR use more specific keywords in lead intents")

if __name__ == "__main__":
    asyncio.run(analyze_intent_matching())
