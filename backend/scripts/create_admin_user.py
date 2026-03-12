"""Script to create an admin user with known credentials"""
import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone
import uuid

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin_user():
    """Create an admin user with known credentials"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    # Admin credentials
    admin_email = "admin@emailassistant.com"
    admin_password = "Admin@123"
    admin_name = "Admin User"
    
    # Check if admin already exists
    existing = await db.users.find_one({"email": admin_email})
    if existing:
        print(f"✓ Admin user already exists: {admin_email}")
        print(f"  Email: {admin_email}")
        print(f"  Password: {admin_password}")
        return
    
    # Create admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "email": admin_email,
        "password_hash": pwd_context.hash(admin_password),
        "full_name": admin_name,
        "quota": 1000,  # Higher quota for admin
        "quota_used": 0,
        "quota_reset_date": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "role": "admin",
        "is_active": True,
        "hubspot_enabled": True,  # Admin has HubSpot access
        "hubspot_connected": False,
        "hubspot_access_token": None,
        "hubspot_refresh_token": None,
        "hubspot_token_expires_at": None,
        "hubspot_portal_id": None,
        "hubspot_auto_sync": False
    }
    
    await db.users.insert_one(admin_user)
    
    print("=" * 60)
    print("✓ Admin user created successfully!")
    print("=" * 60)
    print(f"Email: {admin_email}")
    print(f"Password: {admin_password}")
    print(f"Role: admin")
    print(f"Quota: 1000 emails/day")
    print("=" * 60)
    print("\nYou can now login with these credentials:")
    print(f"  Email: {admin_email}")
    print(f"  Password: {admin_password}")
    print("=" * 60)
    
    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())
