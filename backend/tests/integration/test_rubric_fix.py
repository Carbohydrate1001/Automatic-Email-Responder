#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test the updated rubric scoring for order cancellation with missing order number"""

from services.scoring_service import get_scoring_service
from services.reply_service import ReplyService

# Scenario: Refund request with non-existent order number
subject = '申请退款'
body = '我要退款，订单号是 ORD999999'
category = 'order_cancellation'

# Generate reply (order not found case)
reply_service = ReplyService()
reply_text = reply_service._generate_order_cancellation_template_reply('test@example.com', body)

print('生成的回复:')
print(reply_text)
print('\n' + '='*60 + '\n')

# Score the reply
scoring_service = get_scoring_service()
result = scoring_service.score_auto_send_readiness(
    subject=subject,
    body=body,
    reply_text=reply_text,
    category=category,
    use_llm=True,
    apply_calibration=False
)

print('评分结果:')
print(f"Weighted Score: {result['weighted_score']}/3.0")
print(f"Confidence: {result['confidence']}")
print(f"Auto-send Recommended: {result['auto_send_recommended']}")
print(f"\nThresholds: {result['thresholds_applied']}")
print(f"\n各维度评分:")
for dim, data in result['scores'].items():
    if isinstance(data, dict):
        print(f"  {dim}: {data.get('score', 'N/A')}/3 - {data.get('reasoning', '')}")
    else:
        print(f"  {dim}: {data}/3")
