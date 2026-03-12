"""
Create unique index on inbound_leads collection to prevent duplicates
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

async def create_unique_index():
    """Create unique compound index on user_id + lead_email"""
    
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    try:
        # Create unique compound index
        result = await db.inbound_leads.create_index(
            [("user_id", 1), ("lead_email", 1)],
            unique=True,
            name="unique_user_lead_email"
        )
        
        print(f"✓ Created unique index: {result}")
        
        # List all indexes to verify
        indexes = await db.inbound_leads.list_indexes().to_list(100)
        print("\n✓ All indexes on inbound_leads:")
        for idx in indexes:
            print(f"  - {idx['name']}: {idx.get('key', {})}")
        
        print("\n✓ Index creation complete. This will prevent duplicate leads for same email.")
        
    except Exception as e:
        if "duplicate" in str(e).lower():
            print(f"⚠️ Index already exists or found duplicates: {e}")
            print("\n💡 Cleaning up duplicates first...")
            await cleanup_duplicates(db)
        else:
            print(f"✗ Error creating index: {e}")
    finally:
        client.close()

async def cleanup_duplicates(db):
    """Remove duplicate leads, keeping only the oldest one"""
    
    try:
        print("\nSearching for duplicate leads...")
        
        # Find duplicates using aggregation
        pipeline = [
            {
                "$group": {
                    "_id": {"user_id": "$user_id", "lead_email": "$lead_email"},
                    "count": {"$sum": 1},
                    "ids": {"$push": "$id"},
                    "created_ats": {"$push": "$created_at"}
                }
            },
            {
                "$match": {"count": {"$gt": 1}}
            }
        ]
        
        duplicates = await db.inbound_leads.aggregate(pipeline).to_list(1000)
        
        if not duplicates:
            print("✓ No duplicates found!")
            return
        
        print(f"\n⚠️ Found {len(duplicates)} duplicate email groups")
        
        total_removed = 0
        for dup in duplicates:
            user_id = dup['_id']['user_id']
            lead_email = dup['_id']['lead_email']
            ids = dup['ids']
            
            print(f"\n  Email: {lead_email}")
            print(f"  Found {len(ids)} duplicates")
            
            # Get all leads for this email
            leads = await db.inbound_leads.find({
                "user_id": user_id,
                "lead_email": lead_email
            }).sort("created_at", 1).to_list(100)
            
            # Keep the first one (oldest), delete the rest
            keep_lead = leads[0]
            to_delete = [l['id'] for l in leads[1:]]
            
            print(f"  Keeping: {keep_lead['id']} (created: {keep_lead.get('created_at', 'N/A')})")
            print(f"  Deleting: {len(to_delete)} duplicates")
            
            # Delete duplicates
            result = await db.inbound_leads.delete_many({
                "id": {"$in": to_delete}
            })
            
            total_removed += result.deleted_count
        
        print(f"\n✓ Cleanup complete! Removed {total_removed} duplicate leads")
        
        # Now try creating the index again
        print("\nCreating unique index after cleanup...")
        result = await db.inbound_leads.create_index(
            [("user_id", 1), ("lead_email", 1)],
            unique=True,
            name="unique_user_lead_email"
        )
        print(f"✓ Unique index created: {result}")
        
    except Exception as e:
        print(f"✗ Error during cleanup: {e}")

if __name__ == "__main__":
    asyncio.run(create_unique_index())
