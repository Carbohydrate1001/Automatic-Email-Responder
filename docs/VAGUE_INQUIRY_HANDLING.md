# Systematic Approach for Handling Vague/Ambiguous Inquiries

## Design Principle

**When specific information is unavailable or insufficient, acknowledge it and request clarification rather than generating fake or generic unhelpful responses.**

This principle applies across all business categories to ensure:
- Customer trust (no fake data)
- Accurate responses (no misleading information)
- Efficient resolution (request exactly what's needed)
- Proper routing (vague inquiries go to manual review if needed)

## Implementation Pattern

All reply templates follow a three-branch conditional logic:

```python
def _generate_template_reply(self, sender: str, body: str) -> str:
    # Extract necessary information from email
    key_info = extract_key_information(body)
    
    if key_info.is_sufficient():
        try:
            # Query database for real data
            real_data = query_database(key_info)
            return format_response_with_real_data(real_data)
        except NotFoundError:
            # Data not found - acknowledge and request verification
            return request_verification(key_info)
    else:
        # Insufficient information - request what's needed
        return request_necessary_information()
```

## Category-by-Category Implementation

### 1. pricing_inquiry

**Required Information:**
- Origin city
- Destination city
- Shipping method (sea/air freight)
- Quantity (container type or weight)

**Response Logic:**
- ✅ All info + route found → Return real pricing from logistics_routes table
- ⚠️ All info + route not found → Acknowledge route, request additional details
- ❌ Insufficient info → Request origin, destination, method, quantity

**Example Vague Inquiry:**
```
Input: "你们的运费怎么算？"
Output: "为了给您提供准确的报价，请提供以下信息：
- 起运地（城市）
- 目的地（城市）
- 运输方式（海运/空运）
- 货物重量/体积或柜型"
```

### 2. order_tracking

**Required Information:**
- Order number

**Response Logic:**
- ✅ Order number + found → Return real order status from orders table
- ⚠️ Order number + not found → Request correct order number or alternative info
- ❌ No order number → Request order number

**Example Vague Inquiry:**
```
Input: "我的货物到哪里了？"
Output: "为了查询您的订单物流状态，请您提供订单号（格式如：ORD123456）。"
```

### 3. order_cancellation

**Required Information:**
- Order number

**Response Logic:**
- ✅ Order number + found → Return order details and cancellation confirmation
- ⚠️ Order number + not found → Request correct order number
- ❌ No order number → Request order number

**Example Vague Inquiry:**
```
Input: "我想退款"
Output: "为了处理您的退款申请，请提供订单号（格式如：ORD123456）。"
```

### 4. shipping_time

**Required Information:**
- Order number (for specific inquiry) OR general route info

**Response Logic:**
- ✅ Order number + found → Return real order ETA
- ⚠️ Order number + not found → Request correct order number
- ❌ No order number → Provide general shipping time guidance (NOT fake specific data)

**Example Vague Inquiry:**
```
Input: "一般多久能到？"
Output: "关于运输时效的咨询，以下是我们公司的一般运输时间参考：
- 国内快递：1-3个工作日
- 国际快递（亚洲）：3-5个工作日
- 国际快递（欧美）：5-7个工作日
- 海运（亚洲）：7-14天
- 海运（欧美）：20-35天

如果您有具体的订单需要查询，请提供订单号。"
```

### 5. shipping_exception

**Required Information:**
- Order number
- Exception description

**Response Logic:**
- ✅ Order number + found → Return order details and resolution plan
- ⚠️ Order number + not found → Request correct order number and exception details
- ❌ No order number → Request order number, tracking number, and exception description

**Example Vague Inquiry:**
```
Input: "我的货出问题了"
Output: "为了快速处理，请您提供：
- 订单号（格式如：ORD123456）
- 物流单号（如有）
- 具体异常情况"
```

### 6. billing_invoice

**Required Information:**
- Order number

**Response Logic:**
- ✅ Order number + found → Return real billing/invoice info from order
- ⚠️ Order number + not found → Request correct order number or alternative info
- ❌ No order number → Request order number

**Example Vague Inquiry:**
```
Input: "我要发票"
Output: "为了查询您的账单和发票信息，请提供以下信息：
- 订单号（格式如：ORD123456）
- 或提供下单时使用的邮箱和订单日期"
```

## Anti-Patterns to Avoid

### ❌ Generating Fake Data
```python
# WRONG - generates random fake data
def _generate_route() -> str:
    cities = ["深圳", "新加坡", "鹿特丹"]
    return " -> ".join(sample(cities, 3))
```

**Why it's wrong:**
- Misleads customers with false information
- Erodes trust when customers realize data is fake
- Can cause serious business consequences

### ❌ Generic Unhelpful Responses
```python
# WRONG - returns generic product when asked about specific route
if "海运" in text:
    return "Sea Freight (Standard) - USD 120"
```

**Why it's wrong:**
- Doesn't answer the actual question (route-specific pricing)
- Ignores critical details (origin, destination, quantity)
- Provides useless information that doesn't help customer

### ❌ Claiming Specific Data for General Inquiries
```python
# WRONG - claims "your shipment" when user asked general question
return "您的货物的运输信息：迪拜 -> 上海"
```

**Why it's wrong:**
- User didn't provide order number, so there's no "your shipment"
- Creates confusion and distrust
- May contradict user's actual question

## Best Practices

### ✅ Request Exactly What's Needed
Be specific about what information is required:
```
"为了给您提供准确的报价，请提供以下信息：
- 起运地（城市）
- 目的地（城市）
- 运输方式（海运/空运）
- 货物重量/体积或柜型（如20尺柜、40尺柜）
- 货物类型"
```

### ✅ Provide General Guidance When Appropriate
For general inquiries without specific details, provide general reference information:
```
"以下是我们公司的一般运输时间参考：
- 国内快递：1-3个工作日
- 国际快递（亚洲）：3-5个工作日
- 海运（欧美）：20-35天

具体时效会根据起运地、目的地、货物类型等因素有所不同。"
```

### ✅ Acknowledge When Data Not Available
Be honest when requested information isn't in the database:
```
"关于您咨询的运输路线，我们需要进一步核实具体报价。
您咨询的路线：北京 -> 悉尼

为了给您提供准确的报价，请提供以下信息：
- 货物类型和名称
- 货物重量/体积"
```

## Impact on Rubric Scoring

Properly handling vague inquiries improves rubric scores:

**Before (fake data):**
- `information_completeness`: 0-1/3 (答非所问)
- `risk_level`: 1/3 (fake data is risky)
- `template_applicability`: 1/3 (doesn't match intent)
- **Result:** pending_review ❌

**After (request clarification):**
- `information_completeness`: 3/3 (professional request for info)
- `risk_level`: 3/3 (requesting info is low risk)
- `template_applicability`: 3/3 (appropriate response)
- **Result:** auto_sent ✅

## Testing Vague Inquiries

Each category should have test cases for vague inquiries:

```python
# Test case: Vague pricing inquiry
{
    "subject": "价格咨询",
    "body": "你们的运费怎么算？",
    "expected_behavior": "Request origin, destination, method, quantity",
    "should_not_contain": ["USD 120", "Sea Freight (Standard)"],
    "should_contain": ["起运地", "目的地", "运输方式"]
}

# Test case: Vague tracking inquiry
{
    "subject": "订单查询",
    "body": "我的货在哪里？",
    "expected_behavior": "Request order number",
    "should_not_contain": ["您的货物", "运输路线"],
    "should_contain": ["订单号", "ORD"]
}
```

## Summary

The systematic approach for handling vague inquiries:

1. **Extract** necessary information from email body
2. **Validate** if information is sufficient
3. **Query** database for real data if sufficient
4. **Acknowledge** if data not found and request verification
5. **Request** specific information if insufficient

This ensures all responses are:
- **Honest** - No fake data
- **Helpful** - Request exactly what's needed
- **Professional** - Clear and specific guidance
- **Safe** - Low risk, appropriate for auto-send
