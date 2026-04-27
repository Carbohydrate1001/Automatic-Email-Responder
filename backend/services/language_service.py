"""
Language Detection Service

Detects email language (Chinese/English) using Unicode character analysis.
Supports mixed-language detection and language-specific template routing.
No external dependencies — uses Unicode ranges for CJK detection.
"""

import re
import unicodedata
from typing import Dict, Any, Optional, Tuple
from utils.logger import get_logger


logger = get_logger('language_service')


class Language:
    """Supported language codes."""
    CHINESE = "zh"
    ENGLISH = "en"
    MIXED = "mixed"
    UNKNOWN = "unknown"


# CJK Unicode ranges
_CJK_RANGES = [
    (0x4E00, 0x9FFF),    # CJK Unified Ideographs
    (0x3400, 0x4DBF),    # CJK Unified Ideographs Extension A
    (0xF900, 0xFAFF),    # CJK Compatibility Ideographs
    (0x2E80, 0x2EFF),    # CJK Radicals Supplement
    (0x3000, 0x303F),    # CJK Symbols and Punctuation
    (0xFF00, 0xFFEF),    # Fullwidth Forms
]


def _is_cjk(char: str) -> bool:
    cp = ord(char)
    return any(lo <= cp <= hi for lo, hi in _CJK_RANGES)


def _is_latin(char: str) -> bool:
    try:
        name = unicodedata.name(char, '')
        return 'LATIN' in name
    except ValueError:
        return False


class LanguageService:
    """Detects language and provides language-aware routing."""

    def _preprocess_for_detection(self, text: str) -> str:
        """
        Preprocess text to remove noise that interferes with language detection.
        Strips HTML tags, email addresses, URLs, quoted text, and signatures.
        """
        if not text:
            return ""

        # Strip HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # Remove email addresses (they're always Latin characters)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', ' ', text)

        # Remove URLs
        text = re.sub(r'https?://[^\s]+', ' ', text)
        text = re.sub(r'www\.[^\s]+', ' ', text)

        # Remove quoted text markers (>, |, etc. at line start)
        text = re.sub(r'^[>|]+.*$', '', text, flags=re.MULTILINE)

        # Remove common email signature patterns (English)
        signature_patterns = [
            r'(?i)best regards.*$',
            r'(?i)sincerely.*$',
            r'(?i)kind regards.*$',
            r'(?i)thanks.*$',
            r'(?i)sent from my.*$',
            r'(?i)get outlook for.*$',
        ]
        for pattern in signature_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE | re.DOTALL)

        # Remove common Chinese signature patterns
        text = re.sub(r'此致.*$', '', text, flags=re.MULTILINE | re.DOTALL)
        text = re.sub(r'敬上.*$', '', text, flags=re.MULTILINE | re.DOTALL)

        # Remove phone numbers (international format)
        text = re.sub(r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}', ' ', text)

        return text

    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the primary language of the text.

        Uses asymmetric detection: CJK presence is a strong signal for Chinese,
        since English emails rarely contain CJK characters, but Chinese business
        emails frequently contain English (company names, product codes, etc.).

        Returns:
            Dict with language code, confidence, and character breakdown.
        """
        if not text or not text.strip():
            return {'language': Language.UNKNOWN, 'confidence': 0.0, 'details': {}}

        # Preprocess: strip HTML tags, email addresses, URLs, and common noise
        preprocessed = self._preprocess_for_detection(text)

        # Remove whitespace, digits, and punctuation for character analysis
        cleaned = re.sub(r'[\s\d\W]+', '', preprocessed)
        if not cleaned:
            return {'language': Language.UNKNOWN, 'confidence': 0.0, 'details': {}}

        total = len(cleaned)
        cjk_count = sum(1 for c in cleaned if _is_cjk(c))
        latin_count = sum(1 for c in cleaned if _is_latin(c))

        cjk_ratio = cjk_count / total
        latin_ratio = latin_count / total

        # Asymmetric detection: CJK presence is a strong signal for Chinese
        # Even 15% CJK characters likely means a Chinese email with English mixed in
        if cjk_ratio >= 0.15:
            language = Language.CHINESE
            confidence = min(0.95, 0.6 + cjk_ratio * 0.4)
        elif cjk_ratio > 0.05:
            # Some CJK but not much - likely mixed, lean toward Chinese
            language = Language.MIXED
            confidence = 0.7
            # Store which language dominates for mixed handling
            primary = Language.CHINESE if cjk_ratio >= latin_ratio * 0.3 else Language.ENGLISH
        elif latin_ratio > 0.7:
            # Strongly Latin with no CJK - English
            language = Language.ENGLISH
            confidence = min(0.95, 0.5 + latin_ratio * 0.5)
        elif latin_ratio > 0.4:
            # Moderately Latin with no CJK - probably English
            language = Language.ENGLISH
            confidence = 0.75
        else:
            # Not enough signal
            language = Language.UNKNOWN
            confidence = 0.3
            primary = Language.CHINESE  # Default to Chinese when unknown

        result = {
            'language': language,
            'confidence': round(confidence, 2),
            'details': {
                'cjk_ratio': round(cjk_ratio, 3),
                'latin_ratio': round(latin_ratio, 3),
                'total_chars': total,
                'cjk_chars': cjk_count,
                'latin_chars': latin_count,
            }
        }

        # Add primary_language for mixed content handling
        if language == Language.MIXED:
            result['details']['primary_language'] = primary

        logger.info("Language detected", {
            'language': language,
            'confidence': result['confidence'],
            'cjk_ratio': cjk_ratio,
            'latin_ratio': latin_ratio
        })

        return result

    def get_primary_language(self, text: str) -> str:
        """Return just the language code."""
        result = self.detect_language(text)
        lang = result['language']
        if lang == Language.MIXED:
            return result['details'].get('primary_language', Language.CHINESE)
        if lang == Language.UNKNOWN:
            return Language.CHINESE
        return lang

    def get_reply_language(self, subject: str, body: str) -> str:
        """
        Determine which language to use for the reply.
        Replies should match the customer's language.
        """
        full_text = f"{subject or ''}\n{body or ''}"
        return self.get_primary_language(full_text)

    def get_greeting(self, language: str, customer_name: str) -> str:
        """Get language-appropriate greeting."""
        if language == Language.CHINESE:
            return f"尊敬的 {customer_name}，"
        return f"Dear {customer_name},"

    def get_closing(self, language: str) -> str:
        """Get language-appropriate closing."""
        if language == Language.CHINESE:
            return "此致，\nMIS2001 Dev Ltd.\n+86 123 456 7890"
        return "Best regards,\nMIS2001 Dev Ltd.\n+86 123 456 7890"

    def get_template_key(self, category: str, language: str) -> str:
        """Get the template key for a category and language combination."""
        return f"{category}_{language}"

    def is_chinese(self, text: str) -> bool:
        """Quick check if text is primarily Chinese."""
        return self.get_primary_language(text) == Language.CHINESE

    def is_english(self, text: str) -> bool:
        """Quick check if text is primarily English."""
        return self.get_primary_language(text) == Language.ENGLISH


# Singleton
_language_service = None


def get_language_service() -> LanguageService:
    global _language_service
    if _language_service is None:
        _language_service = LanguageService()
    return _language_service
