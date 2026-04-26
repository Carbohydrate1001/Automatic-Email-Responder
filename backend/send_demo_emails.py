#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive test cases for all business scenarios.
Sends demo emails to test the email processing system.

Usage:
    python send_demo_emails.py [--category CATEGORY] [--scenario SCENARIO]

Examples:
    python send_demo_emails.py                           # Send all test cases
    python send_demo_emails.py --category order_cancellation  # Test only refund scenarios
    python send_demo_emails.py --scenario missing_info   # Test only missing info scenarios
"""

import requests
import json
import argparse
from typing import List, Dict

# Backend API endpoint
API_BASE = "http://localhost:5000"

# Test order data (must match init_orders.py)
TEST_ORDERS = {
    "ORD123456": "customer@example.com",      # in_transit
    "ORD654321": "cn_customer@example.com",   # not_shipped
    "ORD789012": "buyer@example.com",         # delivered
    "ORD111222": "urgent@example.com",        # exception
    "ORD333444": "test@example.com",          # pending
}


class TestCase:
    """Represents a single test case."""

    def __init__(self, name: str, category: str, scenario: str,
                 subject: str, body: str, sender: str,
                 expected_status: str, description: str):
        self.name = name
        self.category = category
        self.scenario = scenario
        self.subject = subject
        self.body = body
        self.sender = sender
        self.expected_status = expected_status
        self.description = description


# ============================================================================
# Test Cases Definition
# ============================================================================

TEST_CASES: List[TestCase] = [

    # ------------------------------------------------------------------------
    # 1. ORDER CANCELLATION / REFUND (订单取消/退款)
    # ------------------------------------------------------------------------

    TestCase(
        name="refund_valid_order",
        category="order_cancellation",
        scenario="complete_info",
        subject="申请退款",
        body="您好，我想申请退款。订单号是 ORD123456，因为不需要了。谢谢。",
        sender="customer@example.com",
        expected_status="auto_sent",
        description="Valid refund request with correct order number and ownership"
    ),

    TestCase(
        name="refund_order_not_found",
        category="order_cancellation",
        scenario="invalid_order",
        subject="退款申请",
        body="我要退款，订单号是 ORD999999",
        sender="customer@example.com",
        expected_status="auto_sent",
        description="Refund request with non-existent order number - should ask to verify"
    ),

    TestCase(
        name="refund_missing_order_number",
        category="order_cancellation",
        scenario="missing_info",
        subject="申请退款",
        body="你好，我想退款，产品不符合预期。",
        sender="customer@example.com",
        expected_status="auto_sent",
        description="Refund request without order number - should ask for order number"
    ),

    TestCase(
        name="refund_wrong_owner",
        category="order_cancellation",
        scenario="unauthorized",
        subject="退款",
        body="订单号 ORD123456 我要退款",
        sender="wrong_user@example.com",
        expected_status="auto_sent",
        description="Refund request for order owned by different user - should reject"
    ),

    TestCase(
        name="cancel_order_delivered",
        category="order_cancellation",
        scenario="complete_info",
        subject="取消订单",
        body="订单号 ORD789012，我想取消这个订单",
        sender="buyer@example.com",
        expected_status="auto_sent",
        description="Cancel request for already delivered order"
    ),

    # ------------------------------------------------------------------------
    # 2. ORDER TRACKING (订单追踪)
    # ------------------------------------------------------------------------

    TestCase(
        name="tracking_valid_order",
        category="order_tracking",
        scenario="complete_info",
        subject="查询订单状态",
        body="你好，我想查询订单 ORD123456 的物流状态",
        sender="customer@example.com",
        expected_status="auto_sent",
        description="Valid tracking request with order number"
    ),

    TestCase(
        name="tracking_missing_order_number",
        category="order_tracking",
        scenario="missing_info",
        subject="订单在哪里",
        body="我的货物到哪里了？",
        sender="customer@example.com",
        expected_status="auto_sent",
        description="Tracking request without order number - should ask for it"
    ),

    TestCase(
        name="tracking_order_not_found",
        category="order_tracking",
        scenario="invalid_order",
        subject="查询物流",
        body="订单号 ORD888888 现在到哪了？",
        sender="customer@example.com",
        expected_status="auto_sent",
        description="Tracking request for non-existent order"
    ),

    TestCase(
        name="tracking_no_tracking_number",
        category="order_tracking",
        scenario="complete_info",
        subject="物流查询",
        body="订单 ORD654321 的物流信息",
        sender="cn_customer@example.com",
        expected_status="auto_sent",
        description="Tracking request for order without tracking number (not_shipped)"
    ),

    # ------------------------------------------------------------------------
    # 3. SHIPPING TIME (物流时间)
    # ------------------------------------------------------------------------

    TestCase(
        name="shipping_time_general",
        category="shipping_time",
        scenario="complete_info",
        subject="多久能到？",
        body="请问从中国到美国的海运一般需要多长时间？",
        sender="inquiry@example.com",
        expected_status="auto_sent",
        description="General shipping time inquiry without specific order"
    ),

    TestCase(
        name="shipping_time_specific_order",
        category="shipping_time",
        scenario="complete_info",
        subject="订单什么时候到",
        body="订单 ORD123456 大概什么时候能到？",
        sender="customer@example.com",
        expected_status="auto_sent",
        description="Shipping time inquiry for specific order"
    ),

    TestCase(
        name="shipping_time_route_inquiry",
        category="shipping_time",
        scenario="complete_info",
        subject="运输时效咨询",
        body="从上海到洛杉矶的空运需要几天？",
        sender="inquiry@example.com",
        expected_status="auto_sent",
        description="Shipping time inquiry for specific route"
    ),

    # ------------------------------------------------------------------------
    # 4. SHIPPING EXCEPTION (物流异常)
    # ------------------------------------------------------------------------

    TestCase(
        name="shipping_exception_delay",
        category="shipping_exception",
        scenario="complete_info",
        subject="货物延误",
        body="订单 ORD111222 已经延误了，什么情况？",
        sender="urgent@example.com",
        expected_status="pending_review",
        description="Shipping delay complaint - high priority, may need manual review"
    ),

    TestCase(
        name="shipping_exception_damage",
        category="shipping_exception",
        scenario="complete_info",
        subject="货物损坏",
        body="订单 ORD789012 收到的货物有损坏，怎么处理？",
        sender="buyer@example.com",
        expected_status="pending_review",
        description="Damaged goods report - requires manual review"
    ),

    TestCase(
        name="shipping_exception_missing_order",
        category="shipping_exception",
        scenario="missing_info",
        subject="物流异常",
        body="我的货物好像出问题了，一直没有更新",
        sender="customer@example.com",
        expected_status="auto_sent",
        description="Exception report without order number - should ask for it"
    ),

    TestCase(
        name="shipping_exception_lost",
        category="shipping_exception",
        scenario="complete_info",
        subject="货物丢失",
        body="订单 ORD123456 显示已签收但我没收到",
        sender="customer@example.com",
        expected_status="pending_review",
        description="Lost package claim - requires investigation"
    ),

    # ------------------------------------------------------------------------
    # 5. PRICING INQUIRY (价格咨询)
    # ------------------------------------------------------------------------

    TestCase(
        name="pricing_sea_freight",
        category="pricing_inquiry",
        scenario="complete_info",
        subject="海运价格咨询",
        body="请问从深圳到纽约的海运价格是多少？20尺柜。",
        sender="inquiry@example.com",
        expected_status="auto_sent",
        description="Sea freight pricing inquiry with route and container size"
    ),

    TestCase(
        name="pricing_air_freight",
        category="pricing_inquiry",
        scenario="complete_info",
        subject="空运报价",
        body="100公斤货物从上海到伦敦空运多少钱？",
        sender="inquiry@example.com",
        expected_status="auto_sent",
        description="Air freight pricing inquiry with weight"
    ),

    TestCase(
        name="pricing_general",
        category="pricing_inquiry",
        scenario="incomplete_info",
        subject="价格咨询",
        body="你们的运费怎么算？",
        sender="inquiry@example.com",
        expected_status="auto_sent",
        description="General pricing inquiry without specifics - should ask for details"
    ),

    TestCase(
        name="pricing_bulk_discount",
        category="pricing_inquiry",
        scenario="complete_info",
        subject="批量优惠",
        body="如果我每月发10个柜，有折扣吗？",
        sender="inquiry@example.com",
        expected_status="pending_review",
        description="Bulk discount inquiry - may require custom pricing"
    ),

    # ------------------------------------------------------------------------
    # 6. BILLING / INVOICE (账单/发票)
    # ------------------------------------------------------------------------

    TestCase(
        name="invoice_request",
        category="billing_invoice",
        scenario="complete_info",
        subject="申请发票",
        body="订单 ORD123456 需要开具发票，公司名称：XX物流有限公司，税号：123456789",
        sender="customer@example.com",
        expected_status="auto_sent",
        description="Invoice request with complete information"
    ),

    TestCase(
        name="invoice_missing_order",
        category="billing_invoice",
        scenario="missing_info",
        subject="发票",
        body="我需要发票",
        sender="customer@example.com",
        expected_status="auto_sent",
        description="Invoice request without order number - should ask for it"
    ),

    TestCase(
        name="billing_dispute",
        category="billing_invoice",
        scenario="complete_info",
        subject="账单有误",
        body="订单 ORD123456 的账单金额不对，应该是2000不是2400",
        sender="customer@example.com",
        expected_status="pending_review",
        description="Billing dispute - requires manual review"
    ),

    TestCase(
        name="payment_confirmation",
        category="billing_invoice",
        scenario="complete_info",
        subject="付款确认",
        body="订单 ORD654321 我已经付款了，请确认",
        sender="cn_customer@example.com",
        expected_status="auto_sent",
        description="Payment confirmation request"
    ),

    # ------------------------------------------------------------------------
    # 7. NON-BUSINESS (非业务邮件)
    # ------------------------------------------------------------------------

    TestCase(
        name="non_business_newsletter",
        category="non_business",
        scenario="spam",
        subject="【促销】限时优惠！",
        body="亲爱的用户，我们的产品正在促销，点击链接了解更多...",
        sender="marketing@spam.com",
        expected_status="pending_review",
        description="Marketing newsletter - should be filtered as non-business"
    ),

    TestCase(
        name="non_business_notification",
        category="non_business",
        scenario="system",
        subject="Your cloud storage is almost full",
        body="Hi, your OneDrive storage is 95% full. Upgrade now to get more space.",
        sender="no-reply@microsoft.com",
        expected_status="pending_review",
        description="System notification - not related to business"
    ),

    TestCase(
        name="non_business_gibberish",
        category="non_business",
        scenario="spam",
        subject="asdfghjkl",
        body="qwertyuiop zxcvbnm",
        sender="random@test.com",
        expected_status="pending_review",
        description="Gibberish email - should be filtered"
    ),

    TestCase(
        name="non_business_personal",
        category="non_business",
        scenario="personal",
        subject="周末聚餐",
        body="嗨，这周末一起吃饭吗？",
        sender="friend@personal.com",
        expected_status="pending_review",
        description="Personal email - not business related"
    ),

    # ------------------------------------------------------------------------
    # 8. EDGE CASES (边界情况)
    # ------------------------------------------------------------------------

    TestCase(
        name="edge_empty_body",
        category="non_business",
        scenario="edge",
        subject="(no subject)",
        body="",
        sender="test@example.com",
        expected_status="pending_review",
        description="Empty email body - should be filtered"
    ),

    TestCase(
        name="edge_multiple_orders",
        category="order_tracking",
        scenario="edge",
        subject="多个订单查询",
        body="我想查询 ORD123456 和 ORD654321 的状态",
        sender="customer@example.com",
        expected_status="auto_sent",
        description="Multiple order numbers in one email - should handle first one"
    ),

    TestCase(
        name="edge_mixed_intent",
        category="order_cancellation",
        scenario="edge",
        subject="退款和发票",
        body="订单 ORD123456 我要退款，另外还需要开发票",
        sender="customer@example.com",
        expected_status="pending_review",
        description="Mixed intents - may require manual handling"
    ),

    TestCase(
        name="edge_urgent_keywords",
        category="order_tracking",
        scenario="edge",
        subject="【紧急】订单查询",
        body="非常紧急！订单 ORD111222 必须今天到！",
        sender="urgent@example.com",
        expected_status="auto_sent",
        description="Urgent keywords - should still auto-send if clear intent"
    ),
]


# ============================================================================
# Test Execution Functions
# ============================================================================

def send_test_email(test_case: TestCase) -> Dict:
    """Send a single test email to the backend API."""
    payload = {
        "subject": test_case.subject,
        "body": test_case.body,
        "sender": test_case.sender,
        "received_at": "2026-04-26T10:00:00Z"
    }

    try:
        response = requests.post(
            f"{API_BASE}/api/emails/process",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def print_test_result(test_case: TestCase, result: Dict, index: int, total: int):
    """Print formatted test result."""
    print(f"\n{'='*80}")
    print(f"Test {index}/{total}: {test_case.name}")
    print(f"{'='*80}")
    print(f"Category: {test_case.category}")
    print(f"Scenario: {test_case.scenario}")
    print(f"Description: {test_case.description}")
    print(f"\nInput:")
    print(f"  Subject: {test_case.subject}")
    print(f"  Body: {test_case.body[:100]}{'...' if len(test_case.body) > 100 else ''}")
    print(f"  Sender: {test_case.sender}")

    if "error" in result:
        print(f"\n❌ ERROR: {result['error']}")
        return

    actual_status = result.get("status", "unknown")
    actual_category = result.get("category", "unknown")
    confidence = result.get("confidence", 0)

    print(f"\nResult:")
    print(f"  Classified as: {actual_category} (confidence: {confidence:.2f})")
    print(f"  Status: {actual_status}")
    print(f"  Expected: {test_case.expected_status}")

    # Check if result matches expectation
    status_match = actual_status == test_case.expected_status
    status_icon = "✅" if status_match else "⚠️"

    print(f"\n{status_icon} Status Match: {status_match}")

    if result.get("reply_text"):
        print(f"\nGenerated Reply:")
        print(f"  {result['reply_text'][:200]}{'...' if len(result['reply_text']) > 200 else ''}")

    if result.get("rubric_scores"):
        scores = result["rubric_scores"]
        print(f"\nRubric Scores:")
        print(f"  Weighted: {scores.get('weighted_score', 'N/A')}/3.0")
        print(f"  Auto-send: {scores.get('auto_send_recommended', 'N/A')}")


def run_tests(category_filter: str = None, scenario_filter: str = None):
    """Run test cases with optional filters."""

    # Filter test cases
    filtered_cases = TEST_CASES
    if category_filter:
        filtered_cases = [tc for tc in filtered_cases if tc.category == category_filter]
    if scenario_filter:
        filtered_cases = [tc for tc in filtered_cases if tc.scenario == scenario_filter]

    if not filtered_cases:
        print("No test cases match the filters.")
        return

    print(f"\n{'='*80}")
    print(f"Running {len(filtered_cases)} test cases")
    if category_filter:
        print(f"Category filter: {category_filter}")
    if scenario_filter:
        print(f"Scenario filter: {scenario_filter}")
    print(f"{'='*80}")

    results = []
    for i, test_case in enumerate(filtered_cases, 1):
        result = send_test_email(test_case)
        print_test_result(test_case, result, i, len(filtered_cases))
        results.append({
            "test_case": test_case.name,
            "expected": test_case.expected_status,
            "actual": result.get("status", "error"),
            "match": result.get("status") == test_case.expected_status
        })

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    total = len(results)
    passed = sum(1 for r in results if r["match"])
    failed = total - passed

    print(f"Total: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")

    if failed > 0:
        print(f"\nFailed tests:")
        for r in results:
            if not r["match"]:
                print(f"  - {r['test_case']}: expected {r['expected']}, got {r['actual']}")


def list_test_cases():
    """List all available test cases."""
    print(f"\n{'='*80}")
    print("Available Test Cases")
    print(f"{'='*80}\n")

    by_category = {}
    for tc in TEST_CASES:
        if tc.category not in by_category:
            by_category[tc.category] = []
        by_category[tc.category].append(tc)

    for category, cases in sorted(by_category.items()):
        print(f"\n{category.upper()} ({len(cases)} cases):")
        for tc in cases:
            print(f"  - {tc.name}: {tc.description}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Send demo emails to test the email processing system"
    )
    parser.add_argument(
        "--category",
        choices=[
            "order_cancellation", "order_tracking", "shipping_time",
            "shipping_exception", "pricing_inquiry", "billing_invoice",
            "non_business"
        ],
        help="Filter by category"
    )
    parser.add_argument(
        "--scenario",
        choices=[
            "complete_info", "missing_info", "invalid_order",
            "unauthorized", "incomplete_info", "spam", "system",
            "personal", "edge"
        ],
        help="Filter by scenario"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all test cases without running them"
    )

    args = parser.parse_args()

    if args.list:
        list_test_cases()
    else:
        run_tests(args.category, args.scenario)


if __name__ == "__main__":
    main()
