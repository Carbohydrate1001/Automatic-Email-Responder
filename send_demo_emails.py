from __future__ import annotations

import smtplib
import ssl
import time
from dataclasses import dataclass
from email.message import EmailMessage

SENDER_EMAIL = "122090121@link.cuhk.edu.cn"
RECIPIENT_EMAIL = "centauric47@outlook.com"
SMTP_HOST = "smtp.office365.com"
SMTP_PORT = 587
SMTP_USERNAME = ""
SMTP_PASSWORD = ""
SEND_INTERVAL_SECONDS = 1


@dataclass
class DemoEmail:
    category: str
    subject: str
    body: str


def build_demo_emails() -> list[DemoEmail]:
    return [
        DemoEmail(
            category="pricing_inquiry",
            subject="报价咨询 - 海运标准服务",
            body=(
                "您好，\n\n"
                "我们想咨询 Sea Freight (Standard) 的最新报价。"
                "请提供单价、最小起订量（MOQ）以及预计交付周期。\n\n"
                "谢谢。"
            ),
        ),
        DemoEmail(
            category="order_cancellation",
            subject="申请取消订单 ORD782311",
            body=(
                "您好，\n\n"
                "由于采购计划调整，我们希望取消订单 ORD782311。"
                "请确认取消处理进度以及退款时间安排。\n\n"
                "感谢配合。"
            ),
        ),
        DemoEmail(
            category="order_tracking",
            subject="订单 ORD993120 物流追踪查询",
            body=(
                "您好客服团队，\n\n"
                "请协助提供订单 ORD993120 的最新物流状态。"
                "我们需要当前运输进度与配送状态信息。\n\n"
                "谢谢。"
            ),
        ),
        DemoEmail(
            category="shipping_time",
            subject="运输时效咨询 - 深圳到鹿特丹",
            body=(
                "您好，\n\n"
                "请问从深圳到鹿特丹的运输周期大约多久？"
                "烦请告知预计到达时间（ETA）与整体时效。\n\n"
                "辛苦了。"
            ),
        ),
        DemoEmail(
            category="shipping_exception",
            subject="紧急：订单 ORD556677 出现运输异常",
            body=(
                "您好，\n\n"
                "订单 ORD556677 在运输过程中出现异常，"
                "货物有破损且到达时间延迟。"
                "请尽快提供处理方案和后续安排。\n\n"
                "谢谢。"
            ),
        ),
        DemoEmail(
            category="billing_invoice",
            subject="账单与发票信息确认请求",
            body=(
                "您好财务团队，\n\n"
                "烦请提供我们最近一笔运费付款对应的账单与发票信息。"
                "我们需要确认账单金额、发票明细以及付款状态。\n\n"
                "感谢支持。"
            ),
        ),
        DemoEmail(
            category="non_business",
            subject="每周资讯：云存储效率与安全小贴士",
            body=(
                "您好，\n\n"
                "这是本周的产品资讯邮件，内容包括云存储备份建议、"
                "账号安全设置技巧以及推广活动通知。"
                "如不需要，可随时在营销中心退订。\n\n"
                "祝好。"
            ),
        ),
    ]



def validate_config() -> None:
    required = {
        "SENDER_EMAIL": SENDER_EMAIL,
        "RECIPIENT_EMAIL": RECIPIENT_EMAIL,
        "SMTP_USERNAME": SMTP_USERNAME,
        "SMTP_PASSWORD": SMTP_PASSWORD,
    }
    missing = [k for k, v in required.items() if not v.strip()]
    if missing:
        raise ValueError(f"请先填写以下配置项: {', '.join(missing)}")


def send_demo_emails() -> None:
    validate_config()
    emails = build_demo_emails()

    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.starttls(context=context)
        server.login(SMTP_USERNAME, SMTP_PASSWORD)

        for idx, item in enumerate(emails, start=1):
            msg = EmailMessage()
            msg["From"] = SENDER_EMAIL
            msg["To"] = RECIPIENT_EMAIL
            msg["Subject"] = f"[DEMO:{item.category}] {item.subject}"
            msg.set_content(item.body)

            server.send_message(msg)
            print(f"[{idx}/{len(emails)}] 已发送: {item.category}")
            time.sleep(SEND_INTERVAL_SECONDS)


if __name__ == "__main__":
    send_demo_emails()
