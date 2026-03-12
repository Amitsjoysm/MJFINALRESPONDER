"""
Test Draft Validation - Ensure greeting-only drafts are rejected
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import os

sys.path.insert(0, '/app/backend')

from config import config
from services.ai_agent_service import AIAgentService
from models.email import Email
from datetime import datetime, timezone

async def test_validation():
    """Test draft validation with various scenarios"""
    
    print("=" * 80)
    print("🧪 TESTING DRAFT VALIDATION")
    print("=" * 80)
    
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    ai_service = AIAgentService(db)
    
    # Create fake email
    fake_email = Email(
        user_id="test-user",
        email_account_id="test-account",
        from_email="test@example.com",
        to_email=["amits.joys@gmail.com"],
        subject="Pricing Inquiry",
        body="Hi, I'm interested in your pricing. Can you send me details about your plans? What are the costs?",
        received_at=datetime.now(timezone.utc).isoformat(),
        message_id="test-123",
        thread_id="test-thread"
    )
    
    # Test cases
    test_cases = [
        {
            "name": "Greeting Only - Just Hi",
            "draft": "Hi John,",
            "should_pass": False,
            "reason": "Only greeting, no content"
        },
        {
            "name": "Greeting Only - Hello",
            "draft": "Hello Sarah,",
            "should_pass": False,
            "reason": "Only greeting, no content"
        },
        {
            "name": "Greeting + Minimal Content",
            "draft": "Hi there,\n\nThanks!",
            "should_pass": False,
            "reason": "Too short, no actual information"
        },
        {
            "name": "Short Generic Response",
            "draft": "Thanks for reaching out. We'll get back to you soon.",
            "should_pass": False,
            "reason": "Doesn't answer the questions"
        },
        {
            "name": "Valid Response - Comprehensive",
            "draft": """Hi John,

Thank you for your interest in our pricing. I'd be happy to provide you with details about our plans.

We offer three main pricing tiers:

1. Starter Plan at $99/month - includes up to 2,000 emails and basic AI features
2. Professional Plan at $299/month - includes up to 10,000 emails and advanced features
3. Enterprise Plan with custom pricing for unlimited usage

Each plan comes with a 14-day free trial. Which plan would best fit your needs based on your email volume?

Looking forward to helping you get started!""",
            "should_pass": True,
            "reason": "Complete response with details"
        },
        {
            "name": "Valid Response - Concise",
            "draft": """Thank you for your pricing inquiry. Our plans start at $99/month for the Starter tier, which includes 2,000 emails and basic features. The Professional plan is $299/month with 10,000 emails and advanced AI capabilities. We also offer custom Enterprise pricing. All plans include a 14-day free trial. Would you like more details about a specific plan?""",
            "should_pass": True,
            "reason": "Answers questions, provides value"
        }
    ]
    
    print("\n" + "=" * 80)
    print("VALIDATION TESTS")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test['name']}")
        print(f"   Draft: {test['draft'][:80]}...")
        print(f"   Expected: {'✅ PASS' if test['should_pass'] else '❌ REJECT'}")
        
        # Validate
        is_valid, issues, tokens = await ai_service.validate_draft(
            test['draft'],
            fake_email,
            []
        )
        
        # Check result
        result_matches = is_valid == test['should_pass']
        
        if result_matches:
            print(f"   Result: ✅ {'PASSED' if is_valid else 'REJECTED'} (Correct!)")
            passed += 1
        else:
            print(f"   Result: ❌ {'PASSED' if is_valid else 'REJECTED'} (WRONG! Should be {'PASS' if test['should_pass'] else 'REJECT'})")
            failed += 1
        
        if issues:
            print(f"   Issues: {', '.join(issues)}")
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {passed}/{len(test_cases)}")
    print(f"❌ Failed: {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Validation is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review validation logic.")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(test_validation())
