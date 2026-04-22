"""
Email classification service.
Uses OpenAI GPT-4o-mini to classify email intent into business categories.
"""

import json
import os
from pathlib import Path
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

BUSINESS_GATE_PROMPT = """You are a strict gatekeeper for a logistics/trade customer-service mailbox.
Your ONLY job: determine if this email is a direct service request from a customer about logistics, shipping, orders, billing, or pricing.

ALWAYS return is_business_related=false for:
- Microsoft/Google/cloud service notifications (OneDrive, Teams, 365 subscription, etc.)
- Newsletter, promotional, or marketing emails
- Password reset, security alerts, verification codes
- Meeting invitations or calendar events
- Internal company announcements or HR notices
- Subscription renewal notices for non-logistics services

ONLY return is_business_related=true if the email is clearly from a customer asking for help with:
- Logistics/shipping services, pricing, quotes
- Order status, tracking, cancellations, returns
- Invoices, billing, or payment confirmation

Respond ONLY with valid JSON:
{
  "is_business_related": <true|false>,
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<brief one-sentence explanation>"
}"""


def _load_few_shot_examples() -> list[dict]:
    """Load few-shot classification examples from JSON file. Returns empty list on failure."""
    path = Path(os.path.dirname(__file__)).parent / "data" / "few_shot_examples.json"
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("examples", [])
    except Exception:
        return []


def _build_category_prompt() -> str:
    """Dynamically build the category classification prompt with few-shot examples."""
    examples = _load_few_shot_examples()

    prompt = """You are an expert email classifier for a logistics and trade company's customer service system.

Classify the incoming email into EXACTLY ONE of these categories:

CATEGORY DEFINITIONS:
- pricing_inquiry: Customer asks for price quotes, rates, or cost estimates for shipping services or products. Key signals: "how much", "quote", "price", "rate", "报价", "运费多少", "费用".
- order_cancellation: Customer explicitly requests to cancel an order AND/OR requests a refund. Key signal: cancel/refund INTENT, NOT just reporting damage without refund request.
- order_tracking: Customer asks about the CURRENT STATUS or LOCATION of a specific existing shipment/order. Key signals: "where is", "status of order", "tracking update", "到哪了", "物流状态".
- shipping_time: Customer asks about transit DURATION or ETA in general (not tracking a specific in-transit order). Key signals: "how long", "how many days", "ETA", "几天到", "运输时间".
- shipping_exception: Customer REPORTS a problem with an existing shipment that has already occurred: delay, damage, lost, stuck at customs. Key signal: a problem has ALREADY occurred, often with a specific order/tracking number.
- billing_invoice: Customer asks about invoices, payment confirmation, billing errors, or financial documentation. Key signals: invoice, payment sent, billing issue, "发票", "付款确认".
- non_business: System notifications, newsletters, marketing, internal announcements, account alerts, or anything NOT a customer service request about logistics/trade.

DISAMBIGUATION RULES (apply in order when ambiguous):
1. "运费多少" / "how much to ship" / asks about PRICE → pricing_inquiry (asking about cost, not time)
2. "几天到" / "how long does it take" / asks about DURATION without a specific in-transit order → shipping_time
3. "我的货到哪了" / "where is my order [ID]" / asks about CURRENT STATUS of a specific shipment → order_tracking
4. "货延误/损坏/丢失" / "shipment delayed, damaged, or lost" → shipping_exception (problem has ALREADY occurred)
5. "退款" / "cancel order" WITHOUT a damage-but-keep-order context → order_cancellation
6. "货损但要重发不退款" / reports damage but wants replacement, NOT refund → shipping_exception
7. "付款确认" / "invoice wrong" / "billing issue" → billing_invoice

"""

    if examples:
        prompt += "EXAMPLES (use these to learn the precise boundary between similar categories):\n\n"
        by_category: dict[str, list] = {}
        for ex in examples:
            cat = ex.get("category", "")
            by_category.setdefault(cat, []).append(ex)

        for cat, exs in by_category.items():
            prompt += f"--- {cat} ---\n"
            for ex in exs:
                label = ex.get("label", "POSITIVE")
                subject = ex.get("subject", "")
                body_preview = ex.get("body", "")[:150]
                note = ex.get("note", "")
                prompt += f"[{label}] Subject: {subject}\nBody: {body_preview}\nWhy: {note}\n\n"

    prompt += """IMPORTANT RULES:
1. If the email is NOT a customer service request to this logistics/trade company → non_business.
2. Do NOT assign logistics categories to generic tech/account/storage/security notifications.
3. Use confidence > 0.85 ONLY when the intent signal is explicit and unambiguous.
4. For ambiguous cases, apply the DISAMBIGUATION RULES above before deciding.

Respond ONLY with valid JSON:
{
  "category": "<one of the 7 category names>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<one sentence citing the specific signal that determined the category>"
}"""

    return prompt


# Pre-build at module load time to avoid re-reading file on every request
CATEGORY_PROMPT = _build_category_prompt()


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
        # Raised threshold from 0.6 to 0.7 to reduce false non-business classifications
        if not gate["is_business_related"] and gate["business_confidence"] >= 0.7:
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
