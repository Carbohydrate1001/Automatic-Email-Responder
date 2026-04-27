"""
Test script to verify order validation functionality.
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from services.order_service import get_order_service, OrderNotFoundError
from services.reply_service import ReplyService


def test_order_validation():
    """Test order validation scenarios."""
    print("=" * 60)
    print("Testing Order Validation Functionality")
    print("=" * 60)

    order_service = get_order_service()
    reply_service = ReplyService()

    # Test 1: Valid order with correct customer
    print("\n[Test 1] Valid order with correct customer")
    print("-" * 60)
    try:
        order = order_service.validate_order_ownership("ORD123456", "customer@example.com")
        print(f"[PASS] Order found: {order['order_number']}")
        print(f"       Product: {order['product_name']}")
        print(f"       Status: {order['order_status']} / {order['shipping_status']}")
    except OrderNotFoundError as e:
        print(f"[FAIL] {e}")

    # Test 2: Valid order with wrong customer
    print("\n[Test 2] Valid order with wrong customer")
    print("-" * 60)
    try:
        order = order_service.validate_order_ownership("ORD123456", "wrong@example.com")
        print(f"[FAIL] Should have raised OrderNotFoundError")
    except OrderNotFoundError as e:
        print(f"[PASS] Correctly rejected: {e}")

    # Test 3: Non-existent order
    print("\n[Test 3] Non-existent order")
    print("-" * 60)
    try:
        order = order_service.validate_order_ownership("ORD999999", "customer@example.com")
        print(f"[FAIL] Should have raised OrderNotFoundError")
    except OrderNotFoundError as e:
        print(f"[PASS] Correctly rejected: {e}")

    # Test 4: Order cancellation reply with valid order
    print("\n[Test 4] Order cancellation reply with valid order")
    print("-" * 60)
    reply = reply_service._generate_order_cancellation_template_reply(
        sender="customer@example.com",
        body="I want to cancel my order ORD123456"
    )
    if "ORD123456" in reply and "Sea Freight" in reply:
        print("[PASS] Reply contains order details")
        print(f"Reply preview: {reply[:200]}...")
    else:
        print("[FAIL] Reply missing order details")

    # Test 5: Order cancellation reply with invalid order
    print("\n[Test 5] Order cancellation reply with invalid order")
    print("-" * 60)
    reply = reply_service._generate_order_cancellation_template_reply(
        sender="customer@example.com",
        body="I want to cancel my order ORD999999"
    )
    if "未能找到相关记录" in reply or "核实订单号" in reply:
        print("[PASS] Reply correctly indicates order not found")
        print(f"Reply preview: {reply[:200]}...")
    else:
        print("[FAIL] Reply should indicate order not found")

    # Test 6: Order tracking reply with valid order
    print("\n[Test 6] Order tracking reply with valid order")
    print("-" * 60)
    reply = reply_service._generate_order_tracking_template_reply(
        sender="buyer@example.com",
        body="Where is my order ORD789012?"
    )
    if "ORD789012" in reply and "已送达" in reply:
        print("[PASS] Reply contains order tracking details")
        print(f"Reply preview: {reply[:200]}...")
    else:
        print("[FAIL] Reply missing tracking details")

    # Test 7: Shipping exception reply with valid order
    print("\n[Test 7] Shipping exception reply with valid order")
    print("-" * 60)
    reply = reply_service._generate_shipping_exception_template_reply(
        sender="urgent@example.com",
        body="My package ORD111222 is delayed and damaged"
    )
    if "ORD111222" in reply and "Air Freight" in reply:
        print("[PASS] Reply contains exception handling details")
        print(f"Reply preview: {reply[:200]}...")
    else:
        print("[FAIL] Reply missing exception details")

    # Test 8: Order status update
    print("\n[Test 8] Order status update")
    print("-" * 60)
    result = order_service.update_order_status("ORD333444", order_status="confirmed")
    if result:
        updated_order = order_service.find_order_by_number("ORD333444")
        if updated_order['order_status'] == 'confirmed':
            print(f"[PASS] Order status updated successfully")
            print(f"       New status: {updated_order['order_status']}")
        else:
            print(f"[FAIL] Status not updated")
    else:
        print(f"[FAIL] Update failed")

    print("\n" + "=" * 60)
    print("Testing Complete")
    print("=" * 60)


if __name__ == "__main__":
    test_order_validation()
