"""
Validation Demo Script

Demonstrates the reply quality validation system with visual quality indicators.
Shows how the system ensures quality through multi-stage validation.

Usage:
    python demo_validation.py
"""

from services.validation_service import get_validation_service
from services.validation_report_generator import get_report_generator


def demo_validation():
    """Run validation demonstration with various test cases."""

    validation_service = get_validation_service()
    report_generator = get_report_generator()

    print("=" * 80)
    print("  REPLY QUALITY VALIDATION SYSTEM DEMONSTRATION")
    print("=" * 80)
    print()

    # Test Case 1: High-Quality Reply (Should Pass)
    print("📋 TEST CASE 1: High-Quality Reply")
    print("-" * 80)

    reply_text_1 = """Dear Customer,

Thank you for your inquiry about our products. We appreciate your interest in our services.

We will review your request and get back to you within 2-3 business days with detailed information about pricing and availability.

If you have any urgent questions, please feel free to contact our customer service team.

Best regards,
MIS2001 Dev Ltd.
+86 123 456 7890"""

    email_context_1 = {
        'subject': 'Product Inquiry',
        'body': 'I would like to know more about your laptop products and pricing.'
    }

    result_1 = validation_service.validate_reply_quality(
        reply_text=reply_text_1,
        email_context=email_context_1,
        category='pricing_inquiry',
        company_info={},
        use_llm=False
    )

    print(result_1.get('visual_report', ''))
    print()

    # Test Case 2: Policy Violation (Should Fail)
    print("📋 TEST CASE 2: Policy Violation - Unauthorized Guarantee")
    print("-" * 80)

    reply_text_2 = """Dear Customer,

We guarantee a full refund within 24 hours, no questions asked!

We promise this is the best deal you'll ever get. Only $99.99 for a limited time!

Contact us now!"""

    email_context_2 = {
        'subject': 'Refund Request',
        'body': 'I want to return my order and get a refund.'
    }

    result_2 = validation_service.validate_reply_quality(
        reply_text=reply_text_2,
        email_context=email_context_2,
        category='order_cancellation',
        company_info={},
        use_llm=False
    )

    print(result_2.get('visual_report', ''))
    print()

    # Test Case 3: Inappropriate Tone (Should Fail)
    print("📋 TEST CASE 3: Inappropriate Tone")
    print("-" * 80)

    reply_text_3 = """That's not our problem. You should have read the instructions.

Too bad you didn't check before ordering. We can't help you with that."""

    email_context_3 = {
        'subject': 'Product Issue',
        'body': 'I received a damaged product and need help.'
    }

    result_3 = validation_service.validate_reply_quality(
        reply_text=reply_text_3,
        email_context=email_context_3,
        category='shipping_exception',
        company_info={},
        use_llm=False
    )

    print(result_3.get('visual_report', ''))
    print()

    # Test Case 4: Incomplete Reply (Should Warn)
    print("📋 TEST CASE 4: Incomplete Reply")
    print("-" * 80)

    reply_text_4 = """Thank you for contacting us."""

    email_context_4 = {
        'subject': 'Multiple Questions',
        'body': 'I have three questions: 1) What is the price? 2) What is the delivery time? 3) Do you offer warranty?'
    }

    result_4 = validation_service.validate_reply_quality(
        reply_text=reply_text_4,
        email_context=email_context_4,
        category='pricing_inquiry',
        company_info={},
        use_llm=False
    )

    print(result_4.get('visual_report', ''))
    print()

    # Test Case 5: Potential Hallucination (Should Warn)
    print("📋 TEST CASE 5: Potential Hallucination - Unverified Claims")
    print("-" * 80)

    reply_text_5 = """Dear Customer,

Our premium laptop model X9000 features:
- 64GB RAM
- 2TB SSD
- RTX 5090 Graphics Card
- Price: $1,299.99

This product is available for immediate delivery within 24 hours."""

    email_context_5 = {
        'subject': 'Laptop Specifications',
        'body': 'What are the specs of your laptops?'
    }

    result_5 = validation_service.validate_reply_quality(
        reply_text=reply_5,
        email_context=email_context_5,
        category='pricing_inquiry',
        company_info={},
        use_llm=False
    )

    print(result_5.get('visual_report', ''))
    print()

    # Summary Statistics
    print("=" * 80)
    print("  VALIDATION SUMMARY")
    print("=" * 80)
    print()

    test_cases = [
        ("High-Quality Reply", result_1),
        ("Policy Violation", result_2),
        ("Inappropriate Tone", result_3),
        ("Incomplete Reply", result_4),
        ("Potential Hallucination", result_5)
    ]

    passed_count = sum(1 for _, r in test_cases if r['passed'])
    failed_count = len(test_cases) - passed_count

    print(f"Total Test Cases: {len(test_cases)}")
    print(f"✅ Passed: {passed_count}")
    print(f"❌ Failed: {failed_count}")
    print()

    print("Quality Scores:")
    for name, result in test_cases:
        score = result['overall_quality_score']
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        print(f"  {name:30s} {bar} {score:.2f} {status}")

    print()
    print("=" * 80)
    print("  KEY FEATURES DEMONSTRATED")
    print("=" * 80)
    print()
    print("✓ Multi-Stage Validation Pipeline")
    print("  - Policy compliance checking (rule-based)")
    print("  - Hallucination detection (fact-checking)")
    print("  - Quality assessment (LLM or rule-based)")
    print()
    print("✓ Visual Quality Indicators")
    print("  - Color-coded quality scores")
    print("  - Progress bars and status icons")
    print("  - Detailed dimension breakdowns")
    print()
    print("✓ Issue Detection & Reporting")
    print("  - Blocking issues (prevent auto-send)")
    print("  - Warnings (flag for review)")
    print("  - Clear explanations and reasoning")
    print()
    print("✓ Automated Decision Making")
    print("  - AUTO_SEND for high-quality replies")
    print("  - MANUAL_REVIEW for problematic replies")
    print("  - Transparent decision criteria")
    print()

    # Generate HTML report for first test case
    print("=" * 80)
    print("  GENERATING HTML REPORT")
    print("=" * 80)
    print()

    html_report = report_generator.generate_html_report(
        validation_result=result_1,
        reply_text=reply_text_1,
        email_context=email_context_1,
        output_path="../reports/validation_demo_report.html"
    )

    print("✓ HTML report generated: backend/reports/validation_demo_report.html")
    print("  Open this file in a browser to see the full visual report.")
    print()


if __name__ == '__main__':
    demo_validation()
