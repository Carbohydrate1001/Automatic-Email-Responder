"""
Quick test to verify shipping_time template fix.
Tests three scenarios:
1. General inquiry (no order number)
2. Specific order inquiry (with valid order number)
3. Specific order inquiry (with invalid order number)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Mock the dependencies to avoid import errors
class MockConfig:
    OPENAI_API_KEY = "test"
    OPENAI_BASE_URL = "test"
    OPENAI_MODEL = "test"
    DEMO_MODE = True

sys.modules['config'] = MockConfig()

# Now we can import and test the reply service
from services.reply_service import ReplyService

def test_shipping_time_scenarios():
    """Test the three problematic scenarios."""

    service = ReplyService()

    print("=" * 80)
    print("Test 1: General inquiry (no order number)")
    print("=" * 80)
    body1 = "请问从中国到美国的海运一般需要多长时间？"
    reply1 = service._generate_shipping_time_template_reply("inquiry@example.com", body1)
    print(f"Body: {body1}")
    print(f"\nReply:\n{reply1}")

    # Check that reply doesn't claim "您的货物" (your shipment)
    if "您的货物" in reply1:
        print("\n❌ FAIL: Reply incorrectly claims 'your shipment' for general inquiry")
    else:
        print("\n✅ PASS: Reply provides general guidance without claiming specific shipment")

    # Check that reply provides general time ranges
    if "海运" in reply1 and ("天" in reply1 or "工作日" in reply1):
        print("✅ PASS: Reply contains general shipping time information")
    else:
        print("❌ FAIL: Reply missing general shipping time information")

    print("\n" + "=" * 80)
    print("Test 2: Specific order inquiry (valid order number)")
    print("=" * 80)
    body2 = "订单 ORD123456 大概什么时候能到？"
    reply2 = service._generate_shipping_time_template_reply("customer@example.com", body2)
    print(f"Body: {body2}")
    print(f"\nReply:\n{reply2}")

    # Check that reply includes order number
    if "ORD123456" in reply2:
        print("\n✅ PASS: Reply references the specific order number")
    else:
        print("❌ FAIL: Reply doesn't reference the order number")

    # Check that reply doesn't contain random routes
    random_cities = ["迪拜", "鹿特丹", "汉堡"]
    has_random_route = any(city in reply2 for city in random_cities)
    if has_random_route:
        print("❌ FAIL: Reply contains random/fake route information")
    else:
        print("✅ PASS: Reply doesn't contain random route information")

    print("\n" + "=" * 80)
    print("Test 3: Route-specific inquiry (no order number)")
    print("=" * 80)
    body3 = "从上海到洛杉矶的空运需要几天？"
    reply3 = service._generate_shipping_time_template_reply("inquiry@example.com", body3)
    print(f"Body: {body3}")
    print(f"\nReply:\n{reply3}")

    # Check that reply doesn't contain contradictory routes
    if "鹿特丹" in reply3 or "迪拜" in reply3:
        print("\n❌ FAIL: Reply contains contradictory route (Rotterdam/Dubai when asked about Shanghai-LA)")
    else:
        print("✅ PASS: Reply doesn't contain contradictory routes")

    # Check that reply provides general guidance
    if "一般运输时间" in reply3 or "参考" in reply3:
        print("✅ PASS: Reply provides general shipping time guidance")
    else:
        print("❌ FAIL: Reply missing general guidance")

if __name__ == "__main__":
    try:
        test_shipping_time_scenarios()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
