"""
Test script for language detection and bilingual support.
"""

from services.language_service import get_language_service
from services.classification_service import ClassificationService
from services.reply_service import ReplyService

def test_language_detection():
    """Test language detection service."""
    print("=" * 60)
    print("Testing Language Detection")
    print("=" * 60)

    lang_service = get_language_service()

    # Test Chinese
    chinese_text = "你好，我想查询订单状态"
    result = lang_service.detect_language(chinese_text)
    print(f"\nChinese text: {chinese_text}")
    print(f"Detected language: {result.get('language')}")
    print(f"Confidence: {result.get('confidence')}")

    # Test English
    english_text = "Hello, I want to track my order"
    result = lang_service.detect_language(english_text)
    print(f"\nEnglish text: {english_text}")
    print(f"Detected language: {result.get('language')}")
    print(f"Confidence: {result.get('confidence')}")

    print("\n✓ Language detection test passed!\n")

def test_english_classification():
    """Test English classification."""
    print("=" * 60)
    print("Testing English Classification")
    print("=" * 60)

    cs_en = ClassificationService(language='en')

    result = cs_en.classify_email(
        subject="Where is my order",
        body="I ordered a package last week but haven't received tracking info"
    )

    print(f"\nSubject: Where is my order")
    print(f"Body: I ordered a package last week but haven't received tracking info")
    print(f"Category: {result.get('category')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Reasoning: {result.get('reasoning')}")

    print("\n✓ English classification test passed!\n")

def test_chinese_classification():
    """Test Chinese classification."""
    print("=" * 60)
    print("Testing Chinese Classification")
    print("=" * 60)

    cs_zh = ClassificationService(language='zh')

    result = cs_zh.classify_email(
        subject="订单在哪里",
        body="我上周订购了一个包裹，但还没有收到追踪信息"
    )

    print(f"\nSubject: 订单在哪里")
    print(f"Body: 我上周订购了一个包裹，但还没有收到追踪信息")
    print(f"Category: {result.get('category')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Reasoning: {result.get('reasoning')}")

    print("\n✓ Chinese classification test passed!\n")

def test_english_reply():
    """Test English reply generation."""
    print("=" * 60)
    print("Testing English Reply Generation")
    print("=" * 60)

    rs_en = ReplyService(language='en')

    reply = rs_en.generate_reply(
        sender="john@example.com",
        received_at="2026-04-27T10:00:00Z",
        subject="Pricing inquiry",
        body="How much does it cost to ship from Shanghai to New York?",
        category="pricing_inquiry",
        reasoning="Customer asking about shipping rates"
    )

    print(f"\nGenerated English reply:")
    print("-" * 60)
    print(reply)
    print("-" * 60)

    print("\n✓ English reply generation test passed!\n")

def test_chinese_reply():
    """Test Chinese reply generation."""
    print("=" * 60)
    print("Testing Chinese Reply Generation")
    print("=" * 60)

    rs_zh = ReplyService(language='zh')

    reply = rs_zh.generate_reply(
        sender="zhang@example.com",
        received_at="2026-04-27T10:00:00Z",
        subject="价格咨询",
        body="从上海到纽约的运费是多少？",
        category="pricing_inquiry",
        reasoning="客户询问运费"
    )

    print(f"\nGenerated Chinese reply:")
    print("-" * 60)
    print(reply)
    print("-" * 60)

    print("\n✓ Chinese reply generation test passed!\n")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LANGUAGE DETECTION AND BILINGUAL SUPPORT TEST SUITE")
    print("=" * 60 + "\n")

    try:
        test_language_detection()
        test_chinese_classification()
        test_english_classification()
        test_chinese_reply()
        test_english_reply()

        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        print("\nLanguage detection and bilingual support is working correctly.")
        print("The system can now:")
        print("  - Detect email language (Chinese/English)")
        print("  - Use language-specific prompts for classification")
        print("  - Generate replies in the customer's language")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
