"""
Email classification service.
Uses OpenAI GPT-4o-mini to classify email intent into one of 6 categories.
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
]

CATEGORY_LABELS_ZH = {
    "pricing_inquiry": "询价/报价",
    "order_cancellation": "取消订单/退款",
    "order_tracking": "订单追踪",
    "shipping_time": "运输时间查询",
    "shipping_exception": "运输异常",
    "billing_invoice": "账单/发票",
}

SYSTEM_PROMPT = """You are an expert email classifier for a logistics and trade company's customer service system.
Classify the incoming customer email into exactly one of the following categories:
- pricing_inquiry: Questions about pricing, quotations, or rates
- order_cancellation: Requests to cancel orders or obtain refunds
- order_tracking: Inquiries about order status or logistics tracking
- shipping_time: Questions about shipping duration or estimated arrival
- shipping_exception: Reports of shipping delays, damage, or abnormal events
- billing_invoice: Issues related to billing, invoices, or payment

Respond ONLY with a valid JSON object in this exact format:
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

    def classify_email(self, subject: str, body: str) -> dict:
        """
        Classify an email and return {category, confidence, reasoning}.
        Falls back to a safe default on parse errors.
        """
        user_content = f"Subject: {subject}\n\nBody:\n{body[:3000]}"

        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            max_tokens=200,
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)

        category = result.get("category", "pricing_inquiry")
        if category not in CATEGORIES:
            category = "pricing_inquiry"

        confidence = float(result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        return {
            "category": category,
            "confidence": confidence,
            "reasoning": result.get("reasoning", ""),
            "category_label": CATEGORY_LABELS_ZH.get(category, category),
        }
