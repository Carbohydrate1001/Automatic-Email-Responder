"""
Reply generation and email processing service.
Generates GPT reply drafts and routes emails based on confidence threshold.
Integrates rubric-based scoring for auto-send decisions.
"""

from datetime import datetime, timezone
from openai import OpenAI
from config import Config
from models.database import get_db_connection
from services.graph_service import EmailSendError
from services.config_loader import get_config_loader
from services.scoring_service import get_scoring_service
from services.validation_service import get_validation_service


REPLY_SYSTEM_PROMPT = """You are a professional customer service representative for a logistics and trade company.
Write a clear, polite, and helpful reply email to the customer based on the email content and its identified category.
Keep the reply concise (3-5 sentences), professional, and empathetic.
Do NOT use placeholders like [tracking number] — acknowledge the inquiry and explain next steps generically.
Write in the same language as the customer's email."""


class ReplyService:
    """Generates reply drafts and orchestrates the full email processing pipeline."""

    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY, base_url=Config.OPENAI_BASE_URL)
        self.model = Config.OPENAI_MODEL
        self.config_loader = get_config_loader()
        self.scoring_service = get_scoring_service()
        self.validation_service = get_validation_service()
        self.threshold = self.config_loader.get_global_threshold('confidence_threshold')
        self.auto_send_minimum = self.config_loader.get_global_threshold('auto_send_minimum_confidence')

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
    def _select_product(subject: str, body: str, products: list[dict]) -> dict | None:
        if not products:
            return None

        haystack = f"{subject}\n{body}".lower()
        for product in products:
            product_name = str(product.get("product_name", "")).strip().lower()
            if product_name and product_name in haystack:
                return product

        return products[0]

    def _generate_pricing_template_reply(
        self,
        sender: str,
        subject: str,
        body: str,
        received_at: str,
    ) -> str:
        from datetime import timedelta
        from services.company_info_service import CompanyInfoService

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
            product_name = "未配置产品"
            unit_price_text = "N/A"
            moq = "N/A"
            eta_date = self._resolve_base_date(received_at).date().isoformat()

        return (
            f"尊敬的 {customer_name}，\n\n"
            "感谢您对我们产品的询价。以下是您所需产品的报价信息：\n"
            f"- 产品名称：{product_name}\n"
            f"- 单价：{unit_price_text}\n"
            f"- 最小订购量：{moq}\n"
            f"- 预计交货期：{eta_date}\n\n"
            "如果您有任何问题或进一步需求，请随时与我们联系。\n\n"
            "感谢您的关注，期待与您的合作！\n\n"
            "此致，\n"
            "MIS2001 Dev Ltd.\n"
            "+86 123 456 7890"
        )

    @staticmethod
    def _generate_order_number() -> str:
        from random import randint

        return f"ORD{randint(100000, 999999)}"

    @staticmethod
    def _generate_billing_number() -> str:
        from random import randint

        return f"BILL{randint(100000, 999999)}"

    @staticmethod
    def _generate_invoice_info() -> str:
        from random import choice, randint

        invoice_type = choice(["电子普通发票", "电子专用发票", "纸质发票"])
        invoice_code = f"INV{randint(1000000, 9999999)}"
        return f"{invoice_type}（发票编号：{invoice_code}）"

    @staticmethod
    def _generate_billing_amount() -> str:
        from random import randint

        amount = randint(500, 50000)
        return f"CNY {amount}.00"

    def _generate_billing_invoice_template_reply(self, sender: str) -> str:
        customer_name = self._extract_sender_local_part(sender)
        billing_no = self._generate_billing_number()
        amount = self._generate_billing_amount()
        payment_status = "已付款"
        invoice_info = self._generate_invoice_info()

        return (
            f"尊敬的 {customer_name}，\n\n"
            "感谢您的来信。以下是您的账单及付款信息：\n"
            f"- 账单号：{billing_no}\n"
            f"- 账单金额：{amount}\n"
            f"- 付款状态：{payment_status}\n"
            f"- 发票信息：{invoice_info}\n\n"
            "如有任何疑问，请随时联系我们的财务部门。感谢您的配合与支持！\n\n"
            "此致，\n"
            "MIS2001 Dev Ltd. 财务部\n"
            "+86 123 456 7890"
        )

    def _generate_non_business_template_reply(self, sender: str) -> str:
        customer_name = self._extract_sender_local_part(sender)
        return (
            f"尊敬的 {customer_name}，\n\n"
            "感谢您的来信。根据您的邮件内容，当前此邮件并不涉及需要进一步回复的业务内容。如果您有任何其他问题或需求，欢迎随时与我们联系。\n\n"
            "感谢您的关注！\n\n"
            "此致，\n"
            "MIS2001 Dev Ltd.\n"
            "+86 123 456 7890"
        )

    def _generate_order_cancellation_template_reply(self, sender: str) -> str:
        customer_name = self._extract_sender_local_part(sender)
        return (
            f"尊敬的 {customer_name}，\n\n"
            "感谢您的来信。我们已经收到您的取消订单请求，并将尽快处理您的退款申请。\n\n"
            "退款预计将在七个工作日内完成，您将收到相应的退款通知。如果有任何问题，您可以随时联系客户服务团队。\n\n"
            "我们为此次不便向您表示歉意，并感谢您的理解。\n\n"
            "此致，\n"
            "MIS2001 Dev Ltd.\n"
            "+86 123 456 7890"
        )

    def _generate_order_tracking_template_reply(self, sender: str) -> str:
        customer_name = self._extract_sender_local_part(sender)
        order_id = self._generate_order_number()
        current_status = "运输中"
        eta_date = "2026/3/16"

        return (
            f"尊敬的 {customer_name}，\n\n"
            "感谢您的来信。以下是您订单的当前物流状态：\n"
            f"- 订单号：{order_id}\n"
            f"- 当前状态：{current_status}\n"
            f"- 预计到达日期：{eta_date}\n\n"
            "如需更多帮助，您可以随时通过我们的客服热线或邮件联系我们。\n\n"
            "感谢您的耐心等待，祝您有愉快的一天！\n\n"
            "此致，\n"
            "MIS2001 Dev Ltd.\n"
            "+86 123 456 7890"
        )

    @staticmethod
    def _generate_route() -> str:
        from random import sample

        cities = ["深圳", "新加坡", "鹿特丹", "上海", "香港", "迪拜", "汉堡", "洛杉矶"]
        route_cities = sample(cities, 3)
        return " -> ".join(route_cities)

    def _generate_shipping_time_template_reply(self, sender: str) -> str:
        customer_name = self._extract_sender_local_part(sender)
        route = self._generate_route()
        eta_date = "2026/3/16"

        return (
            f"尊敬的 {customer_name}，\n\n"
            "感谢您的来信。根据您的需求，以下是您的货物的运输信息：\n"
            f"- 运输路线：{route}\n"
            f"- 预计到达时间：{eta_date}\n\n"
            "如需更多信息，请随时与我们联系。\n\n"
            "感谢您的支持，期待为您提供优质的服务！\n\n"
            "此致，\n"
            "MIS2001 Dev Ltd.\n"
            "+86 123 456 7890"
        )

    @staticmethod
    def _summarize_exception_from_body(body: str) -> str:
        import re

        text = re.sub(r"<[^>]+>", " ", body or "")
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return "运输环节出现异常，包裹未按计划完成交付。"

        text = text[:80]
        if len(text) == 80:
            text = text.rstrip("，。；;,. ") + "……"
        return text

    @staticmethod
    def _extract_order_number_from_text(body: str) -> str | None:
        import re

        text = body or ""
        patterns = [
            r"\bORD\d{6,}\b",
            r"订单号\s*[:：]?\s*([A-Za-z0-9\-]{4,})",
            r"order\s*(?:id|number)\s*[:：]?\s*([A-Za-z0-9\-]{4,})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        return None

    def _generate_shipping_exception_template_reply(self, sender: str, body: str) -> str:
        customer_name = self._extract_sender_local_part(sender)
        order_id = self._extract_order_number_from_text(body) or self._generate_order_number()
        exception_desc = self._summarize_exception_from_body(body)
        solution = "请客户预约专人上门回收货物，公司会重新派送一批"

        return (
            f"尊敬的 {customer_name}，\n\n"
            f"感谢您的反馈。关于您的订单 {order_id}，我们注意到出现了以下运输异常情况：\n"
            f"- 异常情况：{exception_desc}\n"
            f"- 解决方案：{solution}\n\n"
            "我们深感抱歉给您带来的不便，并会尽快处理此问题。您可以通过以下方式与我们进一步沟通：[二维码]\n\n"
            "再次为此给您带来的困扰表示歉意，感谢您的理解。\n\n"
            "此致，\n"
            "MIS2001 Dev Ltd.\n"
            "+86 123 456 7890"
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
            return self._generate_order_cancellation_template_reply(sender)

        if category == "order_tracking":
            return self._generate_order_tracking_template_reply(sender)

        if category == "shipping_time":
            return self._generate_shipping_time_template_reply(sender)

        if category == "shipping_exception":
            return self._generate_shipping_exception_template_reply(sender, body)

        if category == "billing_invoice":
            return self._generate_billing_invoice_template_reply(sender)

        if category == "non_business":
            return self._generate_non_business_template_reply(sender)

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
            reply_text = self._generate_non_business_template_reply(sender)
            status = "ignored_no_reply"
            auto_send_rubric_scores = None
        else:
            reply_text = self.generate_reply(sender, received_at, subject, body, category, reasoning)

            # Phase 2: Use rubric-based scoring for auto-send decision
            auto_send_rubric_scores = None
            auto_send_eligible = confidence >= self.threshold and confidence >= self.auto_send_minimum

            # Phase 3: Validate reply quality before auto-send
            validation_result = None
            try:
                # Score auto-send readiness
                rubric_result = self.scoring_service.score_auto_send_readiness(
                    subject=subject,
                    body=body,
                    reply_text=reply_text,
                    category=category,
                    use_llm=True
                )
                auto_send_rubric_scores = rubric_result

                # Use rubric recommendation if available
                if 'auto_send_recommended' in rubric_result:
                    auto_send_eligible = rubric_result['auto_send_recommended']

                # Validate reply quality (hallucination, policy, tone, completeness)
                if auto_send_eligible:
                    validation_result = self.validation_service.validate_reply_quality(
                        reply_text=reply_text,
                        email_context={'subject': subject, 'body': body},
                        category=category,
                        company_info={},  # TODO: Load from company_info_service
                        use_llm=True
                    )

                    # Block auto-send if validation fails
                    if not validation_result.get('passed', False):
                        auto_send_eligible = False
                        print(f"Validation failed: {validation_result.get('blocking_issues', [])}")

            except Exception as e:
                # Fallback to original threshold-based decision
                print(f"Auto-send rubric scoring or validation failed, using threshold-based decision: {e}")

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
            # Extract rubric scores from classification
            classification_rubric_scores = classification.get("rubric_scores")
            import json

            # Upsert email record with rubric scores
            conn.execute(
                """
                INSERT INTO emails (message_id, subject, sender, received_at, body,
                                    category, confidence, reasoning, status, retry_count, last_error,
                                    classification_rubric_scores, auto_send_rubric_scores, rubric_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(message_id) DO UPDATE SET
                    category=excluded.category,
                    confidence=excluded.confidence,
                    reasoning=excluded.reasoning,
                    status=excluded.status,
                    retry_count=excluded.retry_count,
                    last_error=excluded.last_error,
                    classification_rubric_scores=excluded.classification_rubric_scores,
                    auto_send_rubric_scores=excluded.auto_send_rubric_scores,
                    rubric_version=excluded.rubric_version
                """,
                (message_id, subject, sender, received_at, body,
                 category, confidence, reasoning, status, retry_count, last_error,
                 json.dumps(classification_rubric_scores) if classification_rubric_scores else None,
                 json.dumps(auto_send_rubric_scores) if auto_send_rubric_scores else None,
                 'v1.0'),

            )
            email_row = conn.execute(
                "SELECT id FROM emails WHERE message_id = ?", (message_id,)
            ).fetchone()
            email_id = email_row["id"]

            # Save reply with validation results
            conn.execute(
                """INSERT INTO replies (email_id, reply_text, sent_at, reply_validation_scores,
                                       validation_passed, validation_issues)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (email_id, reply_text, sent_at,
                 json.dumps(validation_result) if validation_result else None,
                 1 if (validation_result and validation_result.get('passed', True)) else 0,
                 json.dumps(validation_result.get('blocking_issues', [])) if validation_result else None),
            )

            # Audit log
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
