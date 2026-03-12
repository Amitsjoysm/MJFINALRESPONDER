"""
Validation Test Script - Test Enhanced Greeting-Only Detection
Tests the fixed validation logic to ensure "Hi Name," responses are rejected
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from services.ai_agent_service import AIAgentService
from models.email import Email
from config import config

async def test_validation():
    """Test validation with various draft scenarios"""
    
    # Connect to database
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    # Initialize AI service
    ai_service = AIAgentService(db)
    
    # Create a test email
    test_email = Email(
        user_id="test-user",
        email_account_id="test-account",
        message_id="test-msg-001",
        from_email="sender@example.com",
        to_email=["receiver@example.com"],
        subject="Test Question",
        body="Can you help me with pricing information?",
        direction="inbound"
    )
    
    # Test cases - these should ALL be REJECTED
    invalid_drafts = [
        "Hi John,",
        "Hello Sarah,",
        "Dear Customer,",
        "Hi there,",
        "Hello John,\n\n",  # With extra whitespace
        "Hi John,\n\n\n\n",  # With multiple newlines
        "Hi John,  \n  \n  ",  # With spaces and newlines
        "Hi John,\n\nThanks.",  # Minimal content after greeting
        "Hello Sarah,\n\nBest regards,",  # Only greeting and closing
        "Dear Customer,\n\nThanks for reaching out.",  # Too short
    ]
    
    # Test cases - these should PASS validation
    valid_drafts = [
        "Hi John,\n\nThank you for reaching out about our pricing. We offer three tiers: Basic ($10/month), Pro ($25/month), and Enterprise (custom pricing). Each tier includes different features tailored to your needs. Would you like me to schedule a call to discuss which option would work best for you?",
        "Hello Sarah,\n\nI'd be happy to help you with that. Based on your requirements, I recommend our Pro plan which includes all the features you mentioned. The Pro plan is $25/month and comes with unlimited users, advanced analytics, and priority support. Let me know if you have any questions!",
        "Dear Customer,\n\nThank you for your interest in our services. I've reviewed your inquiry and prepared a detailed proposal that addresses your specific needs. I'll send over the pricing breakdown shortly. In the meantime, please let me know if you have any immediate questions I can answer."
    ]
    
    print("=" * 80)
    print("🧪 VALIDATION TEST - Enhanced Greeting-Only Detection")
    print("=" * 80)
    print()
    
    # Test invalid drafts (should be rejected)
    print("📛 Testing INVALID Drafts (Should be REJECTED):")
    print("-" * 80)
    
    invalid_passed = 0
    invalid_failed = 0
    
    for i, draft in enumerate(invalid_drafts, 1):
        print(f"\nTest {i}: '{draft[:50]}...' ({len(draft)} chars)")
        
        try:
            is_valid, issues, tokens = await ai_service.validate_draft(
                draft, test_email, []
            )
            
            if is_valid:
                print(f"   ❌ FAIL: Draft was ACCEPTED (should be rejected)")
                invalid_passed += 1
            else:
                print(f"   ✅ PASS: Draft was REJECTED")
                print(f"   Issues: {', '.join(issues)}")
                invalid_failed += 1
        except Exception as e:
            print(f"   ✅ PASS: Draft raised error (rejected): {str(e)[:100]}")
            invalid_failed += 1
    
    print()
    print("=" * 80)
    
    # Test valid drafts (should pass)
    print("\n✅ Testing VALID Drafts (Should be ACCEPTED):")
    print("-" * 80)
    
    valid_passed = 0
    valid_failed = 0
    
    for i, draft in enumerate(valid_drafts, 1):
        print(f"\nTest {i}: '{draft[:50]}...' ({len(draft)} chars)")
        
        try:
            is_valid, issues, tokens = await ai_service.validate_draft(
                draft, test_email, []
            )
            
            if is_valid:
                print(f"   ✅ PASS: Draft was ACCEPTED")
                valid_passed += 1
            else:
                print(f"   ❌ FAIL: Draft was REJECTED (should be accepted)")
                print(f"   Issues: {', '.join(issues)}")
                valid_failed += 1
        except Exception as e:
            print(f"   ❌ FAIL: Draft raised error: {str(e)[:100]}")
            valid_failed += 1
    
    print()
    print("=" * 80)
    print("\n📊 TEST RESULTS:")
    print("=" * 80)
    print(f"\nInvalid Drafts (Greeting-Only):")
    print(f"  ✅ Correctly Rejected: {invalid_failed}/{len(invalid_drafts)}")
    print(f"  ❌ Incorrectly Accepted: {invalid_passed}/{len(invalid_drafts)}")
    
    print(f"\nValid Drafts (Complete Responses):")
    print(f"  ✅ Correctly Accepted: {valid_passed}/{len(valid_drafts)}")
    print(f"  ❌ Incorrectly Rejected: {valid_failed}/{len(valid_drafts)}")
    
    print()
    
    # Overall success
    total_tests = len(invalid_drafts) + len(valid_drafts)
    total_passed = invalid_failed + valid_passed
    success_rate = (total_passed / total_tests) * 100
    
    print(f"Overall Success Rate: {success_rate:.1f}% ({total_passed}/{total_tests} tests passed)")
    print()
    
    if success_rate == 100:
        print("🎉 ALL TESTS PASSED! Validation is working correctly.")
        print("✅ Greeting-only responses will be rejected.")
        print("✅ Valid responses will be accepted.")
    elif success_rate >= 90:
        print("⚠️  MOST TESTS PASSED. Minor issues detected.")
        print("Please review failed tests above.")
    else:
        print("❌ VALIDATION ISSUES DETECTED!")
        print("Please review the validation logic.")
    
    print("=" * 80)
    
    # Close database connection
    client.close()

if __name__ == "__main__":
    print("\nStarting validation tests...")
    print("Note: This will use the GROQ API for AI-powered validation layer.\n")
    
    asyncio.run(test_validation())
