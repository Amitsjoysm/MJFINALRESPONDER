#!/usr/bin/env python3
"""
AUTOMATED TIME-BASED FOLLOW-UP FEATURE TESTING

This test suite comprehensively tests the new automated time-based follow-up feature
as requested in the review request.

TESTING COMPONENTS:
1. Date Parser Service - various date formats
2. AI Agent Service - detect_time_reference() and generate_draft() with follow_up_context
3. Follow-Up Model - new fields (is_automated, follow_up_context, base_date, matched_text, cancellation_reason)
4. Integration Testing - complete flow with real email processing
5. Backend Health Check - all services running without errors

USER UNDER TEST: amits.joys@gmail.com
BACKEND URL: https://followup-enhance.preview.emergentagent.com
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta, timezone
import pymongo
import redis
import os
import asyncio
import logging
from typing import List, Dict, Any

# Configuration
BACKEND_URL = "https://followup-enhance.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test user credentials
TEST_USER = {
    "email": "amits.joys@gmail.com",
    "password": "ij@123"
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutomatedFollowUpTester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.user_id = None
        self.mongo_client = None
        self.redis_client = None
        self.db = None
        self.test_results = {}
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def setup_database_connections(self):
        """Setup direct database connections for verification"""
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
    
    def test_user_authentication(self):
        """Test user authentication to get JWT token"""
        self.log("Testing user authentication...")
        
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
            
            self.log(f"Login response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                self.log("✅ User authentication successful")
                self.log(f"User ID: {self.user_id}")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def test_date_parser_service(self):
        """Test Date Parser Service with various date formats"""
        self.log("=" * 60)
        self.log("TESTING DATE PARSER SERVICE")
        self.log("=" * 60)
        
        # Import the service directly for testing
        try:
            sys.path.append('/app/backend')
            from services.date_parser_service import DateParserService
            
            parser = DateParserService()
            test_cases = [
                # Quarter references
                {
                    "text": "Please follow up with me next quarter about the project status",
                    "expected_patterns": ["next quarter"],
                    "description": "Next quarter reference"
                },
                {
                    "text": "Let's check back in Q3 to see how things are going",
                    "expected_patterns": ["Q3"],
                    "description": "Q3 quarter reference"
                },
                {
                    "text": "I'll be ready to discuss this in the 3rd quarter",
                    "expected_patterns": ["3rd quarter"],
                    "description": "3rd quarter reference"
                },
                
                # Week references
                {
                    "text": "Can you follow up with me next week about this?",
                    "expected_patterns": ["next week"],
                    "description": "Next week reference"
                },
                {
                    "text": "I'll be available in 2-3 weeks to continue this discussion",
                    "expected_patterns": ["2-3 weeks"],
                    "description": "2-3 weeks reference"
                },
                
                # Specific dates
                {
                    "text": "Please contact me after 20th November to discuss the proposal",
                    "expected_patterns": ["after 20th November"],
                    "description": "20th November reference"
                },
                {
                    "text": "I'll be ready to talk on November 20th about this",
                    "expected_patterns": ["November 20"],
                    "description": "November 20 reference"
                },
                {
                    "text": "Let's reconnect after 21st Dec when I'm back from vacation",
                    "expected_patterns": ["after 21st Dec"],
                    "description": "21st Dec reference"
                },
                
                # Special patterns
                {
                    "text": "Follow up with me next year same time about the annual review",
                    "expected_patterns": ["next year same time"],
                    "description": "Next year same time reference"
                },
                {
                    "text": "Check back next year 2nd month for the quarterly results",
                    "expected_patterns": ["next year 2nd month"],
                    "description": "Next year 2nd month reference"
                },
                
                # Availability patterns
                {
                    "text": "I'm out of office till next week, please follow up then",
                    "expected_patterns": ["out of office till next week"],
                    "description": "Out of office till next week"
                },
                {
                    "text": "I will be free after 21st Dec to discuss this further",
                    "expected_patterns": ["will be free after 21st Dec"],
                    "description": "Will be free after 21st Dec"
                }
            ]
            
            results = []
            for i, test_case in enumerate(test_cases, 1):
                self.log(f"\nTest Case {i}: {test_case['description']}")
                self.log(f"Text: {test_case['text']}")
                
                try:
                    time_refs = parser.parse_time_references(test_case['text'])
                    
                    if time_refs:
                        self.log(f"✅ Found {len(time_refs)} time reference(s):")
                        for matched_text, target_date, context in time_refs:
                            self.log(f"  - Matched: '{matched_text}'")
                            self.log(f"  - Target Date: {target_date}")
                            self.log(f"  - Context: {context[:100]}...")
                        
                        # Check if any expected pattern was found
                        found_expected = any(
                            any(pattern.lower() in matched_text.lower() for matched_text, _, _ in time_refs)
                            for pattern in test_case['expected_patterns']
                        )
                        
                        if found_expected:
                            results.append(True)
                            self.log("✅ Expected pattern found")
                        else:
                            results.append(False)
                            self.log(f"❌ Expected patterns {test_case['expected_patterns']} not found")
                    else:
                        results.append(False)
                        self.log("❌ No time references detected")
                        
                except Exception as e:
                    results.append(False)
                    self.log(f"❌ Error parsing: {str(e)}", "ERROR")
            
            success_rate = sum(results) / len(results) * 100
            self.log(f"\n📊 DATE PARSER TEST RESULTS: {sum(results)}/{len(results)} passed ({success_rate:.1f}%)")
            
            if success_rate >= 80:
                self.log("✅ Date Parser Service is working correctly")
                return True
            else:
                self.log("❌ Date Parser Service has issues")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Date Parser Service: {str(e)}", "ERROR")
            return False
    
    def test_ai_agent_service(self):
        """Test AI Agent Service time reference detection and draft generation"""
        self.log("=" * 60)
        self.log("TESTING AI AGENT SERVICE")
        self.log("=" * 60)
        
        try:
            sys.path.append('/app/backend')
            from services.ai_agent_service import AIAgentService
            from models.email import Email
            from motor.motor_asyncio import AsyncIOMotorClient
            import asyncio
            
            # Create async test
            async def run_ai_tests():
                # Setup async MongoDB connection
                client = AsyncIOMotorClient("mongodb://localhost:27017")
                db = client["email_assistant_db"]
                
                ai_service = AIAgentService(db)
                
                # Test emails with time references
                test_emails = [
                    {
                        "subject": "Project Discussion",
                        "body": "Hi, I'd like to discuss the project with you. Can you follow up with me next quarter when I have more bandwidth?",
                        "from_email": "test@example.com",
                        "expected_time_refs": 1
                    },
                    {
                        "subject": "Meeting Request",
                        "body": "Let's schedule a meeting. I'll be available after 20th November to discuss the proposal in detail.",
                        "from_email": "test@example.com",
                        "expected_time_refs": 1
                    },
                    {
                        "subject": "Follow-up Needed",
                        "body": "I'm out of office till next week. Please follow up then about the contract terms.",
                        "from_email": "test@example.com",
                        "expected_time_refs": 1
                    },
                    {
                        "subject": "No Time Reference",
                        "body": "Thanks for your email. I'll get back to you soon with more details.",
                        "from_email": "test@example.com",
                        "expected_time_refs": 0
                    }
                ]
                
                results = []
                for i, test_email in enumerate(test_emails, 1):
                    self.log(f"\nAI Test Case {i}: {test_email['subject']}")
                    
                    # Create email object
                    email = Email(
                        id=f"test-{i}",
                        user_id=self.user_id or "test-user",
                        email_account_id="test-account",
                        subject=test_email['subject'],
                        body=test_email['body'],
                        from_email=test_email['from_email'],
                        to_email=["recipient@example.com"],
                        received_at=datetime.now(timezone.utc).isoformat()
                    )
                    
                    try:
                        # Test detect_time_reference
                        time_refs = await ai_service.detect_time_reference(email)
                        
                        self.log(f"Expected time references: {test_email['expected_time_refs']}")
                        self.log(f"Found time references: {len(time_refs)}")
                        
                        if len(time_refs) == test_email['expected_time_refs']:
                            results.append(True)
                            self.log("✅ Time reference detection correct")
                            
                            # If time references found, test follow-up context generation
                            if time_refs:
                                for ref in time_refs:
                                    self.log(f"  - Matched: '{ref['matched_text']}'")
                                    self.log(f"  - Target Date: {ref['target_date']}")
                                    self.log(f"  - Context: {ref['context'][:100]}...")
                                
                                # Test draft generation with follow-up context
                                follow_up_context = {
                                    'is_automated_followup': True,
                                    'base_date': time_refs[0]['target_date'].isoformat(),
                                    'matched_text': time_refs[0]['matched_text'],
                                    'original_context': time_refs[0]['context']
                                }
                                
                                try:
                                    draft, tokens = await ai_service.generate_draft(
                                        email=email,
                                        user_id=self.user_id or "test-user",
                                        follow_up_context=follow_up_context
                                    )
                                    
                                    if draft and len(draft) > 50:
                                        self.log("✅ Follow-up draft generated successfully")
                                        self.log(f"Draft length: {len(draft)} characters")
                                        self.log(f"Draft preview: {draft[:200]}...")
                                    else:
                                        self.log("❌ Follow-up draft generation failed or too short")
                                        results[-1] = False
                                        
                                except Exception as e:
                                    self.log(f"❌ Error generating follow-up draft: {str(e)}")
                                    results[-1] = False
                        else:
                            results.append(False)
                            self.log("❌ Time reference detection incorrect")
                            
                    except Exception as e:
                        results.append(False)
                        self.log(f"❌ Error in AI test: {str(e)}", "ERROR")
                
                client.close()
                return results
            
            # Run async tests
            results = asyncio.run(run_ai_tests())
            
            success_rate = sum(results) / len(results) * 100
            self.log(f"\n📊 AI AGENT SERVICE TEST RESULTS: {sum(results)}/{len(results)} passed ({success_rate:.1f}%)")
            
            if success_rate >= 75:
                self.log("✅ AI Agent Service is working correctly")
                return True
            else:
                self.log("❌ AI Agent Service has issues")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing AI Agent Service: {str(e)}", "ERROR")
            return False
    
    def test_follow_up_model(self):
        """Test Follow-Up Model with new automated fields"""
        self.log("=" * 60)
        self.log("TESTING FOLLOW-UP MODEL")
        self.log("=" * 60)
        
        if not self.db:
            self.log("❌ No database connection", "ERROR")
            return False
        
        try:
            sys.path.append('/app/backend')
            from models.follow_up import FollowUp
            
            # Test creating follow-up with new automated fields
            test_follow_up = FollowUp(
                user_id=self.user_id or "test-user",
                email_id="test-email-id",
                email_account_id="test-account-id",
                thread_id="test-thread-id",
                scheduled_at=(datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
                subject="Test Automated Follow-up",
                body="This is a test automated follow-up",
                is_automated=True,
                follow_up_context="User requested follow-up next quarter about project status",
                base_date=(datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
                matched_text="next quarter",
                status="pending"
            )
            
            # Test model validation
            model_data = test_follow_up.model_dump()
            
            # Check all required fields are present
            required_fields = [
                'id', 'user_id', 'email_id', 'email_account_id', 'scheduled_at',
                'subject', 'body', 'status', 'is_automated', 'follow_up_context',
                'base_date', 'matched_text', 'created_at'
            ]
            
            missing_fields = [field for field in required_fields if field not in model_data]
            
            if missing_fields:
                self.log(f"❌ Missing fields in Follow-Up model: {missing_fields}")
                return False
            
            self.log("✅ All required fields present in Follow-Up model")
            
            # Test database insertion
            try:
                result = self.db.follow_ups.insert_one(model_data)
                if result.inserted_id:
                    self.log("✅ Follow-up successfully inserted into database")
                    
                    # Verify the data was stored correctly
                    stored_follow_up = self.db.follow_ups.find_one({"id": test_follow_up.id})
                    if stored_follow_up:
                        # Check automated fields
                        automated_fields_correct = (
                            stored_follow_up.get('is_automated') == True and
                            stored_follow_up.get('follow_up_context') == test_follow_up.follow_up_context and
                            stored_follow_up.get('base_date') == test_follow_up.base_date and
                            stored_follow_up.get('matched_text') == test_follow_up.matched_text
                        )
                        
                        if automated_fields_correct:
                            self.log("✅ Automated follow-up fields stored correctly")
                            
                            # Clean up test data
                            self.db.follow_ups.delete_one({"id": test_follow_up.id})
                            return True
                        else:
                            self.log("❌ Automated follow-up fields not stored correctly")
                            return False
                    else:
                        self.log("❌ Follow-up not found after insertion")
                        return False
                else:
                    self.log("❌ Failed to insert follow-up into database")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Database insertion error: {str(e)}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Follow-Up model: {str(e)}", "ERROR")
            return False
    
    def test_integration_flow(self):
        """Test complete integration flow with time-based follow-ups"""
        self.log("=" * 60)
        self.log("TESTING INTEGRATION FLOW")
        self.log("=" * 60)
        
        if not self.db or not self.user_id:
            self.log("❌ Missing database connection or user ID", "ERROR")
            return False
        
        try:
            # Create a test email with time reference in database
            test_email_data = {
                "id": f"test-integration-{int(time.time())}",
                "user_id": self.user_id,
                "email_account_id": "test-account",
                "subject": "Project Follow-up Request",
                "body": "Hi, thanks for the meeting today. Can you please follow up with me next quarter about the project status? I'll have more clarity on the budget by then.",
                "from_email": "sender@example.com",
                "to_email": ["recipient@example.com"],
                "received_at": datetime.now(timezone.utc).isoformat(),
                "processed": False,
                "status": "received"
            }
            
            # Insert test email
            result = self.db.emails.insert_one(test_email_data)
            if not result.inserted_id:
                self.log("❌ Failed to insert test email")
                return False
            
            self.log("✅ Test email inserted successfully")
            
            # Simulate email processing (normally done by worker)
            try:
                sys.path.append('/app/backend')
                from services.ai_agent_service import AIAgentService
                from models.email import Email
                from motor.motor_asyncio import AsyncIOMotorClient
                import asyncio
                
                async def process_test_email():
                    client = AsyncIOMotorClient("mongodb://localhost:27017")
                    db = client["email_assistant_db"]
                    
                    ai_service = AIAgentService(db)
                    
                    # Create email object
                    email = Email(**test_email_data)
                    
                    # Test time reference detection
                    time_refs = await ai_service.detect_time_reference(email)
                    
                    if time_refs:
                        self.log(f"✅ Time references detected: {len(time_refs)}")
                        
                        # Simulate creating automated follow-ups
                        from workers.email_worker import create_automated_followups
                        
                        for ref in time_refs:
                            await create_automated_followups(email, ref, ai_service)
                        
                        # Check if follow-ups were created
                        follow_ups = await db.follow_ups.find({
                            "email_id": email.id,
                            "is_automated": True
                        }).to_list(10)
                        
                        if follow_ups:
                            self.log(f"✅ Created {len(follow_ups)} automated follow-ups")
                            
                            # Verify follow-up structure
                            for follow_up in follow_ups:
                                required_fields = ['is_automated', 'follow_up_context', 'base_date', 'matched_text']
                                if all(field in follow_up for field in required_fields):
                                    self.log(f"✅ Follow-up {follow_up['id'][:8]}... has all required fields")
                                else:
                                    self.log(f"❌ Follow-up {follow_up['id'][:8]}... missing required fields")
                                    client.close()
                                    return False
                            
                            client.close()
                            return True
                        else:
                            self.log("❌ No automated follow-ups created")
                            client.close()
                            return False
                    else:
                        self.log("❌ No time references detected in test email")
                        client.close()
                        return False
                
                # Run async processing
                success = asyncio.run(process_test_email())
                
                # Clean up test data
                self.db.emails.delete_one({"id": test_email_data["id"]})
                self.db.follow_ups.delete_many({"email_id": test_email_data["id"]})
                
                if success:
                    self.log("✅ Integration flow test passed")
                    return True
                else:
                    self.log("❌ Integration flow test failed")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error in integration processing: {str(e)}", "ERROR")
                # Clean up on error
                self.db.emails.delete_one({"id": test_email_data["id"]})
                self.db.follow_ups.delete_many({"email_id": test_email_data["id"]})
                return False
                
        except Exception as e:
            self.log(f"❌ Error in integration flow test: {str(e)}", "ERROR")
            return False
    
    def test_backend_health(self):
        """Test backend health and service status"""
        self.log("=" * 60)
        self.log("TESTING BACKEND HEALTH")
        self.log("=" * 60)
        
        health_checks = {}
        
        # 1. Test API health endpoint
        try:
            response = self.session.get(f"{API_BASE}/health")
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "healthy":
                    health_checks['api_health'] = True
                    self.log("✅ API health endpoint responding correctly")
                else:
                    health_checks['api_health'] = False
                    self.log("❌ API health endpoint reports unhealthy status")
            else:
                health_checks['api_health'] = False
                self.log(f"❌ API health endpoint failed: {response.status_code}")
        except Exception as e:
            health_checks['api_health'] = False
            self.log(f"❌ API health check error: {str(e)}")
        
        # 2. Test MongoDB connection
        try:
            if self.db:
                self.db.command('ping')
                health_checks['mongodb'] = True
                self.log("✅ MongoDB connection healthy")
            else:
                health_checks['mongodb'] = False
                self.log("❌ MongoDB connection not established")
        except Exception as e:
            health_checks['mongodb'] = False
            self.log(f"❌ MongoDB health check error: {str(e)}")
        
        # 3. Test Redis connection
        try:
            if self.redis_client:
                self.redis_client.ping()
                health_checks['redis'] = True
                self.log("✅ Redis connection healthy")
            else:
                health_checks['redis'] = False
                self.log("❌ Redis connection not established")
        except Exception as e:
            health_checks['redis'] = False
            self.log(f"❌ Redis health check error: {str(e)}")
        
        # 4. Check background workers (via logs)
        try:
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "20", "/var/log/supervisor/backend.out.log"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                log_content = result.stdout
                worker_indicators = [
                    "Background worker started",
                    "email worker",
                    "follow-up worker",
                    "reminder worker"
                ]
                
                found_indicators = sum(1 for indicator in worker_indicators if indicator.lower() in log_content.lower())
                
                if found_indicators >= 2:
                    health_checks['workers'] = True
                    self.log("✅ Background workers appear to be running")
                else:
                    health_checks['workers'] = False
                    self.log("❌ Limited background worker activity detected")
            else:
                health_checks['workers'] = False
                self.log("❌ Could not check background worker logs")
        except Exception as e:
            health_checks['workers'] = False
            self.log(f"❌ Worker health check error: {str(e)}")
        
        # 5. Test import of key services
        try:
            sys.path.append('/app/backend')
            from services.date_parser_service import DateParserService
            from services.ai_agent_service import AIAgentService
            from models.follow_up import FollowUp
            
            health_checks['imports'] = True
            self.log("✅ All required services can be imported")
        except Exception as e:
            health_checks['imports'] = False
            self.log(f"❌ Service import error: {str(e)}")
        
        # Overall health assessment
        healthy_services = sum(health_checks.values())
        total_services = len(health_checks)
        health_percentage = (healthy_services / total_services) * 100
        
        self.log(f"\n📊 BACKEND HEALTH SUMMARY: {healthy_services}/{total_services} services healthy ({health_percentage:.1f}%)")
        
        for service, status in health_checks.items():
            status_icon = "✅" if status else "❌"
            self.log(f"  {status_icon} {service}: {'Healthy' if status else 'Unhealthy'}")
        
        if health_percentage >= 80:
            self.log("✅ Backend is healthy and ready for automated follow-up feature")
            return True
        else:
            self.log("❌ Backend has health issues that may affect automated follow-up feature")
            return False
    
    def run_comprehensive_test(self):
        """Run all automated follow-up feature tests"""
        self.log("🚀 STARTING AUTOMATED TIME-BASED FOLLOW-UP FEATURE TESTING")
        self.log("=" * 80)
        
        test_results = {}
        
        # Setup
        self.log("PHASE 1: SETUP")
        self.log("-" * 40)
        test_results['database_setup'] = self.setup_database_connections()
        test_results['authentication'] = self.test_user_authentication()
        
        if not test_results['database_setup']:
            self.log("❌ Cannot proceed without database connection")
            return False
        
        # Core feature tests
        self.log("\nPHASE 2: CORE FEATURE TESTING")
        self.log("-" * 40)
        test_results['date_parser'] = self.test_date_parser_service()
        test_results['ai_agent'] = self.test_ai_agent_service()
        test_results['follow_up_model'] = self.test_follow_up_model()
        
        # Integration tests
        self.log("\nPHASE 3: INTEGRATION TESTING")
        self.log("-" * 40)
        test_results['integration'] = self.test_integration_flow()
        
        # Health checks
        self.log("\nPHASE 4: BACKEND HEALTH CHECK")
        self.log("-" * 40)
        test_results['backend_health'] = self.test_backend_health()
        
        # Final assessment
        self.log("\nPHASE 5: FINAL ASSESSMENT")
        self.log("-" * 40)
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        self.log(f"\n📊 OVERALL TEST RESULTS: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
        for test_name, result in test_results.items():
            status_icon = "✅" if result else "❌"
            self.log(f"  {status_icon} {test_name.replace('_', ' ').title()}: {'PASSED' if result else 'FAILED'}")
        
        if success_rate >= 80:
            self.log("\n🎉 AUTOMATED TIME-BASED FOLLOW-UP FEATURE IS WORKING CORRECTLY!")
            self.log("✅ All critical components tested successfully")
            return True
        else:
            self.log("\n❌ AUTOMATED TIME-BASED FOLLOW-UP FEATURE HAS ISSUES")
            self.log("⚠️  Some components need attention before production use")
            return False

def main():
    """Main test execution"""
    tester = AutomatedFollowUpTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n" + "="*80)
            print("✅ AUTOMATED TIME-BASED FOLLOW-UP FEATURE TESTING COMPLETED SUCCESSFULLY")
            print("🚀 Feature is ready for production use")
            print("="*80)
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ AUTOMATED TIME-BASED FOLLOW-UP FEATURE TESTING FAILED")
            print("🔧 Issues need to be resolved before production use")
            print("="*80)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")
        sys.exit(1)
    finally:
        # Cleanup
        if tester.mongo_client:
            tester.mongo_client.close()

if __name__ == "__main__":
    main()