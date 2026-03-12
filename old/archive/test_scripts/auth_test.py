#!/usr/bin/env python3
"""
AUTHENTICATION ENDPOINTS TESTING

This test suite comprehensively tests the authentication endpoints as requested:
1. POST /api/auth/register with valid data
2. POST /api/auth/login with created user
3. POST /api/auth/login with admin credentials  
4. GET /api/auth/me with valid token
5. Negative test cases

BACKEND URL: https://followup-enhance.preview.emergentagent.com
"""

import requests
import json
import sys
import time
from datetime import datetime
import logging

# Configuration
BACKEND_URL = "https://followup-enhance.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test user data
TEST_USER = {
    "email": "test_user@test.com",
    "password": "Test@123",
    "full_name": "Test User"
}

# Admin credentials
ADMIN_USER = {
    "email": "admin@emailassistant.com", 
    "password": "Admin@123"
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AuthenticationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {}
        self.test_user_token = None
        self.admin_token = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_user_registration(self):
        """Test POST /api/auth/register with valid data"""
        self.log("=" * 60)
        self.log("TESTING USER REGISTRATION")
        self.log("=" * 60)
        
        try:
            # First, try to clean up any existing test user
            try:
                login_response = self.session.post(
                    f"{API_BASE}/auth/login",
                    json={"email": TEST_USER["email"], "password": TEST_USER["password"]},
                    headers={"Content-Type": "application/json"}
                )
                if login_response.status_code == 200:
                    self.log("⚠️  Test user already exists, will test with existing user")
                    data = login_response.json()
                    self.test_user_token = data.get("access_token")
                    user = data.get("user", {})
                    
                    # Verify all required fields are present
                    required_fields = [
                        "id", "email", "full_name", "quota", "quota_used", 
                        "quota_reset_date", "created_at", "role", "is_active",
                        "hubspot_enabled", "hubspot_connected", "hubspot_portal_id", "hubspot_auto_sync"
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in user]
                    
                    if missing_fields:
                        self.log(f"❌ Missing required fields in user object: {missing_fields}")
                        return False
                    
                    self.log("✅ User registration test passed (user already exists with all required fields)")
                    self.log(f"User ID: {user.get('id')}")
                    self.log(f"Email: {user.get('email')}")
                    self.log(f"Full Name: {user.get('full_name')}")
                    self.log(f"Role: {user.get('role')}")
                    self.log(f"Quota: {user.get('quota')}")
                    self.log(f"Quota Used: {user.get('quota_used')}")
                    self.log(f"Is Active: {user.get('is_active')}")
                    self.log(f"HubSpot Enabled: {user.get('hubspot_enabled')}")
                    self.log(f"HubSpot Connected: {user.get('hubspot_connected')}")
                    return True
            except:
                pass  # User doesn't exist, proceed with registration
            
            # Test user registration
            self.log(f"Testing registration with email: {TEST_USER['email']}")
            
            response = self.session.post(
                f"{API_BASE}/auth/register",
                json=TEST_USER,
                headers={"Content-Type": "application/json"}
            )
            
            self.log(f"Registration response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "access_token" not in data or "user" not in data:
                    self.log("❌ Registration response missing access_token or user")
                    return False
                
                self.test_user_token = data.get("access_token")
                user = data.get("user", {})
                
                # Verify all required user fields are present
                required_fields = [
                    "id", "email", "full_name", "quota", "quota_used", 
                    "quota_reset_date", "created_at", "role", "is_active",
                    "hubspot_enabled", "hubspot_connected", "hubspot_portal_id", "hubspot_auto_sync"
                ]
                
                missing_fields = [field for field in required_fields if field not in user]
                
                if missing_fields:
                    self.log(f"❌ Missing required fields in user object: {missing_fields}")
                    return False
                
                # Verify field values
                if user.get("email") != TEST_USER["email"]:
                    self.log(f"❌ Email mismatch: expected {TEST_USER['email']}, got {user.get('email')}")
                    return False
                
                if user.get("full_name") != TEST_USER["full_name"]:
                    self.log(f"❌ Full name mismatch: expected {TEST_USER['full_name']}, got {user.get('full_name')}")
                    return False
                
                self.log("✅ User registration successful")
                self.log(f"User ID: {user.get('id')}")
                self.log(f"Email: {user.get('email')}")
                self.log(f"Full Name: {user.get('full_name')}")
                self.log(f"Role: {user.get('role')}")
                self.log(f"Quota: {user.get('quota')}")
                self.log(f"Quota Used: {user.get('quota_used')}")
                self.log(f"Is Active: {user.get('is_active')}")
                self.log(f"HubSpot Enabled: {user.get('hubspot_enabled')}")
                self.log(f"HubSpot Connected: {user.get('hubspot_connected')}")
                self.log(f"Access Token: {self.test_user_token[:20]}...")
                
                return True
            else:
                self.log(f"❌ Registration failed: {response.status_code}")
                self.log(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Registration error: {str(e)}", "ERROR")
            return False
    
    def test_user_login(self):
        """Test POST /api/auth/login with the created user"""
        self.log("=" * 60)
        self.log("TESTING USER LOGIN")
        self.log("=" * 60)
        
        try:
            login_data = {
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            }
            
            self.log(f"Testing login with email: {login_data['email']}")
            
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            self.log(f"Login response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "access_token" not in data or "user" not in data:
                    self.log("❌ Login response missing access_token or user")
                    return False
                
                self.test_user_token = data.get("access_token")
                user = data.get("user", {})
                
                # Verify user data
                if user.get("email") != TEST_USER["email"]:
                    self.log(f"❌ Email mismatch in login response")
                    return False
                
                self.log("✅ User login successful")
                self.log(f"User ID: {user.get('id')}")
                self.log(f"Email: {user.get('email')}")
                self.log(f"Role: {user.get('role')}")
                self.log(f"Access Token: {self.test_user_token[:20]}...")
                
                return True
            else:
                self.log(f"❌ Login failed: {response.status_code}")
                self.log(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Login error: {str(e)}", "ERROR")
            return False
    
    def test_admin_login(self):
        """Test POST /api/auth/login with admin credentials"""
        self.log("=" * 60)
        self.log("TESTING ADMIN LOGIN")
        self.log("=" * 60)
        
        try:
            self.log(f"Testing admin login with email: {ADMIN_USER['email']}")
            
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=ADMIN_USER,
                headers={"Content-Type": "application/json"}
            )
            
            self.log(f"Admin login response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "access_token" not in data or "user" not in data:
                    self.log("❌ Admin login response missing access_token or user")
                    return False
                
                self.admin_token = data.get("access_token")
                user = data.get("user", {})
                
                # Verify admin role
                if user.get("role") != "admin":
                    self.log(f"❌ Expected admin role, got: {user.get('role')}")
                    return False
                
                # Verify email
                if user.get("email") != ADMIN_USER["email"]:
                    self.log(f"❌ Email mismatch in admin login response")
                    return False
                
                self.log("✅ Admin login successful")
                self.log(f"Admin ID: {user.get('id')}")
                self.log(f"Email: {user.get('email')}")
                self.log(f"Role: {user.get('role')}")
                self.log(f"Access Token: {self.admin_token[:20]}...")
                
                return True
            else:
                self.log(f"❌ Admin login failed: {response.status_code}")
                self.log(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Admin login error: {str(e)}", "ERROR")
            return False
    
    def test_get_profile(self):
        """Test GET /api/auth/me with valid token"""
        self.log("=" * 60)
        self.log("TESTING GET PROFILE")
        self.log("=" * 60)
        
        if not self.test_user_token:
            self.log("❌ No test user token available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.test_user_token}",
                "Content-Type": "application/json"
            }
            
            self.log("Testing GET /api/auth/me with valid token")
            
            response = self.session.get(
                f"{API_BASE}/auth/me",
                headers=headers
            )
            
            self.log(f"Profile response status: {response.status_code}")
            
            if response.status_code == 200:
                user = response.json()
                
                # Verify all required fields are present
                required_fields = [
                    "id", "email", "full_name", "quota", "quota_used", 
                    "quota_reset_date", "created_at", "role", "is_active",
                    "hubspot_enabled", "hubspot_connected", "hubspot_portal_id", "hubspot_auto_sync"
                ]
                
                missing_fields = [field for field in required_fields if field not in user]
                
                if missing_fields:
                    self.log(f"❌ Missing required fields in profile response: {missing_fields}")
                    return False
                
                # Verify user data matches
                if user.get("email") != TEST_USER["email"]:
                    self.log(f"❌ Email mismatch in profile response")
                    return False
                
                self.log("✅ Get profile successful")
                self.log(f"User ID: {user.get('id')}")
                self.log(f"Email: {user.get('email')}")
                self.log(f"Full Name: {user.get('full_name')}")
                self.log(f"Role: {user.get('role')}")
                self.log(f"Quota: {user.get('quota')}")
                self.log(f"Is Active: {user.get('is_active')}")
                
                return True
            else:
                self.log(f"❌ Get profile failed: {response.status_code}")
                self.log(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Get profile error: {str(e)}", "ERROR")
            return False
    
    def test_negative_cases(self):
        """Test negative cases: existing email, wrong password, no token"""
        self.log("=" * 60)
        self.log("TESTING NEGATIVE CASES")
        self.log("=" * 60)
        
        results = {}
        
        # Test 1: Register with existing email
        try:
            self.log("Test 1: Register with existing email (should fail with 400)")
            
            response = self.session.post(
                f"{API_BASE}/auth/register",
                json=TEST_USER,  # Same user data as before
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400:
                self.log("✅ Registration with existing email correctly failed with 400")
                results['existing_email'] = True
            else:
                self.log(f"❌ Expected 400 for existing email, got {response.status_code}")
                results['existing_email'] = False
                
        except Exception as e:
            self.log(f"❌ Error testing existing email: {str(e)}")
            results['existing_email'] = False
        
        # Test 2: Login with wrong password
        try:
            self.log("Test 2: Login with wrong password (should fail with 401)")
            
            wrong_credentials = {
                "email": TEST_USER["email"],
                "password": "WrongPassword123"
            }
            
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=wrong_credentials,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 401:
                self.log("✅ Login with wrong password correctly failed with 401")
                results['wrong_password'] = True
            else:
                self.log(f"❌ Expected 401 for wrong password, got {response.status_code}")
                results['wrong_password'] = False
                
        except Exception as e:
            self.log(f"❌ Error testing wrong password: {str(e)}")
            results['wrong_password'] = False
        
        # Test 3: Access /api/auth/me without token
        try:
            self.log("Test 3: Access /api/auth/me without token (should fail with 401)")
            
            response = self.session.get(f"{API_BASE}/auth/me")
            
            if response.status_code == 401:
                self.log("✅ Access without token correctly failed with 401")
                results['no_token'] = True
            else:
                self.log(f"❌ Expected 401 for no token, got {response.status_code}")
                results['no_token'] = False
                
        except Exception as e:
            self.log(f"❌ Error testing no token: {str(e)}")
            results['no_token'] = False
        
        # Test 4: Access /api/auth/me with invalid token
        try:
            self.log("Test 4: Access /api/auth/me with invalid token (should fail with 401)")
            
            headers = {
                "Authorization": "Bearer invalid_token_here",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{API_BASE}/auth/me",
                headers=headers
            )
            
            if response.status_code == 401:
                self.log("✅ Access with invalid token correctly failed with 401")
                results['invalid_token'] = True
            else:
                self.log(f"❌ Expected 401 for invalid token, got {response.status_code}")
                results['invalid_token'] = False
                
        except Exception as e:
            self.log(f"❌ Error testing invalid token: {str(e)}")
            results['invalid_token'] = False
        
        # Summary
        passed_negative_tests = sum(results.values())
        total_negative_tests = len(results)
        
        self.log(f"\n📊 NEGATIVE TESTS RESULTS: {passed_negative_tests}/{total_negative_tests} passed")
        
        for test_name, result in results.items():
            status_icon = "✅" if result else "❌"
            self.log(f"  {status_icon} {test_name.replace('_', ' ').title()}: {'PASSED' if result else 'FAILED'}")
        
        return passed_negative_tests == total_negative_tests
    
    def run_comprehensive_test(self):
        """Run all authentication tests"""
        self.log("🚀 STARTING AUTHENTICATION ENDPOINTS TESTING")
        self.log("=" * 80)
        
        test_results = {}
        
        # Core authentication tests
        self.log("PHASE 1: CORE AUTHENTICATION TESTING")
        self.log("-" * 50)
        test_results['user_registration'] = self.test_user_registration()
        test_results['user_login'] = self.test_user_login()
        test_results['admin_login'] = self.test_admin_login()
        test_results['get_profile'] = self.test_get_profile()
        
        # Negative test cases
        self.log("\nPHASE 2: NEGATIVE TEST CASES")
        self.log("-" * 50)
        test_results['negative_cases'] = self.test_negative_cases()
        
        # Final assessment
        self.log("\nPHASE 3: FINAL ASSESSMENT")
        self.log("-" * 50)
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        self.log(f"\n📊 OVERALL TEST RESULTS: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
        for test_name, result in test_results.items():
            status_icon = "✅" if result else "❌"
            self.log(f"  {status_icon} {test_name.replace('_', ' ').title()}: {'PASSED' if result else 'FAILED'}")
        
        if success_rate == 100:
            self.log("\n🎉 ALL AUTHENTICATION TESTS PASSED!")
            self.log("✅ Authentication endpoints are working correctly")
            return True
        else:
            self.log("\n❌ SOME AUTHENTICATION TESTS FAILED")
            self.log("⚠️  Issues need to be resolved")
            return False

def main():
    """Main test execution"""
    tester = AuthenticationTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n" + "="*80)
            print("✅ AUTHENTICATION ENDPOINTS TESTING COMPLETED SUCCESSFULLY")
            print("🚀 All authentication features are working correctly")
            print("="*80)
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ AUTHENTICATION ENDPOINTS TESTING FAILED")
            print("🔧 Issues need to be resolved")
            print("="*80)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()