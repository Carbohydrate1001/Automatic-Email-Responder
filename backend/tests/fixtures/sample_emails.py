"""
Sample email data for testing.
"""

SAMPLE_EMAILS = {
    "pricing_inquiry": {
        "subject": "Price inquiry for sea freight",
        "body": "Dear Sir/Madam,\n\nI would like to know the price for sea freight service from Shanghai to Los Angeles. Please send me a quotation for 20ft container.\n\nBest regards,\nJohn Doe",
        "sender": "john.doe@example.com",
        "expected_category": "pricing_inquiry"
    },
    "order_cancellation": {
        "subject": "Cancel my order #12345",
        "body": "Hi,\n\nI need to cancel my order #12345 placed yesterday. Please process the refund.\n\nThanks",
        "sender": "customer@example.com",
        "expected_category": "order_cancellation"
    },
    "order_tracking": {
        "subject": "Where is my shipment?",
        "body": "Hello,\n\nI placed an order last week (Order #67890) and haven't received any tracking information. Can you please provide the tracking number?\n\nRegards",
        "sender": "buyer@example.com",
        "expected_category": "order_tracking"
    },
    "shipping_time": {
        "subject": "How long does shipping take?",
        "body": "Hi,\n\nI'm interested in your air freight service. How long does it typically take to ship from Beijing to New York?\n\nThank you",
        "sender": "inquiry@example.com",
        "expected_category": "shipping_time"
    },
    "shipping_exception": {
        "subject": "My package is delayed",
        "body": "Dear Support,\n\nMy shipment (tracking #ABC123) was supposed to arrive yesterday but it's still in transit. What happened?\n\nUrgent!",
        "sender": "urgent@example.com",
        "expected_category": "shipping_exception"
    },
    "billing_invoice": {
        "subject": "Invoice request for order #99999",
        "body": "Hello,\n\nI need an invoice for my recent order #99999. Please send it to this email address.\n\nBest regards",
        "sender": "accounting@example.com",
        "expected_category": "billing_invoice"
    },
    "non_business": {
        "subject": "OneDrive storage is almost full",
        "body": "Your OneDrive storage is 95% full. Upgrade to get more space.\n\nMicrosoft 365 Team",
        "sender": "no-reply@microsoft.com",
        "expected_category": "non_business"
    },
    "multi_intent": {
        "subject": "Cancel order and track another",
        "body": "Hi,\n\nI need to cancel order #11111 and get a refund. Also, can you provide tracking for order #22222?\n\nThanks",
        "sender": "multi@example.com",
        "expected_category": "order_cancellation"
    },
    "incomplete": {
        "subject": "Question",
        "body": "Hi",
        "sender": "vague@example.com",
        "expected_category": "non_business"
    },
    "very_long": {
        "subject": "Detailed inquiry about multiple services",
        "body": "Dear Team,\n\n" + "This is a very long email. " * 500 + "\n\nPlease advise.\n\nRegards",
        "sender": "verbose@example.com",
        "expected_category": "pricing_inquiry"
    },
    "chinese": {
        "subject": "询价",
        "body": "您好，\n\n我想了解从上海到洛杉矶的海运价格。请发送报价单。\n\n谢谢",
        "sender": "chinese@example.com",
        "expected_category": "pricing_inquiry"
    },
    "mixed_language": {
        "subject": "Price inquiry 询价",
        "body": "Hello,\n\n我想了解 sea freight 的价格。Please send quotation.\n\nThanks",
        "sender": "bilingual@example.com",
        "expected_category": "pricing_inquiry"
    },
    "chinese_cancellation": {
        "subject": "取消订单",
        "body": "您好，\n\n我需要取消订单号为 #54321 的订单，请尽快处理退款。\n\n谢谢",
        "sender": "cn_customer@example.com",
        "expected_category": "order_cancellation"
    },
    "chinese_tracking": {
        "subject": "查询物流状态",
        "body": "你好，\n\n我的订单 #67890 已经发货一周了，但还没有收到。请问物流状态如何？\n\n谢谢",
        "sender": "cn_buyer@example.com",
        "expected_category": "order_tracking"
    },
    "chinese_shipping_time": {
        "subject": "运输时间咨询",
        "body": "您好，\n\n请问从深圳到汉堡的海运大概需要多长时间？\n\n谢谢",
        "sender": "cn_inquiry@example.com",
        "expected_category": "shipping_time"
    },
    "chinese_billing": {
        "subject": "发票申请",
        "body": "您好，\n\n我需要申请订单 #88888 的增值税专用发票，请发送到此邮箱。\n\n谢谢",
        "sender": "cn_accounting@example.com",
        "expected_category": "billing_invoice"
    }
}
