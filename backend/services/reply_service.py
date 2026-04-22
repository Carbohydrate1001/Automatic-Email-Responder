"""
Reply generation and email processing service.
Generates reply drafts using context-aware templates and routes emails based on confidence threshold.
"""

import re
from datetime import datetime, timezone
from openai import OpenAI
from config import Config
from models.database import get_db_connection
from services.graph_service import EmailSendError


REPLY_SYSTEM_PROMPT = """You are a professional customer service representative for a logistics and trade company.
Write a clear, polite, and helpful reply email to the customer based on the email content and its identified category.
Keep the reply concise (3-5 sentences), professional, and empathetic.
Do NOT use placeholders like [tracking number] — acknowledge the inquiry and explain next steps generically.
Write in the same language as the customer's email."""

COMPANY_SIGNATURE_ZH = "此致，\nMIS2001 Dev Ltd.\n+86 123 456 7890"
COMPANY_SIGNATURE_EN = "Best regards,\nMIS2001 Dev Ltd.\n+86 123 456 7890"
FINANCE_SIGNATURE_ZH = "此致，\nMIS2001 Dev Ltd. 财务部\n+86 123 456 7890"
FINANCE_SIGNATURE_EN = "Best regards,\nMIS2001 Dev Ltd. Finance Department\n+86 123 456 7890"


class ReplyService:
    """Generates reply drafts and orchestrates the full email processing pipeline."""

    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY, base_url=Config.OPENAI_BASE_URL)
        self.model = Config.OPENAI_MODEL
        self.threshold = Config.CONFIDENCE_THRESHOLD

    @staticmethod
    def _extract_sender_local_part(sender: str) -> str:
        local_part = (sender or "").split("@", 1)[0].strip()
        return local_part or "客户"

    @staticmethod
    def _extract_customer_name(sender: str) -> str:
        local_part = ReplyService._extract_sender_local_part(sender)
        normalized = local_part.replace(".", " ").replace("_", " ").replace("-", " ").strip()
        return normalized or "客户"

    @staticmethod
    def _resolve_base_date(received_at: str) -> datetime:
        if not received_at:
            return datetime.now(timezone.utc)
        try:
            parsed = datetime.fromisoformat(received_at.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return datetime.now(timezone.utc)

    @staticmethod
    def _detect_language(text: str) -> str:
        """Detect email language. Returns 'zh' for Chinese, 'en' otherwise."""
        if not text:
            return "en"
        sample = text[:500]
        cjk_count = sum(1 for c in sample if "一" <= c <= "鿿")
        return "zh" if cjk_count / max(len(sample), 1) > 0.15 else "en"

    @staticmethod
    def _extract_order_number_from_text(body: str) -> str | None:
        text = body or ""
        patterns = [
            r"\bORD\d{6,}\b",
            r"订单号\s*[:：]?\s*([A-Za-z0-9\-]{4,})",
            r"order\s*(?:id|number|no\.?)\s*[:：]?\s*([A-Za-z0-9\-]{4,})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        return None

    @staticmethod
    def _extract_tracking_number(body: str) -> str | None:
        """Extract logistics tracking numbers from email body (supports multiple carrier formats)."""
        text = body or ""
        patterns = [
            r"\b(SF\d{12,15})\b",
            r"\b(JT\d{13,15})\b",
            r"\b(YT\d{16,18})\b",
            r"\b([A-Z]{2}\d{9}[A-Z]{2})\b",
            r"tracking\s*(?:number|no\.?|#)\s*[:\s]*([A-Za-z0-9\-]{6,})",
            r"运单号\s*[:\：]?\s*([A-Za-z0-9\-]{6,})",
            r"快递单号\s*[:\：]?\s*([A-Za-z0-9\-]{6,})",
        ]
        for pattern in patterns:
            m = re.search(pattern, text, flags=re.IGNORECASE)
            if m:
                return m.group(1) if m.lastindex else m.group(0)
        return None

    @staticmethod
    def _extract_mentioned_amount(body: str) -> str | None:
        """Extract monetary amounts mentioned in the email body."""
        text = body or ""
        patterns = [
            r"(USD|CNY|EUR|RMB|HKD|GBP)\s*([\d,]+(?:\.\d{1,2})?)",
            r"([\d,]+(?:\.\d{1,2})?)\s*(USD|CNY|EUR|RMB|HKD|GBP)",
            r"人民币\s*([\d,]+(?:\.\d{1,2})?)\s*元",
            r"\$([\d,]+(?:\.\d{2})?)",
        ]
        for pattern in patterns:
            m = re.search(pattern, text, flags=re.IGNORECASE)
            if m:
                return m.group(0)
        return None

    @staticmethod
    def _summarize_exception_full(body: str) -> str:
        """Extract shipping exception description, prioritizing sentences with exception keywords."""
        text = re.sub(r"<[^>]+>", " ", body or "")
        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            return "运输环节出现异常，包裹未按计划完成交付。"

        exception_keywords = [
            "损坏", "破损", "延误", "延迟", "丢失", "扣押", "异常", "投诉", "货损",
            "damage", "delay", "lost", "stuck", "customs", "missing", "broken", "exception",
        ]
        sentences = re.split(r"[。！？\.\!\?]", text)
        relevant = []
        for s in sentences:
            s = s.strip()
            if s and any(kw in s.lower() for kw in exception_keywords):
                relevant.append(s)

        if relevant:
            summary = "；".join(relevant[:3])
            return summary[:300] if len(summary) > 300 else summary

        # Fallback: first 200 characters
        return text[:200] + ("……" if len(text) > 200 else "")

    @staticmethod
    def _select_product(subject: str, body: str, products: list[dict]) -> dict | None:
        if not products:
            return None

        haystack = f"{subject}\n{body}".lower()

        for product in products:
            product_name = str(product.get("product_name", "")).strip().lower()
            if product_name and product_name in haystack:
                return product

            # Check aliases field (JSON array of alternate names)
            aliases_raw = product.get("aliases")
            if aliases_raw:
                try:
                    import json
                    aliases = json.loads(aliases_raw) if isinstance(aliases_raw, str) else aliases_raw
                    for alias in (aliases or []):
                        if str(alias).lower() in haystack:
                            return product
                except Exception:
                    pass

        # Tokenized fuzzy match: all significant words of product name must appear
        for product in products:
            product_name = str(product.get("product_name", "")).strip().lower()
            words = [w for w in product_name.split() if len(w) > 3]
            if words and all(w in haystack for w in words):
                return product

        return products[0]

    # -------------------------------------------------------------------------
    # Template reply generators
    # -------------------------------------------------------------------------

    def _generate_pricing_template_reply(
        self,
        sender: str,
        subject: str,
        body: str,
        received_at: str,
    ) -> str:
        from datetime import timedelta
        from services.company_info_service import CompanyInfoService

        lang = self._detect_language(f"{subject}\n{body}")
        customer_name = self._extract_customer_name(sender)
        products = CompanyInfoService().list_products()
        selected_product = self._select_product(subject, body, products)

        if selected_product:
            product_name = str(selected_product.get("product_name", "未配置产品"))
            unit_price = selected_product.get("unit_price", "N/A")
            currency = str(selected_product.get("currency", "USD"))
            moq = selected_product.get("min_order_quantity", "N/A")
            lead_days = int(selected_product.get("delivery_lead_time_days", 0) or 0)
            eta_date = (self._resolve_base_date(received_at) + timedelta(days=lead_days)).date().isoformat()
            unit_price_text = f"{currency} {unit_price}"
        else:
            product_name = "N/A"
            unit_price_text = "N/A"
            moq = "N/A"
            eta_date = self._resolve_base_date(received_at).date().isoformat()

        if lang == "zh":
            return (
                f"尊敬的 {customer_name}，\n\n"
                "感谢您对我们产品的询价。以下是您所需产品的报价信息：\n"
                f"- 产品名称：{product_name}\n"
                f"- 单价：{unit_price_text}\n"
                f"- 最小订购量：{moq}\n"
                f"- 预计交货期：{eta_date}\n\n"
                "如果您有任何问题或进一步需求，请随时与我们联系。\n\n"
                "感谢您的关注，期待与您的合作！\n\n"
                f"{COMPANY_SIGNATURE_ZH}"
            )
        else:
            return (
                f"Dear {customer_name},\n\n"
                "Thank you for your pricing inquiry. Here is the information for the product you requested:\n"
                f"- Product: {product_name}\n"
                f"- Unit Price: {unit_price_text}\n"
                f"- Minimum Order Quantity: {moq}\n"
                f"- Estimated Delivery: {eta_date}\n\n"
                "If you have any questions or further requirements, please do not hesitate to contact us.\n\n"
                "Thank you for your interest. We look forward to working with you!\n\n"
                f"{COMPANY_SIGNATURE_EN}"
            )

    def _generate_order_cancellation_template_reply(
        self, sender: str, subject: str, body: str
    ) -> str:
        lang = self._detect_language(f"{subject}\n{body}")
        customer_name = self._extract_sender_local_part(sender)
        order_id = (
            self._extract_order_number_from_text(body)
            or self._extract_order_number_from_text(subject)
        )

        if lang == "zh":
            order_ref = f"订单 {order_id} 的" if order_id else "您的"
            return (
                f"尊敬的 {customer_name}，\n\n"
                f"感谢您的来信。我们已收到您关于{order_ref}取消/退款申请。\n\n"
                "我们将在1个工作日内核实订单状态并处理您的申请。退款预计在审核通过后7个工作日内到账，届时您将收到退款通知。\n\n"
                "如有疑问，请随时联系我们的客服团队。\n\n"
                f"{COMPANY_SIGNATURE_ZH}"
            )
        else:
            order_ref = f"for order {order_id}" if order_id else ""
            return (
                f"Dear {customer_name},\n\n"
                f"Thank you for contacting us. We have received your cancellation/refund request {order_ref}.\n\n"
                "Our team will review your order status within 1 business day. "
                "If approved, the refund will be processed within 7 business days and you will be notified.\n\n"
                "Please feel free to reach out if you have any questions.\n\n"
                f"{COMPANY_SIGNATURE_EN}"
            )

    def _generate_order_tracking_template_reply(
        self, sender: str, subject: str, body: str
    ) -> str:
        lang = self._detect_language(f"{subject}\n{body}")
        customer_name = self._extract_sender_local_part(sender)

        order_id = (
            self._extract_order_number_from_text(body)
            or self._extract_order_number_from_text(subject)
            or self._extract_tracking_number(body)
        )

        if lang == "zh":
            if order_id:
                return (
                    f"尊敬的 {customer_name}，\n\n"
                    f"感谢您的来信。我们已收到您关于订单 {order_id} 的物流查询。\n\n"
                    "我们的物流团队正在核查该订单的最新运输状态，将在1个工作日内通过邮件向您反馈详细的物流信息。\n\n"
                    "如需紧急处理，请拨打客服热线 +86 123 456 7890。\n\n"
                    f"{COMPANY_SIGNATURE_ZH}"
                )
            else:
                return (
                    f"尊敬的 {customer_name}，\n\n"
                    "感谢您的来信。为了帮您准确查询物流状态，请提供您的订单号或快递运单号，我们将立即为您跟进。\n\n"
                    f"{COMPANY_SIGNATURE_ZH}"
                )
        else:
            if order_id:
                return (
                    f"Dear {customer_name},\n\n"
                    f"Thank you for contacting us regarding order {order_id}. "
                    "Our logistics team is checking the latest shipping status and will "
                    "update you via email within 1 business day.\n\n"
                    "For urgent assistance, please call us at +86 123 456 7890.\n\n"
                    f"{COMPANY_SIGNATURE_EN}"
                )
            else:
                return (
                    f"Dear {customer_name},\n\n"
                    "Thank you for your inquiry. To help you track your shipment accurately, "
                    "please provide your order number or tracking number and we will look into it right away.\n\n"
                    f"{COMPANY_SIGNATURE_EN}"
                )

    def _generate_shipping_time_template_reply(
        self, sender: str, subject: str, body: str, received_at: str
    ) -> str:
        from datetime import timedelta
        from services.company_info_service import CompanyInfoService

        lang = self._detect_language(f"{subject}\n{body}")
        customer_name = self._extract_sender_local_part(sender)

        products = CompanyInfoService().list_products()
        selected = self._select_product(subject, body, products)

        if selected:
            lead_days = int(selected.get("delivery_lead_time_days", 0) or 0)
            product_name = selected.get("product_name", "")
            eta_date = (self._resolve_base_date(received_at) + timedelta(days=lead_days)).date().isoformat()
            time_info_zh = f"选择 {product_name} 服务，预计运输时长约 {lead_days} 天（预计到达：{eta_date}）"
            time_info_en = (
                f"For {product_name} service, estimated transit time is approximately "
                f"{lead_days} days (estimated arrival: {eta_date})"
            )
        else:
            time_info_zh = "具体运输时长取决于所选服务类型（海运标准约25-35天，空运特快约5-10天）"
            time_info_en = (
                "Transit time depends on the selected service "
                "(Sea Freight Standard: ~25-35 days; Air Freight Express: ~5-10 days)"
            )

        if lang == "zh":
            return (
                f"尊敬的 {customer_name}，\n\n"
                "感谢您的来信。关于运输时间，请参考以下信息：\n"
                f"- {time_info_zh}\n\n"
                "如需获取精确报价和时间安排，请提供起运港、目的港及货物规格，我们将为您量身定制方案。\n\n"
                f"{COMPANY_SIGNATURE_ZH}"
            )
        else:
            return (
                f"Dear {customer_name},\n\n"
                "Thank you for your inquiry about shipping time. Please see the following reference:\n"
                f"- {time_info_en}\n\n"
                "For a precise schedule and quote, please provide the origin port, destination port, "
                "and cargo details and we will tailor a solution for you.\n\n"
                f"{COMPANY_SIGNATURE_EN}"
            )

    def _generate_shipping_exception_template_reply(
        self, sender: str, subject: str, body: str
    ) -> str:
        lang = self._detect_language(f"{subject}\n{body}")
        customer_name = self._extract_sender_local_part(sender)
        order_id = (
            self._extract_order_number_from_text(body)
            or self._extract_order_number_from_text(subject)
            or self._extract_tracking_number(body)
        )
        exception_desc = self._summarize_exception_full(f"{subject}\n{body}")

        if lang == "zh":
            order_ref = f"订单 {order_id}" if order_id else "您的货物"
            return (
                f"尊敬的 {customer_name}，\n\n"
                f"感谢您及时反馈。我们非常抱歉{order_ref}出现了运输异常：\n"
                f"「{exception_desc}」\n\n"
                "我们的异常处理团队已介入跟进，将在24小时内联系您提供解决方案。"
                "在此期间，请保留货物受损的照片及相关单据作为索赔凭证。\n\n"
                f"MIS2001 Dev Ltd. 客服团队\n+86 123 456 7890"
            )
        else:
            order_ref = f"order {order_id}" if order_id else "your shipment"
            return (
                f"Dear {customer_name},\n\n"
                f"We sincerely apologize for the issue with {order_ref}. "
                f"We have noted the following exception:\n\"{exception_desc[:250]}\"\n\n"
                "Our exception handling team has been notified and will contact you "
                "with a resolution within 24 hours. Please retain all photos and "
                "documents of the damaged goods as evidence for claims.\n\n"
                f"MIS2001 Dev Ltd. Customer Service\n+86 123 456 7890"
            )

    def _generate_billing_invoice_template_reply(
        self, sender: str, subject: str, body: str
    ) -> str:
        lang = self._detect_language(f"{subject}\n{body}")
        customer_name = self._extract_sender_local_part(sender)
        mentioned_amount = self._extract_mentioned_amount(body)
        order_id = (
            self._extract_order_number_from_text(body)
            or self._extract_order_number_from_text(subject)
        )

        if lang == "zh":
            ref_parts = []
            if order_id:
                ref_parts.append(f"订单 {order_id}")
            if mentioned_amount:
                ref_parts.append(f"金额 {mentioned_amount}")
            ref_info = "（参考：" + "，".join(ref_parts) + "）" if ref_parts else ""

            return (
                f"尊敬的 {customer_name}，\n\n"
                f"感谢您的来信。我们的财务团队已收到您的账单/发票查询{ref_info}，"
                "将在1-2个工作日内核实相关信息并向您回复。\n\n"
                "如有紧急需求，请直接联系财务部门：finance@mis2001dev.com\n\n"
                f"{FINANCE_SIGNATURE_ZH}"
            )
        else:
            ref_info = f" regarding order {order_id}" if order_id else ""
            return (
                f"Dear {customer_name},\n\n"
                f"Thank you for reaching out about your billing/invoice inquiry{ref_info}. "
                "Our finance team has received your request and will verify the details "
                "and respond within 1-2 business days.\n\n"
                "For urgent matters, please contact: finance@mis2001dev.com\n\n"
                f"{FINANCE_SIGNATURE_EN}"
            )

    def _generate_non_business_template_reply(
        self, sender: str, subject: str = "", body: str = ""
    ) -> str:
        lang = self._detect_language(f"{subject}\n{body}")
        customer_name = self._extract_sender_local_part(sender)

        if lang == "zh":
            return (
                f"尊敬的 {customer_name}，\n\n"
                "感谢您的来信。根据您的邮件内容，当前此邮件并不涉及需要进一步回复的业务内容。"
                "如果您有任何其他问题或需求，欢迎随时与我们联系。\n\n"
                "感谢您的关注！\n\n"
                f"{COMPANY_SIGNATURE_ZH}"
            )
        else:
            return (
                f"Dear {customer_name},\n\n"
                "Thank you for reaching out. Based on the content of your email, "
                "this message does not require a business reply at this time. "
                "If you have any other questions or needs, please feel free to contact us.\n\n"
                "Thank you for your attention!\n\n"
                f"{COMPANY_SIGNATURE_EN}"
            )

    def generate_reply(
        self,
        sender: str,
        received_at: str,
        subject: str,
        body: str,
        category: str,
        reasoning: str,
    ) -> str:
        """Generate reply draft based on category policy."""
        if category in ("pricing_inquiry", "price_inquiry"):
            return self._generate_pricing_template_reply(sender, subject, body, received_at)

        if category == "order_cancellation":
            return self._generate_order_cancellation_template_reply(sender, subject, body)

        if category == "order_tracking":
            return self._generate_order_tracking_template_reply(sender, subject, body)

        if category == "shipping_time":
            return self._generate_shipping_time_template_reply(sender, subject, body, received_at)

        if category == "shipping_exception":
            return self._generate_shipping_exception_template_reply(sender, subject, body)

        if category == "billing_invoice":
            return self._generate_billing_invoice_template_reply(sender, subject, body)

        if category == "non_business":
            return self._generate_non_business_template_reply(sender, subject, body)

        # Fallback: GPT-generated reply for unknown categories
        user_content = (
            f"Customer Email Subject: {subject}\n\n"
            f"Customer Email Body:\n{body[:3000]}\n\n"
            f"Identified Category: {category}\n"
            f"Classification Reasoning: {reasoning}"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": REPLY_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.4,
            max_tokens=500,
        )

        return response.choices[0].message.content.strip()

    def process_email(
        self,
        message_id: str,
        subject: str,
        sender: str,
        received_at: str,
        body: str,
        classification: dict,
        graph_service=None,
        operator: str = "system",
    ) -> dict:
        """
        Full pipeline: persist email + reply, decide auto-send or pending_review.
        Returns the saved email record dict.
        """
        category = classification["category"]
        confidence = classification["confidence"]
        reasoning = classification.get("reasoning", "")
        is_business_related = classification.get("is_business_related", category != "non_business")

        sent_at = None
        retry_count = 0
        last_error = None

        if category == "non_business" or not is_business_related:
            reply_text = self._generate_non_business_template_reply(sender, subject, body)
            status = "ignored_no_reply"
        else:
            reply_text = self.generate_reply(sender, received_at, subject, body, category, reasoning)
            auto_send_eligible = confidence >= self.threshold and confidence >= 0.8
            status = "auto_sent" if auto_send_eligible else "pending_review"

            if status == "auto_sent" and graph_service is not None:
                try:
                    send_result = graph_service.send_reply(message_id, reply_text)
                    retry_count = send_result.get("attempts", 1)
                    graph_service.mark_as_read(message_id)
                    sent_at = datetime.now(timezone.utc).isoformat()
                except EmailSendError as e:
                    status = "send_failed"
                    retry_count = e.attempts
                    last_error = e.last_error

        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO emails (message_id, subject, sender, received_at, body,
                                    category, confidence, reasoning, status, retry_count, last_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(message_id) DO UPDATE SET
                    category=excluded.category,
                    confidence=excluded.confidence,
                    reasoning=excluded.reasoning,
                    status=excluded.status,
                    retry_count=excluded.retry_count,
                    last_error=excluded.last_error
                """,
                (message_id, subject, sender, received_at, body,
                 category, confidence, reasoning, status, retry_count, last_error),
            )
            email_row = conn.execute(
                "SELECT id FROM emails WHERE message_id = ?", (message_id,)
            ).fetchone()
            email_id = email_row["id"]

            conn.execute(
                "INSERT INTO replies (email_id, reply_text, sent_at) VALUES (?, ?, ?)",
                (email_id, reply_text, sent_at),
            )

            conn.execute(
                "INSERT INTO audit_log (email_id, action, operator) VALUES (?, ?, ?)",
                (email_id, status, operator),
            )
            conn.commit()

        return {
            "id": email_id,
            "message_id": message_id,
            "subject": subject,
            "sender": sender,
            "received_at": received_at,
            "category": category,
            "confidence": confidence,
            "status": status,
            "retry_count": retry_count,
            "last_error": last_error,
            "reply_text": reply_text,
        }
