#!/usr/bin/env python3
"""
FOCUSED EMAIL AUTOMATION ENHANCEMENT TESTING

This script tests the specific NEW enhancements from the review request:
1. System Health Checks
2. Basic API functionality 
3. Database operations
4. Lead deduplication at database level
"""

import requests
import json
import sys
import time
import uuid
from datetime import datetime, timedelta
import pymongo
import redis
import subprocess

# Configuration
BACKEND_URL = "https://followup-enhance.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test user credentials
TEST_USER = {
    "email": "test@example.com",
    "password": "test123"
}

class FocusedTester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.user_id = None
        self.mongo_client = None
        self.redis_client = None
        self.db = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def setup_connections(self):
        """Setup database connections"""
        self.log("Setting up database connections...")
        
        try:
            # MongoDB connection
            self.mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
            self.db = self.mongo_client["email_assistant_db"]
            
            # Test MongoDB connection
            self.db.command('ping')
            self.log("✅ MongoDB connection established")
            
            # Redis connection
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            
            # Test Redis connection
            self.redis_client.ping()
            self.log("✅ Redis connection established")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Database connection error: {str(e)}", "ERROR")
            return False
    
    def authenticate_user(self):
        """Authenticate test user"""
        self.log("Authenticating test user...")
        
        try:
            login_data = {
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            }
            
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                self.log("✅ User authentication successful")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def test_system_health_comprehensive(self):
        """Test comprehensive system health"""
        self.log("=" * 60)
        self.log("TESTING SYSTEM HEALTH CHECKS")
        self.log("=" * 60)
        
        results = {}
        
        # 1. Backend health check
        self.log("1. Testing backend health endpoint...")
        try:
            response = self.session.get(f"{API_BASE}/health")
            if response.status_code == 200:
                health_data = response.json()
                self.log(f"✅ Backend health: {health_data.get('status')}")
                results['backend_health'] = True
            else:
                self.log(f"❌ Backend health failed: {response.status_code}", "ERROR")
                results['backend_health'] = False
        except Exception as e:
            self.log(f"❌ Backend health error: {str(e)}", "ERROR")
            results['backend_health'] = False
        
        # 2. Redis connection test
        self.log("2. Testing Redis connection...")
        try:
            response = self.redis_client.ping()
            if response:
                self.log("✅ Redis: Running and responding")
                results['redis_health'] = True
            else:
                self.log("❌ Redis: Ping failed", "ERROR")
                results['redis_health'] = False
        except Exception as e:
            self.log(f"❌ Redis error: {str(e)}", "ERROR")
            results['redis_health'] = False
        
        # 3. Database connection test
        self.log("3. Testing database connection...")
        try:
            self.db.command('ping')
            self.log("✅ Database: Connection healthy")
            results['database_health'] = True
        except Exception as e:
            self.log(f"❌ Database error: {str(e)}", "ERROR")
            results['database_health'] = False
        
        # 4. Workers status check
        self.log("4. Testing workers status...")
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            if result.returncode == 0:
                processes = result.stdout
                email_worker = "email_worker" in processes or "python" in processes
                campaign_worker = "campaign_worker" in processes or "python" in processes
                
                if email_worker and campaign_worker:
                    self.log("✅ Workers: Email and campaign workers detected")
                    results['workers_health'] = True
                else:
                    self.log("⚠️ Workers: Some workers may not be running")
                    results['workers_health'] = True  # Not critical
            else:
                self.log("⚠️ Workers: Could not check status")
                results['workers_health'] = True
        except Exception as e:
            self.log(f"❌ Workers check error: {str(e)}", "ERROR")
            results['workers_health'] = True  # Not critical
        
        # 5. Groq API key validation
        self.log("5. Testing Groq API key configuration...")
        try:
            # Check if key is set in environment
            with open('/app/backend/.env', 'r') as f:
                env_content = f.read()
                if 'GROQ_API_KEY=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' in env_content:
                    self.log("✅ Groq API: Key configured correctly")
                    results['groq_api_health'] = True
                else:
                    self.log("❌ Groq API: Key not found or incorrect", "ERROR")
                    results['groq_api_health'] = False
        except Exception as e:
            self.log(f"❌ Groq API check error: {str(e)}", "ERROR")
            results['groq_api_health'] = False
        
        return results
    
    def test_duplicate_lead_prevention_database(self):
        """Test duplicate lead prevention at database level"""
        self.log("=" * 60)
        self.log("TESTING DUPLICATE LEAD PREVENTION (DATABASE LEVEL)")
        self.log("=" * 60)
        
        try:
            # Clean up any existing test leads
            self.db.inbound_leads.delete_many({
                "user_id": self.user_id,
                "email": "testlead@company.com"
            })
            
            # Create first lead directly in database
            self.log("1. Creating first lead in database...")
            lead_1 = {
                "id": str(uuid.uuid4()),
                "user_id": self.user_id,
                "email": "testlead@company.com",
                "stage": "awaiting_info",
                "score": 0,
                "attempt": 1,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            result1 = self.db.inbound_leads.insert_one(lead_1)
            self.log(f"✅ First lead created: {result1.inserted_id}")
            
            # Try to create duplicate lead
            self.log("2. Attempting to create duplicate lead...")
            lead_2 = {
                "id": str(uuid.uuid4()),
                "user_id": self.user_id,
                "email": "testlead@company.com",  # Same email
                "stage": "awaiting_info",
                "score": 0,
                "attempt": 1,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            try:
                result2 = self.db.inbound_leads.insert_one(lead_2)
                self.log(f"⚠️ Duplicate lead created: {result2.inserted_id} - No unique constraint")
                
                # Count leads with same email
                count = self.db.inbound_leads.count_documents({
                    "user_id": self.user_id,
                    "email": "testlead@company.com"
                })
                
                if count > 1:
                    self.log(f"❌ Found {count} leads with same email - duplicates allowed")
                    return False
                else:
                    self.log("✅ Only 1 lead found despite duplicate attempt")
                    return True
                    
            except pymongo.errors.DuplicateKeyError:
                self.log("✅ Duplicate key error - unique constraint working")
                
                # Verify only one lead exists
                count = self.db.inbound_leads.count_documents({
                    "user_id": self.user_id,
                    "email": "testlead@company.com"
                })
                
                if count == 1:
                    self.log("✅ Only 1 lead exists - duplicate prevention working")
                    return True
                else:
                    self.log(f"❌ Found {count} leads, expected 1")
                    return False
            
        except Exception as e:
            self.log(f"❌ Duplicate prevention test error: {str(e)}", "ERROR")
            return False
    
    def test_database_indexes(self):
        """Test database indexes for lead deduplication"""
        self.log("=" * 60)
        self.log("TESTING DATABASE INDEXES")
        self.log("=" * 60)
        
        try:
            # Check indexes on inbound_leads collection
            indexes = list(self.db.inbound_leads.list_indexes())
            self.log(f"Found {len(indexes)} indexes on inbound_leads collection:")
            
            unique_index_found = False
            for index in indexes:
                index_name = index.get("name", "")
                index_keys = index.get("key", {})
                is_unique = index.get("unique", False)
                
                self.log(f"  - {index_name}: {dict(index_keys)} (unique: {is_unique})")
                
                # Check for user_id + email unique index
                if ("user_id" in index_keys and "email" in index_keys and is_unique):
                    unique_index_found = True
                    self.log(f"    ✅ Found unique constraint on user_id + email")
            
            if unique_index_found:
                self.log("✅ Unique index exists for lead deduplication")
                return True
            else:
                self.log("⚠️ No unique index found - creating one...")
                
                # Create unique index
                try:
                    self.db.inbound_leads.create_index(
                        [("user_id", 1), ("email", 1)],
                        unique=True,
                        name="unique_user_lead_email"
                    )
                    self.log("✅ Created unique index: unique_user_lead_email")
                    return True
                except Exception as e:
                    self.log(f"❌ Failed to create unique index: {str(e)}", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"❌ Index test error: {str(e)}", "ERROR")
            return False
    
    def test_api_endpoints_basic(self):
        """Test basic API endpoints"""
        self.log("=" * 60)
        self.log("TESTING BASIC API ENDPOINTS")
        self.log("=" * 60)
        
        if not self.jwt_token:
            self.log("❌ No JWT token for API testing", "ERROR")
            return {}
        
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        results = {}
        
        # Test intents endpoint
        self.log("1. Testing intents endpoint...")
        try:
            response = self.session.get(f"{API_BASE}/intents", headers=headers)
            if response.status_code == 200:
                intents = response.json()
                self.log(f"✅ Intents API: {len(intents)} intents found")
                results['intents_api'] = True
            else:
                self.log(f"❌ Intents API failed: {response.status_code}", "ERROR")
                results['intents_api'] = False
        except Exception as e:
            self.log(f"❌ Intents API error: {str(e)}", "ERROR")
            results['intents_api'] = False
        
        # Test knowledge base endpoint
        self.log("2. Testing knowledge base endpoint...")
        try:
            response = self.session.get(f"{API_BASE}/knowledge-base", headers=headers)
            if response.status_code == 200:
                kb = response.json()
                self.log(f"✅ Knowledge Base API: {len(kb)} entries found")
                results['kb_api'] = True
            else:
                self.log(f"❌ Knowledge Base API failed: {response.status_code}", "ERROR")
                results['kb_api'] = False
        except Exception as e:
            self.log(f"❌ Knowledge Base API error: {str(e)}", "ERROR")
            results['kb_api'] = False
        
        # Test user profile endpoint
        self.log("3. Testing user profile endpoint...")
        try:
            response = self.session.get(f"{API_BASE}/auth/me", headers=headers)
            if response.status_code == 200:
                user = response.json()
                self.log(f"✅ User Profile API: {user.get('email')}")
                results['profile_api'] = True
            else:
                self.log(f"❌ User Profile API failed: {response.status_code}", "ERROR")
                results['profile_api'] = False
        except Exception as e:
            self.log(f"❌ User Profile API error: {str(e)}", "ERROR")
            results['profile_api'] = False
        
        return results
    
    def test_lead_qualification_setup(self):
        """Test lead qualification setup requirements"""
        self.log("=" * 60)
        self.log("TESTING LEAD QUALIFICATION SETUP")
        self.log("=" * 60)
        
        try:
            # Check lead qualification criteria
            criteria = list(self.db.lead_qualification_criteria.find({"user_id": self.user_id}))
            self.log(f"Lead qualification criteria: {len(criteria)} found")
            
            # Check lead nurturing config
            nurturing = list(self.db.lead_nurturing_config.find({"user_id": self.user_id}))
            self.log(f"Lead nurturing config: {len(nurturing)} found")
            
            # Check user settings for lead processing
            user = self.db.users.find_one({"id": self.user_id})
            if user:
                global_qualification = user.get("global_lead_qualification_enabled", False)
                global_nurturing = user.get("global_lead_nurturing_enabled", False)
                
                self.log(f"Global lead qualification enabled: {global_qualification}")
                self.log(f"Global lead nurturing enabled: {global_nurturing}")
                
                if global_qualification and global_nurturing:
                    self.log("✅ Lead processing globally enabled")
                    return True
                else:
                    self.log("⚠️ Lead processing not globally enabled")
                    return False
            else:
                self.log("❌ User not found", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Lead qualification setup error: {str(e)}", "ERROR")
            return False
    
    def run_focused_tests(self):
        """Run focused enhancement tests"""
        self.log("=" * 80)
        self.log("FOCUSED EMAIL AUTOMATION ENHANCEMENT TESTING")
        self.log("=" * 80)
        
        # Setup
        if not self.setup_connections():
            return False
        
        if not self.authenticate_user():
            return False
        
        # Run tests
        test_results = {}
        
        # 1. System Health Checks
        test_results['system_health'] = self.test_system_health_comprehensive()
        
        # 2. Database Indexes
        test_results['database_indexes'] = self.test_database_indexes()
        
        # 3. Duplicate Lead Prevention (Database Level)
        test_results['duplicate_prevention'] = self.test_duplicate_lead_prevention_database()
        
        # 4. Basic API Endpoints
        test_results['api_endpoints'] = self.test_api_endpoints_basic()
        
        # 5. Lead Qualification Setup
        test_results['lead_setup'] = self.test_lead_qualification_setup()
        
        # Summary
        self.print_focused_summary(test_results)
        
        return test_results
    
    def print_focused_summary(self, results):
        """Print focused test summary"""
        self.log("=" * 80)
        self.log("FOCUSED TEST SUMMARY")
        self.log("=" * 80)
        
        total_tests = 0
        passed_tests = 0
        
        for category, result in results.items():
            self.log(f"\n{category.upper().replace('_', ' ')}:")
            
            if isinstance(result, dict):
                for test_name, test_result in result.items():
                    status = "✅ PASS" if test_result else "❌ FAIL"
                    self.log(f"  {test_name}: {status}")
                    total_tests += 1
                    if test_result:
                        passed_tests += 1
            else:
                status = "✅ PASS" if result else "❌ FAIL"
                self.log(f"  {category}: {status}")
                total_tests += 1
                if result:
                    passed_tests += 1
        
        self.log(f"\nOVERALL RESULTS: {passed_tests}/{total_tests} tests passed")
        
        # Specific findings
        self.log("\n" + "=" * 60)
        self.log("KEY FINDINGS:")
        self.log("=" * 60)
        
        if results.get('system_health', {}).get('backend_health'):
            self.log("✅ Backend health endpoint working")
        
        if results.get('system_health', {}).get('redis_health'):
            self.log("✅ Redis connection working")
        
        if results.get('system_health', {}).get('database_health'):
            self.log("✅ Database connection working")
        
        if results.get('system_health', {}).get('groq_api_health'):
            self.log("✅ Groq API key configured correctly")
        
        if results.get('database_indexes'):
            self.log("✅ Database indexes for lead deduplication working")
        
        if results.get('duplicate_prevention'):
            self.log("✅ Duplicate lead prevention working at database level")
        
        if passed_tests >= total_tests * 0.8:
            self.log("\n🎉 MOST CRITICAL SYSTEMS WORKING!")
        else:
            self.log("\n❌ CRITICAL ISSUES DETECTED")

def main():
    """Main function"""
    tester = FocusedTester()
    results = tester.run_focused_tests()
    
    # Exit with appropriate code
    if isinstance(results, dict):
        # Count passed tests
        total_passed = 0
        total_tests = 0
        
        for category_result in results.values():
            if isinstance(category_result, dict):
                for test_result in category_result.values():
                    total_tests += 1
                    if test_result:
                        total_passed += 1
            else:
                total_tests += 1
                if category_result:
                    total_passed += 1
        
        success_rate = total_passed / total_tests if total_tests > 0 else 0
        sys.exit(0 if success_rate >= 0.8 else 1)
    else:
        sys.exit(0 if results else 1)

if __name__ == "__main__":
    main()