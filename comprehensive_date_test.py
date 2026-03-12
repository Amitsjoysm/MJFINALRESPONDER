#!/usr/bin/env python3
"""
Comprehensive Date Parsing Tests for Email Assistant
Tests all the specific date parsing patterns mentioned in the review request
"""

import requests
import json
import sys
from datetime import datetime, timezone, timedelta
import time

# Configuration - Use the public API URL 
BACKEND_URL = "https://8da67e83-14ca-40cc-a94c-001d8b401cb2.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class DateParsingTester:
    def __init__(self):
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_test(self, name, test_func):
        """Run a single test and track results"""
        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            success = test_func()
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED: {name}")
                return True
            else:
                self.log(f"❌ FAILED: {name}")
                return False
        except Exception as e:
            self.log(f"❌ ERROR in {name}: {str(e)}", "ERROR")
            return False

    def parse_date_and_validate(self, text, expected_days_range=None, expected_season=None, expected_month=None, exact_days=None):
        """Helper function to parse date and validate results"""
        try:
            response = self.session.post(
                f"{API_BASE}/test/parse-dates",
                params={"text": text},
                timeout=10
            )
            
            if response.status_code != 200:
                self.log(f"API error: {response.status_code} - {response.text}")
                return False
            
            data = response.json()
            references = data.get('references', [])
            
            if len(references) == 0:
                self.log(f"No date references found for: '{text}'")
                return False
            
            ref = references[0]
            matched_text = ref.get('matched_text', '')
            target_date = ref.get('target_date', '')
            days_from_now = ref.get('days_from_now', 0)
            
            self.log(f"Match: '{matched_text}' -> {target_date} ({days_from_now} days)")
            
            # Validate based on criteria
            if expected_days_range:
                min_days, max_days = expected_days_range
                if not (min_days <= days_from_now <= max_days):
                    self.log(f"Days outside expected range: {days_from_now} not in [{min_days}, {max_days}]")
                    return False
            
            if exact_days is not None:
                if days_from_now != exact_days:
                    self.log(f"Days not exact match: {days_from_now} != {exact_days}")
                    return False
            
            if expected_season:
                try:
                    parsed_date = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
                    season_months = {
                        'spring': [3],  # March 20
                        'summer': [6],  # June 21  
                        'fall': [9],    # September 22
                        'autumn': [9],  # September 22
                        'winter': [12]  # December 21
                    }
                    
                    if parsed_date.month not in season_months.get(expected_season, []):
                        self.log(f"Season validation failed: {expected_season} -> month {parsed_date.month}")
                        return False
                except:
                    self.log(f"Could not parse date: {target_date}")
                    return False
            
            if expected_month:
                try:
                    parsed_date = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
                    if parsed_date.month != expected_month:
                        self.log(f"Month validation failed: expected {expected_month}, got {parsed_date.month}")
                        return False
                except:
                    self.log(f"Could not parse date: {target_date}")
                    return False
            
            return True
            
        except Exception as e:
            self.log(f"Test error: {e}")
            return False

    def test_next_month(self):
        """Test: Please follow up next month"""
        return self.parse_date_and_validate(
            "Please follow up next month",
            expected_days_range=(28, 35)  # ~30 days from now
        )

    def test_next_quarter(self):
        """Test: Contact me next quarter"""  
        # Should return date around April 1 (next quarter start)
        return self.parse_date_and_validate(
            "Contact me next quarter", 
            expected_month=4  # April
        )

    def test_next_year(self):
        """Test: Follow up next year"""
        return self.parse_date_and_validate(
            "Follow up next year",
            expected_days_range=(360, 370)  # ~365 days from now
        )

    def test_next_summer(self):
        """Test: Reach out next summer"""
        return self.parse_date_and_validate(
            "Reach out next summer",
            expected_season="summer"  # Should be June 21
        )

    def test_after_10_15_days(self):
        """Test: Get back to me after 10-15 days"""
        return self.parse_date_and_validate(
            "Get back to me after 10-15 days",
            exact_days=12  # Should return midpoint: 12 days
        )

    def test_after_30_days_single_result(self):
        """Test: Follow up after 30 days -> returns EXACTLY 1 result (no false positive)"""
        try:
            text = "Follow up after 30 days"
            response = self.session.post(
                f"{API_BASE}/test/parse-dates",
                params={"text": text},
                timeout=10
            )
            
            if response.status_code != 200:
                return False
            
            data = response.json()
            references = data.get('references', [])
            
            # Should have exactly 1 result
            if len(references) != 1:
                self.log(f"Expected exactly 1 result, got {len(references)}")
                return False
            
            ref = references[0]
            days_from_now = ref.get('days_from_now', 0)
            
            # Should be exactly 30 days
            if days_from_now != 30:
                self.log(f"Expected 30 days, got {days_from_now}")
                return False
            
            self.log(f"✓ Single result for '30 days': {days_from_now} days")
            return True
            
        except Exception as e:
            self.log(f"Test error: {e}")
            return False

    def test_next_winter(self):
        """Test: Let us connect next winter"""
        return self.parse_date_and_validate(
            "Let us connect next winter",
            expected_season="winter"  # Should be December 21
        )

    def test_next_fall(self):
        """Test: Follow up next fall"""
        return self.parse_date_and_validate(
            "Follow up next fall", 
            expected_season="fall"  # Should be September 22
        )

    def test_beginning_next_year(self):
        """Test: Follow up at beginning of next year"""
        # Should return Jan 2 of next year
        return self.parse_date_and_validate(
            "Follow up at beginning of next year",
            expected_month=1  # January
        )

    def test_next_fiscal_year(self):
        """Test: Revisit next fiscal year"""
        # Should return Apr 1 of next year
        return self.parse_date_and_validate(
            "Revisit next fiscal year",
            expected_month=4  # April (fiscal year start)
        )

    def test_couple_days(self):
        """Test: in a couple of days"""
        return self.parse_date_and_validate(
            "in a couple of days",
            exact_days=3  # Should return 3 days
        )

    def test_after_2_3_weeks(self):
        """Test: Follow up after 2-3 weeks"""
        return self.parse_date_and_validate(
            "Follow up after 2-3 weeks",
            exact_days=14  # Should return midpoint: 14 days (2 weeks)
        )

    def run_all_tests(self):
        """Run all date parsing validation tests"""
        self.log("=" * 80)
        self.log("COMPREHENSIVE DATE PARSING VALIDATION TESTS")
        self.log("=" * 80)
        
        # Test all patterns from the review request
        test_cases = [
            ("Next Month Pattern", self.test_next_month),
            ("Next Quarter Pattern", self.test_next_quarter),
            ("Next Year Pattern", self.test_next_year),
            ("Next Summer Pattern", self.test_next_summer),
            ("After 10-15 Days Range", self.test_after_10_15_days),
            ("After 30 Days (Single Result)", self.test_after_30_days_single_result),
            ("Next Winter Pattern", self.test_next_winter),
            ("Next Fall Pattern", self.test_next_fall),
            ("Beginning Next Year", self.test_beginning_next_year),
            ("Next Fiscal Year", self.test_next_fiscal_year),
            ("Couple of Days", self.test_couple_days),
            ("After 2-3 Weeks Range", self.test_after_2_3_weeks),
        ]
        
        for name, test_func in test_cases:
            self.run_test(name, test_func)
        
        # Print results
        self.log("=" * 80)
        self.log("DATE PARSING TEST RESULTS")
        self.log("=" * 80)
        self.log(f"Tests Run: {self.tests_run}")
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Tests Failed: {self.tests_run - self.tests_passed}")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            self.log("🎉 OVERALL STATUS: EXCELLENT - All date parsing patterns working")
            return 0
        elif success_rate >= 80:
            self.log("✅ OVERALL STATUS: GOOD - Most patterns working") 
            return 0
        elif success_rate >= 60:
            self.log("⚠️  OVERALL STATUS: PARTIAL - Some patterns need fixes")
            return 1
        else:
            self.log("❌ OVERALL STATUS: FAILED - Major date parsing issues")
            return 1

def main():
    """Main test execution"""
    tester = DateParsingTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())