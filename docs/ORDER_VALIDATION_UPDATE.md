# 订单验证功能更新说明

## 更新概述

本次更新解决了系统对任意订单号都会回复"已处理"的问题。现在系统会真正验证订单是否存在于数据库中，并根据验证结果生成相应的回复。

---

## 主要变更

### 1. 新增订单数据表

在数据库中新增 `orders` 表，用于存储订单信息：
- 订单号、客户邮箱、产品名称、数量、金额
- 订单状态（待确认/已确认/已取消/已退款）
- 物流状态（未发货/运输中/已送达/异常）
- 物流单号、目的地等信息

**文件**: `backend/models/database.py`

### 2. 创建订单验证服务

新增 `OrderService` 类，提供订单管理功能：
- `find_order_by_number()` - 根据订单号查询订单
- `validate_order_ownership()` - 验证订单存在且属于该客户
- `update_order_status()` - 更新订单状态
- `format_order_info()` - 格式化订单信息用于邮件回复

**文件**: `backend/services/order_service.py`

### 3. 更新邮件回复模板

修改了三个订单相关的回复模板，添加订单验证逻辑：

#### 订单取消模板
- **有效订单**: 显示订单详细信息 + 确认退款
- **无效订单**: 提示"订单未找到，请核实订单号"
- **无订单号**: 要求用户提供订单号

#### 订单追踪模板
- **有效订单**: 显示订单详细信息 + 物流状态 + 追踪号
- **无效订单**: 提示"订单未找到"并要求提供更多信息
- **无订单号**: 要求用户提供订单号

#### 运输异常模板
- **有效订单**: 显示订单信息 + 更新状态为"异常" + 提供解决方案
- **无效订单**: 提示"订单未找到"并要求提供订单号和物流单号
- **无订单号**: 要求用户提供订单号和异常描述

**文件**: `backend/services/reply_service.py`

### 4. 初始化脚本和测试工具

- `backend/scripts/init_orders.py` - 初始化示例订单数据
- `backend/scripts/test_order_validation.py` - 测试订单验证功能

---

## 使用方法

### 初始化订单数据

首次使用前，需要初始化示例订单数据：

```bash
cd backend
python scripts/init_orders.py
```

这会创建 5 个示例订单：
- ORD123456: customer@example.com (运输中)
- ORD654321: cn_customer@example.com (未发货)
- ORD789012: buyer@example.com (已送达)
- ORD111222: urgent@example.com (异常)
- ORD333444: test@example.com (待确认)

### 测试功能

运行测试脚本验证功能：

```bash
cd backend
python scripts/test_order_validation.py
```

### 查看订单数据

使用 SQLite 命令行工具：

```bash
sqlite3 backend/email_system.db "SELECT * FROM orders;"
```

---

## 测试场景

### 场景 1: 有效订单取消

**邮件内容**:
- 发件人: customer@example.com
- 主题: Cancel my order
- 正文: I want to cancel order ORD123456

**系统回复**:
```
尊敬的 customer，

感谢您的来信。我们已经收到您的取消订单请求，订单信息如下：

- 订单号：ORD123456
- 产品：Sea Freight (Standard)
- 数量：2
- 金额：CNY 2400.00
- 订单状态：已确认
- 物流状态：运输中
- 物流单号：TRK789012
- 目的地：洛杉矶, 美国

我们将尽快处理您的退款申请。退款预计将在七个工作日内完成...
```

### 场景 2: 无效订单取消

**邮件内容**:
- 发件人: customer@example.com
- 主题: Cancel my order
- 正文: I want to cancel order ORD999999

**系统回复**:
```
尊敬的 customer，

感谢您的来信。关于您提到的订单 ORD999999，我们在系统中未能找到相关记录，
或该订单不属于您的账户。

请您核实订单号是否正确，或联系我们的客服团队获取进一步帮助。

客服热线：+86 123 456 7890
客服邮箱：support@mis2001.com
```

### 场景 3: 无订单号

**邮件内容**:
- 发件人: customer@example.com
- 主题: Cancel my order
- 正文: I want to cancel my recent order

**系统回复**:
```
尊敬的 customer，

感谢您的来信。为了更好地处理您的取消订单请求，请您提供以下信息：

- 订单号（格式如：ORD123456）
- 订单日期

收到您的订单信息后，我们将立即为您处理。
```

---

## 数据库管理

详细的数据库管理指南请参考：[DATABASE_MANAGEMENT.md](./DATABASE_MANAGEMENT.md)

### 快速操作

#### 添加新订单
```sql
INSERT INTO orders (order_number, customer_email, product_name, quantity, total_amount, currency, order_status, shipping_status, tracking_number, destination)
VALUES ('ORD888999', 'newuser@example.com', 'Sea Freight (Standard)', 3, 3600.00, 'CNY', 'confirmed', 'in_transit', 'TRK888999', '上海');
```

#### 更新订单状态
```sql
UPDATE orders 
SET order_status = 'cancelled', updated_at = datetime('now')
WHERE order_number = 'ORD123456';
```

#### 查询订单
```sql
SELECT order_number, customer_email, product_name, order_status, shipping_status 
FROM orders 
WHERE customer_email = 'customer@example.com';
```

---

## 技术细节

### 订单号提取

系统使用正则表达式从邮件正文中提取订单号，支持以下格式：
- `ORD123456` - 直接的订单号
- `订单号：ORD123456` - 中文标签
- `order number: ORD123456` - 英文标签

### 订单归属验证

系统会验证订单是否属于发件人：
- 比较订单的 `customer_email` 与邮件的 `sender`
- 不匹配时返回"订单未找到"（出于安全考虑，不透露订单是否存在）

### 状态更新

- 订单取消 → `order_status = 'cancelled'`
- 运输异常 → `shipping_status = 'exception'`
- 订单追踪 → 不更新状态，仅查询

---

## 文件清单

### 新增文件
- `backend/services/order_service.py` - 订单验证服务
- `backend/scripts/init_orders.py` - 初始化订单数据
- `backend/scripts/test_order_validation.py` - 测试脚本
- `docs/DATABASE_MANAGEMENT.md` - 数据库管理指南
- `docs/ORDER_VALIDATION_UPDATE.md` - 本文档

### 修改文件
- `backend/models/database.py` - 添加 orders 表
- `backend/services/reply_service.py` - 更新订单相关模板

---

## 后续扩展建议

1. **订单管理界面**: 在前端添加订单管理页面，方便查看和编辑订单
2. **批量导入**: 支持从 CSV 或 Excel 文件批量导入订单
3. **订单历史**: 记录订单状态变更历史
4. **客户管理**: 创建客户表，关联订单和客户信息
5. **产品目录**: 创建产品表，标准化产品信息
6. **自动同步**: 与外部订单系统（如 ERP）自动同步订单数据

---

## 常见问题

### Q: 如何添加更多测试订单？
A: 运行 `python backend/scripts/init_orders.py` 或使用 SQL 直接插入。

### Q: 订单号格式有要求吗？
A: 建议使用 `ORD` 前缀 + 6位数字，但系统支持任意格式。

### Q: 如何重置所有订单数据？
A: 执行 `sqlite3 backend/email_system.db "DELETE FROM orders;"` 然后重新运行初始化脚本。

### Q: 订单验证失败会影响自动发送吗？
A: 不会。订单验证失败时，系统会生成"订单未找到"的回复，仍然可以自动发送（如果满足其他条件）。

### Q: 如何查看订单验证日志？
A: 查看应用日志，OrderService 会记录所有验证操作。

---

## 联系支持

如有问题或建议，请联系开发团队或在项目仓库提交 Issue。
