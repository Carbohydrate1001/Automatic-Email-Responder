"""
Test script to verify pricing_inquiry template fix.
Tests route-specific pricing queries against the logistics database.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Mock config to avoid import errors
class MockConfig:
    OPENAI_API_KEY = "test"
    OPENAI_BASE_URL = "test"
    OPENAI_MODEL = "test"
    DEMO_MODE = True
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), "email_system.db")

sys.modules['config'] = MockConfig()

# Initialize database with logistics routes
from models.database import init_db
from scripts.init_logistics_routes import init_logistics_routes

print("Initializing database...")
init_db()
init_logistics_routes()

# Now test the reply service
from services.reply_service import ReplyService

def test_pricing_scenarios():
    """Test pricing inquiry scenarios."""

    service = ReplyService()

    print("\n" + "=" * 80)
    print("Test 1: Sea freight with route and container (should find in database)")
    print("=" * 80)
    subject1 = "海运价格咨询"
    body1 = "请问从深圳到纽约的海运价格是多少？20尺柜。"
    reply1 = service._generate_pricing_template_reply("inquiry@example.com", subject1, body1, "2026-04-26")
    print(f"Subject: {subject1}")
    print(f"Body: {body1}")
    print(f"\nReply:\n{reply1}\n")

    # Verify reply contains real pricing
    if "USD 2800" in reply1 or "2800.0" in reply1:
        print("✅ PASS: Reply contains real database pricing (USD 2800 for 20ft Shenzhen-NY)")
    else:
        print("❌ FAIL: Reply doesn't contain expected pricing")

    if "深圳" in reply1 and "纽约" in reply1:
        print("✅ PASS: Reply mentions correct route")
    else:
        print("❌ FAIL: Reply doesn't mention the route")

    if "Sea Freight (Standard)" in reply1:
        print("❌ FAIL: Reply still uses old generic product template")
    else:
        print("✅ PASS: Reply doesn't use generic product template")

    print("\n" + "=" * 80)
    print("Test 2: Air freight with weight (should find in database)")
    print("=" * 80)
    subject2 = "空运报价"
    body2 = "100公斤货物从上海到伦敦空运多少钱？"
    reply2 = service._generate_pricing_template_reply("inquiry@example.com", subject2, body2, "2026-04-26")
    print(f"Subject: {subject2}")
    print(f"Body: {body2}")
    print(f"\nReply:\n{reply2}\n")

    # Verify reply contains real pricing (100kg falls in 100-500 range: USD 7.8/kg)
    if "USD 7.8" in reply2 or "7.8" in reply2:
        print("✅ PASS: Reply contains real database pricing (USD 7.8/kg for 100kg Shanghai-London)")
    else:
        print("❌ FAIL: Reply doesn't contain expected pricing")

    if "上海" in reply2 and "伦敦" in reply2:
        print("✅ PASS: Reply mentions correct route")
    else:
        print("❌ FAIL: Reply doesn't mention the route")

    if "空运" in reply2:
        print("✅ PASS: Reply mentions air freight")
    else:
        print("❌ FAIL: Reply doesn't mention shipping method")

    print("\n" + "=" * 80)
    print("Test 3: Route not in database (should acknowledge and request details)")
    print("=" * 80)
    subject3 = "运费咨询"
    body3 = "从北京到悉尼的海运多少钱？"
    reply3 = service._generate_pricing_template_reply("inquiry@example.com", subject3, body3, "2026-04-26")
    print(f"Subject: {subject3}")
    print(f"Body: {body3}")
    print(f"\nReply:\n{reply3}\n")

    # Verify reply acknowledges route not found
    if "北京" in reply3 and "悉尼" in reply3:
        print("✅ PASS: Reply mentions the queried route")
    else:
        print("❌ FAIL: Reply doesn't mention the route")

    if "进一步核实" in reply3 or "详细信息" in reply3 or "提供" in reply3:
        print("✅ PASS: Reply requests more details (route not in database)")
    else:
        print("❌ FAIL: Reply doesn't request additional information")

    if "USD 120" in reply3 or "Sea Freight (Standard)" in reply3:
        print("❌ FAIL: Reply uses fake generic pricing instead of acknowledging missing data")
    else:
        print("✅ PASS: Reply doesn't use fake generic pricing")

    print("\n" + "=" * 80)
    print("Test 4: Insufficient information (should request details)")
    print("=" * 80)
    subject4 = "询价"
    body4 = "你们的运费怎么算？"
    reply4 = service._generate_pricing_template_reply("inquiry@example.com", subject4, body4, "2026-04-26")
    print(f"Subject: {subject4}")
    print(f"Body: {body4}")
    print(f"\nReply:\n{reply4}\n")

    # Verify reply requests necessary information
    if "起运地" in reply4 and "目的地" in reply4:
        print("✅ PASS: Reply requests origin and destination")
    else:
        print("❌ FAIL: Reply doesn't request route information")

    if "运输方式" in reply4 or "海运" in reply4 or "空运" in reply4:
        print("✅ PASS: Reply requests shipping method")
    else:
        print("❌ FAIL: Reply doesn't request shipping method")

if __name__ == "__main__":
    try:
        test_pricing_scenarios()
        print("\n" + "=" * 80)
        print("All tests completed!")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
