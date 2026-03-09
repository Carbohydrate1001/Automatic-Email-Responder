"""
Email classification service.
Uses OpenAI GPT-4o-mini to classify email intent into business categories.
"""

import json
from openai import OpenAI
from config import Config

CATEGORIES = [
    "pricing_inquiry",       # 询价/报价
    "order_cancellation",    # 取消订单/退款
    "order_tracking",        # 订单追踪/物流状态
    "shipping_time",         # 运输时间/预计到达
    "shipping_exception",    # 运输异常/延误/损坏
    "billing_invoice",       # 账单/发票/付款
    "non_business",          # 非业务邮件（无需回复）
]

CATEGORY_LABELS_ZH = {
    "pricing_inquiry": "询价/报价",
    "order_cancellation": "取消订单/退款",
    "order_tracking": "订单追踪",
    "shipping_time": "运输时间查询",
    "shipping_exception": "运输异常",
    "billing_invoice": "账单/发票",
    "non_business": "非业务邮件（无需回复）",
}

BUSINESS_HINTS = [
    "order", "shipment", "shipping", "tracking", "invoice", "billing", "refund", "quotation", "quote", "logistics",
    "订单", "物流", "追踪", "发票", "账单", "退款", "报价", "运费", "到货", "运输",
]

NON_BUSINESS_HINTS = [
    "onedrive", "microsoft 365", "outlook tips", "newsletter", "unsubscribe", "promotion", "backup", "windows", "security alert",
    "verification code", "meeting invitation", "calendar", "teams", "cloud storage", "photo", "video",
    "系统通知", "运营通知", "营销", "活动", "订阅", "退订", "备份", "云盘", "验证码", "安全提醒", "会议邀请", "照片", "视频",
]

BUSINESS_GATE_PROMPT = """You are a gatekeeper for a logistics/trade customer-service mailbox.
Determine whether the incoming email is a real business-service request relevant to logistics/trade operations.

Respond ONLY with valid JSON:
{
  "is_business_related": <true|false>,
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<brief one-sentence explanation>"
}

Set is_business_related=false for newsletters, account/system notifications, promotions, cloud storage tips, security reminders, and other non-service content."""

CATEGORY_PROMPT = """You are an expert email classifier for a logistics and trade company's customer service system.
Classify the incoming email into exactly one category:
- pricing_inquiry: pricing, quotation, rate questions
- order_cancellation: cancellation or refund requests
- order_tracking: order status / logistics tracking
- shipping_time: shipping duration / ETA
- shipping_exception: delay, damage, abnormal shipping events
- billing_invoice: billing, invoice, payment issues
- non_business: newsletters, marketing, account/system notifications, internal announcements, or messages unrelated to the company's logistics/trade business

Important rules:
1) If the email is not a customer service business request to this company, choose non_business.
2) Do NOT map generic technology/account/storage/security messages to logistics categories.
3) Only use high confidence (>0.85) when evidence is explicit.

Respond ONLY with valid JSON:
{
  "category": "<one of the category names above>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<brief one-sentence explanation>"
}"""



class ClassificationService:
    """Classifies customer service emails using OpenAI GPT."""

    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY, base_url=Config.OPENAI_BASE_URL)
        self.model = Config.OPENAI_MODEL

    @staticmethod
    def _contains_any(text: str, keywords: list[str]) -> bool:
        lowered = text.lower()
        return any(keyword in lowered for keyword in keywords)

    def _rule_based_non_business(self, subject: str, body: str) -> bool:
        text = f"{subject}\n{body[:3000]}"
        has_business = self._contains_any(text, BUSINESS_HINTS)
        has_non_business = self._contains_any(text, NON_BUSINESS_HINTS)
        return has_non_business and not has_business

    def _gate_business_relevance(self, subject: str, body: str) -> dict:
        user_content = f"Subject: {subject}\n\nBody:\n{body[:3000]}"
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": BUSINESS_GATE_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.0,
            max_tokens=120,
        )
        raw = response.choices[0].message.content
        result = json.loads(raw)
        is_business_related = bool(result.get("is_business_related", False))
        confidence = float(result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
        reasoning = result.get("reasoning", "")
        return {
            "is_business_related": is_business_related,
            "business_confidence": confidence,
            "business_reasoning": reasoning,
        }

    def classify_email(self, subject: str, body: str) -> dict:
        """
        Classify an email and return {category, confidence, reasoning}.
        Falls back to a safe default on parse errors.
        """
        if self._rule_based_non_business(subject, body):
            category = "non_business"
            return {
                "category": category,
                "confidence": 0.98,
                "reasoning": "Rule-based filter: detected non-business notification/marketing content.",
                "category_label": CATEGORY_LABELS_ZH.get(category, category),
                "is_business_related": False,
                "business_confidence": 0.98,
            }

        gate = self._gate_business_relevance(subject, body)
        if not gate["is_business_related"] and gate["business_confidence"] >= 0.6:
            category = "non_business"
            return {
                "category": category,
                "confidence": max(0.85, gate["business_confidence"]),
                "reasoning": gate["business_reasoning"] or "Business gate: email judged as non-business.",
                "category_label": CATEGORY_LABELS_ZH.get(category, category),
                "is_business_related": False,
                "business_confidence": gate["business_confidence"],
            }

        user_content = f"Subject: {subject}\n\nBody:\n{body[:3000]}"

        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": CATEGORY_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            max_tokens=200,
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)

        category = result.get("category", "non_business")
        if category not in CATEGORIES:
            category = "non_business"

        confidence = float(result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        if category != "non_business" and confidence >= 0.9 and self._rule_based_non_business(subject, body):
            category = "non_business"
            confidence = 0.85

        return {
            "category": category,
            "confidence": confidence,
            "reasoning": result.get("reasoning", ""),
            "category_label": CATEGORY_LABELS_ZH.get(category, category),
            "is_business_related": category != "non_business",
            "business_confidence": gate["business_confidence"],
        }


