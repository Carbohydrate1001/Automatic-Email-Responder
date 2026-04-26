#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test with detailed reasoning output"""

from services.scoring_service import get_scoring_service
from services.reply_service import ReplyService
import json

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

print(f"\n详细评分和推理:")
print("="*60)
for dim, data in result['scores'].items():
    if isinstance(data, dict):
        score = data.get('score', 'N/A')
        reasoning = data.get('reasoning', '')
        print(f"\n【{dim}】: {score}/3")
        print(f"推理: {reasoning}")
    else:
        print(f"\n【{dim}】: {data}/3")

print("\n" + "="*60)
print("\n完整结果JSON:")
print(json.dumps(result, indent=2, ensure_ascii=False))
