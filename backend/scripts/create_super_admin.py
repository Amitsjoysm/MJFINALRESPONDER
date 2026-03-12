"""
Create Super Admin User
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from models.user import User
from datetime import datetime, timezone
import bcrypt
import uuid

async def create_super_admin():
    """Create a super admin user"""
    
    # Database connection
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "email_assistant_db")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Super admin credentials
    admin_email = "admin@crm.com"
    admin_password = "Admin@123"
    
    # Check if admin already exists
    existing_admin = await db.users.find_one({"email": admin_email})
    if existing_admin:
        print(f"✅ Super admin already exists: {admin_email}")
        print(f"   Password: {admin_password}")
        client.close()
        return
    
    # Hash password
    password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create super admin user
    admin_id = str(uuid.uuid4())
    admin_data = {
        "id": admin_id,  # UUID for JWT token
        "email": admin_email,
        "password_hash": password_hash,
        "full_name": "Super Admin",
        "quota": 10000,  # High quota for admin
        "quota_used": 0,
        "quota_reset_date": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "role": "super_admin",  # Super admin role
        "is_active": True
    }
    
    # Insert user
    result = await db.users.insert_one(admin_data)
    admin_data['_id'] = result.inserted_id
    
    print("=" * 60)
    print("✅ SUPER ADMIN USER CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"📧 Email: {admin_email}")
    print(f"🔑 Password: {admin_password}")
    print(f"👤 Role: super_admin")
    print(f"🆔 User ID: {admin_id}")
    print("=" * 60)
    print("\n⚠️  IMPORTANT: Save these credentials securely!")
    print("   These are the only credentials with admin privileges.\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_super_admin())
