"""
Unit tests for Language Detection Service.

Tests cover:
- Chinese text detection
- English text detection
- Mixed language detection
- Edge cases (empty, numbers-only, etc.)
- Reply language determination
- Greeting/closing generation
"""

import pytest
from services.language_service import (
    LanguageService, Language, get_language_service
)


class TestLanguageDetection:
    """Test language detection accuracy."""

    def setup_method(self):
        self.service = LanguageService()

    def test_detect_chinese(self):
        text = "您好，我想了解从上海到洛杉矶的海运价格。"
        result = self.service.detect_language(text)
        assert result['language'] == Language.CHINESE
        assert result['confidence'] >= 0.7

    def test_detect_english(self):
        text = "I would like to know the price for sea freight from Shanghai to LA."
        result = self.service.detect_language(text)
        assert result['language'] == Language.ENGLISH
        assert result['confidence'] >= 0.7

    def test_detect_mixed_language(self):
        text = "Hello, 我想了解 sea freight 的价格。Please send quotation."
        result = self.service.detect_language(text)
        assert result['language'] in (Language.MIXED, Language.CHINESE, Language.ENGLISH)

    def test_detect_empty_string(self):
        result = self.service.detect_language("")
        assert result['language'] == Language.UNKNOWN
        assert result['confidence'] == 0.0

    def test_detect_whitespace_only(self):
        result = self.service.detect_language("   \n\t  ")
        assert result['language'] == Language.UNKNOWN

    def test_detect_chinese_email_subject(self):
        result = self.service.detect_language("询价 - 海运服务")
        assert result['language'] == Language.CHINESE

    def test_detect_english_email_subject(self):
        result = self.service.detect_language("Price inquiry for sea freight")
        assert result['language'] == Language.ENGLISH

    def test_detect_chinese_with_numbers(self):
        text = "订单号12345的物流状态是什么？"
        result = self.service.detect_language(text)
        assert result['language'] == Language.CHINESE

    def test_detect_english_with_numbers(self):
        text = "What is the status of order #12345?"
        result = self.service.detect_language(text)
        assert result['language'] == Language.ENGLISH

    def test_details_contain_ratios(self):
        text = "这是中文测试"
        result = self.service.detect_language(text)
        assert 'cjk_ratio' in result['details']
        assert 'latin_ratio' in result['details']
        assert result['details']['cjk_ratio'] > 0


class TestPrimaryLanguage:
    """Test primary language extraction."""

    def setup_method(self):
        self.service = LanguageService()

    def test_primary_chinese(self):
        assert self.service.get_primary_language("你好世界") == Language.CHINESE

    def test_primary_english(self):
        assert self.service.get_primary_language("Hello world") == Language.ENGLISH

    def test_is_chinese(self):
        assert self.service.is_chinese("这是中文") is True
        assert self.service.is_chinese("This is English") is False

    def test_is_english(self):
        assert self.service.is_english("This is English") is True
        assert self.service.is_english("这是中文") is False


class TestReplyLanguage:
    """Test reply language determination."""

    def setup_method(self):
        self.service = LanguageService()

    def test_reply_in_chinese_for_chinese_email(self):
        lang = self.service.get_reply_language("询价", "我想了解海运价格")
        assert lang == Language.CHINESE

    def test_reply_in_english_for_english_email(self):
        lang = self.service.get_reply_language("Price inquiry", "I need a quote for shipping")
        assert lang == Language.ENGLISH

    def test_reply_language_uses_body_primarily(self):
        lang = self.service.get_reply_language("RE:", "请问运费多少？我需要从上海发货到纽约。")
        assert lang == Language.CHINESE


class TestGreetingClosing:
    """Test language-specific greetings and closings."""

    def setup_method(self):
        self.service = LanguageService()

    def test_chinese_greeting(self):
        greeting = self.service.get_greeting(Language.CHINESE, "张三")
        assert "尊敬的" in greeting
        assert "张三" in greeting

    def test_english_greeting(self):
        greeting = self.service.get_greeting(Language.ENGLISH, "John")
        assert "Dear" in greeting
        assert "John" in greeting

    def test_chinese_closing(self):
        closing = self.service.get_closing(Language.CHINESE)
        assert "此致" in closing

    def test_english_closing(self):
        closing = self.service.get_closing(Language.ENGLISH)
        assert "Best regards" in closing


class TestTemplateKey:
    """Test template key generation."""

    def setup_method(self):
        self.service = LanguageService()

    def test_template_key_chinese(self):
        key = self.service.get_template_key("pricing_inquiry", Language.CHINESE)
        assert key == "pricing_inquiry_zh"

    def test_template_key_english(self):
        key = self.service.get_template_key("order_tracking", Language.ENGLISH)
        assert key == "order_tracking_en"


class TestSingleton:
    """Test singleton pattern."""

    def test_same_instance(self):
        s1 = get_language_service()
        s2 = get_language_service()
        assert s1 is s2
