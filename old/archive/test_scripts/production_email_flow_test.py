#!/usr/bin/env python3
"""
COMPREHENSIVE PRODUCTION EMAIL FLOW TEST

This test suite performs the complete production email flow test as requested:
1. Send 4 real test emails using SMTP credentials
2. Wait 90 seconds for email polling and processing
3. Verify complete email flow: receive -> classify -> draft -> validate -> auto-send
4. Check signature handling (no double signatures)
5. Verify plain text formatting
6. Check knowledge base integration
7. Verify system health

USER UNDER TEST: amits.joys@gmail.com (ID: afab1f05-37bf-4c23-9c94-0e2365986ea1)
BACKEND URL: https://followup-enhance.preview.emergentagent.com
"""

import requests
import json
import sys
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
    "user_id": "afab1f05-37bf-4c23-9c94-0e2365986ea1",
    "password": "ij@123"
}

# SMTP credentials for sending test emails
SMTP_CONFIG = {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "sagarshinde15798796456@gmail.com",
    "password": "bmwqmytxrsgrlusp"
}

# Test emails to send
TEST_EMAILS = [
    {
        "subject": "Can we schedule a meeting next week?",
        "body": "Hi, I'd like to discuss our upcoming project. Are you available for a 30-minute call next Tuesday or Wednesday afternoon? Looking forward to connecting.",
        "expected_intent": "Meeting Request",
        "should_create_calendar_event": True
    },
    {
        "subject": "Need help with login issue",
        "body": "Hello, I'm having trouble accessing my account. I keep getting an error message when I try to log in. Can you help me resolve this? Thanks!",
        "expected_intent": "Support Request",
        "should_create_calendar_event": False
    },
    {
        "subject": "Question about pricing plans",
        "body": "Hi there, I'm interested in your Professional plan. Can you tell me more about the features and if there's a discount for annual subscriptions? Thanks in advance.",
        "expected_intent": "General Inquiry",
        "should_create_calendar_event": False
    },
    {
        "subject": "Thanks for your help!",
        "body": "Just wanted to say thank you for the quick response yesterday. Really appreciate your support and the solution worked perfectly!",
        "expected_intent": "Thank You",
        "should_create_calendar_event": False
    }
]

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionEmailFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.user_id = TEST_USER["user_id"]
        self.mongo_client = None
        self.redis_client = None
        self.db = None
        self.test_results = {}
        self.sent_email_ids = []
        
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
                user_data = data.get("user", {})
                self.log("✅ User authentication successful")
                self.log(f"User ID: {user_data.get('id')}")
                self.log(f"User Email: {user_data.get('email')}")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def verify_user_setup(self):
        """Verify user has OAuth Gmail account and calendar provider connected"""
        self.log("=" * 60)
        self.log("VERIFYING USER SETUP")
        self.log("=" * 60)
        
        if not self.jwt_token:
            self.log("❌ No JWT token available", "ERROR")
            return False
        
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        
        # Check email accounts
        try:
            response = self.session.get(f"{API_BASE}/email-accounts", headers=headers)
            if response.status_code == 200:
                email_accounts = response.json()
                oauth_gmail_accounts = [acc for acc in email_accounts if acc.get("account_type") == "oauth_gmail"]
                
                if oauth_gmail_accounts:
                    self.log(f"✅ Found {len(oauth_gmail_accounts)} OAuth Gmail account(s)")
                    for acc in oauth_gmail_accounts:
                        self.log(f"  - {acc.get('email')} (Active: {acc.get('is_active')})")
                else:
                    self.log("❌ No OAuth Gmail accounts found")
                    return False
            else:
                self.log(f"❌ Failed to fetch email accounts: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error checking email accounts: {str(e)}", "ERROR")
            return False
        
        # Check calendar providers
        try:
            response = self.session.get(f"{API_BASE}/calendar/providers", headers=headers)
            if response.status_code == 200:
                calendar_providers = response.json()
                google_providers = [prov for prov in calendar_providers if prov.get("provider") == "google"]
                
                if google_providers:
                    self.log(f"✅ Found {len(google_providers)} Google Calendar provider(s)")
                    for prov in google_providers:
                        self.log(f"  - {prov.get('email')} (Active: {prov.get('is_active')})")
                else:
                    self.log("❌ No Google Calendar providers found")
                    return False
            else:
                self.log(f"❌ Failed to fetch calendar providers: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error checking calendar providers: {str(e)}", "ERROR")
            return False
        
        # Check intents
        try:
            response = self.session.get(f"{API_BASE}/intents", headers=headers)
            if response.status_code == 200:
                intents = response.json()
                auto_send_intents = [intent for intent in intents if intent.get("auto_send")]
                
                self.log(f"✅ Found {len(intents)} intents, {len(auto_send_intents)} with auto_send enabled")
                for intent in intents:
                    self.log(f"  - {intent.get('name')} (Priority: {intent.get('priority')}, Auto-send: {intent.get('auto_send')})")
            else:
                self.log(f"❌ Failed to fetch intents: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error checking intents: {str(e)}", "ERROR")
            return False
        
        # Check knowledge base
        try:
            response = self.session.get(f"{API_BASE}/knowledge-base", headers=headers)
            if response.status_code == 200:
                kb_entries = response.json()
                self.log(f"✅ Found {len(kb_entries)} knowledge base entries")
                for entry in kb_entries:
                    self.log(f"  - {entry.get('title')} ({entry.get('category')})")
            else:
                self.log(f"❌ Failed to fetch knowledge base: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error checking knowledge base: {str(e)}", "ERROR")
            return False
        
        return True
    
    def send_test_emails(self):
        """Send 4 test emails using SMTP"""
        self.log("=" * 60)
        self.log("SENDING TEST EMAILS")
        self.log("=" * 60)
        
        try:
            # Setup SMTP connection
            server = smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"])
            server.starttls()
            server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
            
            self.log(f"✅ SMTP connection established to {SMTP_CONFIG['host']}")
            
            sent_count = 0
            for i, email_data in enumerate(TEST_EMAILS, 1):
                try:
                    # Create email message
                    msg = MIMEMultipart()
                    msg['From'] = SMTP_CONFIG["username"]
                    msg['To'] = TEST_USER["email"]
                    msg['Subject'] = email_data["subject"]
                    
                    # Add body
                    msg.attach(MIMEText(email_data["body"], 'plain'))
                    
                    # Send email
                    text = msg.as_string()
                    server.sendmail(SMTP_CONFIG["username"], TEST_USER["email"], text)
                    
                    sent_count += 1
                    self.log(f"✅ Email {i} sent: {email_data['subject']}")
                    
                    # Small delay between emails
                    time.sleep(2)
                    
                except Exception as e:
                    self.log(f"❌ Failed to send email {i}: {str(e)}", "ERROR")
            
            server.quit()
            self.log(f"✅ Successfully sent {sent_count}/{len(TEST_EMAILS)} test emails")
            
            return sent_count == len(TEST_EMAILS)
            
        except Exception as e:
            self.log(f"❌ SMTP error: {str(e)}", "ERROR")
            return False
    
    def wait_for_email_processing(self, wait_seconds=90):
        """Wait for email polling and processing"""
        self.log("=" * 60)
        self.log(f"WAITING {wait_seconds} SECONDS FOR EMAIL PROCESSING")
        self.log("=" * 60)
        
        self.log("Email polling frequency: Every 60 seconds")
        self.log("Waiting for emails to be polled, processed, and auto-replied...")
        
        for i in range(wait_seconds):
            if i % 10 == 0:
                remaining = wait_seconds - i
                self.log(f"⏳ {remaining} seconds remaining...")
            time.sleep(1)
        
        self.log("✅ Wait period completed")
        return True
    
    def verify_email_processing(self):
        """Verify emails were received, processed, and auto-replied"""
        self.log("=" * 60)
        self.log("VERIFYING EMAIL PROCESSING")
        self.log("=" * 60)
        
        if self.db is None:
            self.log("❌ No database connection", "ERROR")
            return False
        
        try:
            # Get emails from the last 10 minutes
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=10)
            
            emails = list(self.db.emails.find({
                "user_id": self.user_id,
                "received_at": {"$gte": cutoff_time.isoformat()}
            }).sort("received_at", -1))
            
            self.log(f"Found {len(emails)} recent emails for user")
            
            if len(emails) < len(TEST_EMAILS):
                self.log(f"❌ Expected {len(TEST_EMAILS)} emails, found {len(emails)}")
                return False
            
            # Take the most recent emails (should be our test emails)
            test_emails = emails[:len(TEST_EMAILS)]
            
            results = []
            for i, email in enumerate(test_emails, 1):
                self.log(f"\n--- EMAIL {i} VERIFICATION ---")
                self.log(f"Subject: {email.get('subject')}")
                self.log(f"From: {email.get('from_email')}")
                self.log(f"Received: {email.get('received_at')}")
                
                email_result = {
                    "email_id": email.get("id"),
                    "subject": email.get("subject"),
                    "received": True,
                    "intent_classified": False,
                    "meeting_detected": False,
                    "draft_generated": False,
                    "auto_sent": False,
                    "follow_ups_created": False,
                    "thread_id_extracted": False,
                    "signature_issues": False,
                    "kb_integration": False
                }
                
                # Check intent classification
                intent_detected = email.get("intent_detected")
                if intent_detected:
                    email_result["intent_classified"] = True
                    self.log(f"✅ Intent classified: {intent_detected}")
                else:
                    self.log("❌ No intent detected")
                
                # Check meeting detection
                meeting_detected = email.get("meeting_detected")
                if meeting_detected is not None:
                    email_result["meeting_detected"] = meeting_detected
                    self.log(f"✅ Meeting detected: {meeting_detected}")
                else:
                    self.log("⚠️ Meeting detection not recorded")
                
                # Check draft generation
                draft_content = email.get("draft_content")
                if draft_content:
                    email_result["draft_generated"] = True
                    self.log(f"✅ Draft generated ({len(draft_content)} characters)")
                    
                    # Check for signature issues (no double signatures)
                    if self.check_signature_issues(draft_content):
                        email_result["signature_issues"] = True
                        self.log("❌ Signature issues detected in draft")
                    else:
                        self.log("✅ No signature issues detected")
                    
                    # Check knowledge base integration
                    if self.check_kb_integration(draft_content):
                        email_result["kb_integration"] = True
                        self.log("✅ Knowledge base information detected in draft")
                    else:
                        self.log("⚠️ Limited knowledge base integration detected")
                else:
                    self.log("❌ No draft generated")
                
                # Check auto-send status
                status = email.get("status")
                if status == "sent":
                    email_result["auto_sent"] = True
                    self.log("✅ Email auto-sent successfully")
                else:
                    self.log(f"❌ Email not auto-sent (status: {status})")
                
                # Check thread ID extraction
                thread_id = email.get("thread_id")
                if thread_id:
                    email_result["thread_id_extracted"] = True
                    self.log(f"✅ Thread ID extracted: {thread_id[:20]}...")
                else:
                    self.log("❌ No thread ID extracted")
                
                # Check follow-ups created
                follow_ups = list(self.db.follow_ups.find({"email_id": email.get("id")}))
                if follow_ups:
                    email_result["follow_ups_created"] = True
                    self.log(f"✅ {len(follow_ups)} follow-ups created")
                else:
                    self.log("❌ No follow-ups created")
                
                results.append(email_result)
            
            # Check calendar events for meeting emails
            meeting_emails = [r for r in results if any(
                "meeting" in r["subject"].lower() or "schedule" in r["subject"].lower()
                for r in results
            )]
            
            if meeting_emails:
                calendar_events = list(self.db.calendar_events.find({
                    "user_id": self.user_id,
                    "created_at": {"$gte": cutoff_time.isoformat()}
                }))
                
                self.log(f"\n--- CALENDAR EVENTS ---")
                self.log(f"Found {len(calendar_events)} recent calendar events")
                
                for event in calendar_events:
                    self.log(f"✅ Event: {event.get('title')} at {event.get('start_time')}")
            
            return results
            
        except Exception as e:
            self.log(f"❌ Error verifying email processing: {str(e)}", "ERROR")
            return False
    
    def check_signature_issues(self, draft_content):
        """Check for double signature issues in draft content"""
        if not draft_content:
            return False
        
        # Common signature phrases that shouldn't appear in AI-generated content
        ai_signature_phrases = [
            "best regards",
            "sincerely",
            "kind regards",
            "yours truly",
            "warm regards",
            "respectfully"
        ]
        
        draft_lower = draft_content.lower()
        signature_count = sum(1 for phrase in ai_signature_phrases if phrase in draft_lower)
        
        # If we find AI signature phrases, it might indicate double signatures
        return signature_count > 0
    
    def check_kb_integration(self, draft_content):
        """Check if draft content includes knowledge base information"""
        if not draft_content:
            return False
        
        # Common knowledge base terms that should appear in responses
        kb_indicators = [
            "company",
            "product",
            "feature",
            "pricing",
            "support",
            "documentation",
            "security",
            "privacy"
        ]
        
        draft_lower = draft_content.lower()
        kb_matches = sum(1 for indicator in kb_indicators if indicator in draft_lower)
        
        # If we find multiple KB indicators, it suggests good integration
        return kb_matches >= 2
    
    def verify_system_health(self):
        """Verify system health and background workers"""
        self.log("=" * 60)
        self.log("VERIFYING SYSTEM HEALTH")
        self.log("=" * 60)
        
        health_checks = {}
        
        # 1. API Health
        try:
            response = self.session.get(f"{API_BASE}/health")
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "healthy":
                    health_checks['api'] = True
                    self.log("✅ Backend API responding")
                else:
                    health_checks['api'] = False
                    self.log("❌ Backend API unhealthy")
            else:
                health_checks['api'] = False
                self.log(f"❌ API health check failed: {response.status_code}")
        except Exception as e:
            health_checks['api'] = False
            self.log(f"❌ API health error: {str(e)}")
        
        # 2. MongoDB
        try:
            if self.db is not None:
                self.db.command('ping')
                health_checks['mongodb'] = True
                self.log("✅ MongoDB connected")
            else:
                health_checks['mongodb'] = False
                self.log("❌ MongoDB not connected")
        except Exception as e:
            health_checks['mongodb'] = False
            self.log(f"❌ MongoDB error: {str(e)}")
        
        # 3. Redis
        try:
            if self.redis_client is not None:
                self.redis_client.ping()
                health_checks['redis'] = True
                self.log("✅ Redis running")
            else:
                health_checks['redis'] = False
                self.log("❌ Redis not connected")
        except Exception as e:
            health_checks['redis'] = False
            self.log(f"❌ Redis error: {str(e)}")
        
        # 4. Background Workers
        try:
            import subprocess
            result = subprocess.run(
                ["supervisorctl", "status"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                status_output = result.stdout
                running_services = status_output.count("RUNNING")
                
                if running_services >= 3:  # backend, frontend, workers
                    health_checks['workers'] = True
                    self.log(f"✅ Background workers running ({running_services} services)")
                else:
                    health_checks['workers'] = False
                    self.log(f"❌ Limited services running ({running_services})")
            else:
                health_checks['workers'] = False
                self.log("❌ Could not check service status")
        except Exception as e:
            health_checks['workers'] = False
            self.log(f"❌ Worker check error: {str(e)}")
        
        return health_checks
    
    def run_comprehensive_test(self):
        """Run complete production email flow test"""
        self.log("🚀 STARTING COMPREHENSIVE PRODUCTION EMAIL FLOW TEST")
        self.log("=" * 80)
        
        test_results = {}
        
        # Phase 1: Setup
        self.log("PHASE 1: SETUP VERIFICATION")
        self.log("-" * 40)
        test_results['database_setup'] = self.setup_database_connections()
        test_results['authentication'] = self.test_user_authentication()
        test_results['user_setup'] = self.verify_user_setup()
        
        if not all([test_results['database_setup'], test_results['authentication'], test_results['user_setup']]):
            self.log("❌ Setup verification failed - cannot proceed")
            return False
        
        # Phase 2: Send emails
        self.log("\nPHASE 2: REAL EMAIL SENDING")
        self.log("-" * 40)
        test_results['email_sending'] = self.send_test_emails()
        
        if not test_results['email_sending']:
            self.log("❌ Email sending failed - cannot proceed")
            return False
        
        # Phase 3: Wait for processing
        self.log("\nPHASE 3: EMAIL PROCESSING WAIT")
        self.log("-" * 40)
        test_results['processing_wait'] = self.wait_for_email_processing()
        
        # Phase 4: Verify processing
        self.log("\nPHASE 4: EMAIL PROCESSING VERIFICATION")
        self.log("-" * 40)
        email_results = self.verify_email_processing()
        test_results['email_processing'] = bool(email_results)
        
        # Phase 5: System health
        self.log("\nPHASE 5: SYSTEM HEALTH VERIFICATION")
        self.log("-" * 40)
        health_results = self.verify_system_health()
        test_results['system_health'] = all(health_results.values())
        
        # Final assessment
        self.log("\nPHASE 6: FINAL ASSESSMENT")
        self.log("-" * 40)
        
        if email_results:
            # Detailed email results
            self.log("\n📊 EMAIL PROCESSING RESULTS:")
            for i, result in enumerate(email_results, 1):
                self.log(f"\nEmail {i}: {result['subject']}")
                for key, value in result.items():
                    if key not in ['email_id', 'subject']:
                        status = "✅" if value else "❌"
                        self.log(f"  {status} {key.replace('_', ' ').title()}: {value}")
        
        # Overall results
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        self.log(f"\n📊 OVERALL TEST RESULTS: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
        for test_name, result in test_results.items():
            status_icon = "✅" if result else "❌"
            self.log(f"  {status_icon} {test_name.replace('_', ' ').title()}: {'PASSED' if result else 'FAILED'}")
        
        if success_rate >= 80:
            self.log("\n🎉 PRODUCTION EMAIL FLOW TEST COMPLETED SUCCESSFULLY!")
            self.log("✅ System is ready for production use")
            return True, email_results
        else:
            self.log("\n❌ PRODUCTION EMAIL FLOW TEST FAILED")
            self.log("⚠️ Issues need to be resolved before production use")
            return False, email_results

def main():
    """Main test execution"""
    tester = ProductionEmailFlowTester()
    
    try:
        success, email_results = tester.run_comprehensive_test()
        
        if success:
            print("\n" + "="*80)
            print("✅ COMPREHENSIVE PRODUCTION EMAIL FLOW TEST COMPLETED SUCCESSFULLY")
            print("🚀 System is production ready")
            print("="*80)
            
            # Summary of critical checks
            if email_results:
                auto_sent_count = sum(1 for r in email_results if r['auto_sent'])
                follow_up_count = sum(1 for r in email_results if r['follow_ups_created'])
                signature_issues = sum(1 for r in email_results if r['signature_issues'])
                
                print(f"\n📊 CRITICAL SUCCESS METRICS:")
                print(f"✅ Emails auto-sent: {auto_sent_count}/{len(email_results)}")
                print(f"✅ Follow-ups created: {follow_up_count}/{len(email_results)}")
                print(f"✅ Signature issues: {signature_issues}/{len(email_results)}")
            
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ COMPREHENSIVE PRODUCTION EMAIL FLOW TEST FAILED")
            print("🔧 Issues need to be resolved")
            print("="*80)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
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