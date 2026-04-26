# 数据库管理指南

## 数据库位置

数据库文件位于：`backend/email_system.db`

这是一个 SQLite 数据库文件，可以使用多种工具进行编辑。

---

## 方法 1: 使用 SQLite 命令行工具

### 打开数据库
```bash
sqlite3 backend/email_system.db
```

### 常用命令

#### 查看所有表
```sql
.tables
```

#### 查看表结构
```sql
.schema orders
```

#### 查询订单数据
```sql
SELECT * FROM orders;
```

#### 格式化输出
```sql
.mode column
.headers on
SELECT order_number, customer_email, product_name, order_status, shipping_status FROM orders;
```

#### 添加新订单
```sql
INSERT INTO orders (order_number, customer_email, product_name, quantity, total_amount, currency, order_status, shipping_status, tracking_number, destination)
VALUES ('ORD555666', 'newcustomer@example.com', 'Sea Freight (Express)', 3, 4500.00, 'CNY', 'confirmed', 'in_transit', 'TRK999888', '深圳');
```

#### 更新订单状态
```sql
UPDATE orders 
SET order_status = 'cancelled', updated_at = datetime('now')
WHERE order_number = 'ORD123456';
```

#### 删除订单
```sql
DELETE FROM orders WHERE order_number = 'ORD555666';
```

#### 退出 SQLite
```sql
.quit
```

---

## 方法 2: 使用 DB Browser for SQLite (推荐)

### 下载安装
- 官网：https://sqlitebrowser.org/
- 免费开源的图形化 SQLite 管理工具

### 使用步骤
1. 打开 DB Browser for SQLite
2. 点击 "Open Database"
3. 选择 `backend/email_system.db`
4. 在 "Browse Data" 标签页中可以查看和编辑数据
5. 在 "Execute SQL" 标签页中可以执行 SQL 语句
6. 修改后点击 "Write Changes" 保存

---

## 方法 3: 使用 Python 脚本

创建一个简单的 Python 脚本来管理订单：

```python
import sqlite3

# 连接数据库
conn = sqlite3.connect('backend/email_system.db')
cursor = conn.cursor()

# 添加订单
cursor.execute("""
    INSERT INTO orders (order_number, customer_email, product_name, quantity, total_amount, currency, order_status, shipping_status, tracking_number, destination)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", ('ORD777888', 'customer@example.com', 'Air Freight (Standard)', 2, 3200.00, 'CNY', 'confirmed', 'not_shipped', None, '上海'))

# 提交更改
conn.commit()

# 查询订单
cursor.execute("SELECT * FROM orders WHERE customer_email = ?", ('customer@example.com',))
for row in cursor.fetchall():
    print(row)

# 关闭连接
conn.close()
```

---

## 订单表字段说明

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `id` | INTEGER | 主键，自动递增 | 1 |
| `order_number` | TEXT | 订单号（唯一） | ORD123456 |
| `customer_email` | TEXT | 客户邮箱 | customer@example.com |
| `product_name` | TEXT | 产品名称 | Sea Freight (Standard) |
| `quantity` | INTEGER | 数量 | 2 |
| `total_amount` | REAL | 订单金额 | 2400.00 |
| `currency` | TEXT | 货币 | CNY 或 USD |
| `order_status` | TEXT | 订单状态 | pending/confirmed/cancelled/refunded |
| `shipping_status` | TEXT | 物流状态 | not_shipped/in_transit/delivered/exception |
| `tracking_number` | TEXT | 物流单号 | TRK789012 |
| `destination` | TEXT | 目的地 | 洛杉矶, 美国 |
| `created_at` | TEXT | 创建时间 | 2026-04-26 15:30:00 |
| `updated_at` | TEXT | 更新时间 | 2026-04-26 15:30:00 |

---

## 订单状态说明

### order_status（订单状态）
- `pending` - 待确认
- `confirmed` - 已确认
- `cancelled` - 已取消
- `refunded` - 已退款

### shipping_status（物流状态）
- `not_shipped` - 未发货
- `in_transit` - 运输中
- `delivered` - 已送达
- `exception` - 异常

---

## 批量导入订单

### 方法 1: 使用 CSV 文件

1. 创建 CSV 文件 `orders.csv`：
```csv
order_number,customer_email,product_name,quantity,total_amount,currency,order_status,shipping_status,tracking_number,destination
ORD100001,user1@example.com,Sea Freight (Standard),5,6000.00,CNY,confirmed,in_transit,TRK100001,北京
ORD100002,user2@example.com,Air Freight (Express),2,4800.00,CNY,confirmed,delivered,TRK100002,上海
```

2. 使用 SQLite 导入：
```bash
sqlite3 backend/email_system.db
.mode csv
.import orders.csv orders
```

### 方法 2: 使用 Python 脚本

```python
import sqlite3
import csv

conn = sqlite3.connect('backend/email_system.db')
cursor = conn.cursor()

with open('orders.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cursor.execute("""
            INSERT INTO orders (order_number, customer_email, product_name, quantity, total_amount, currency, order_status, shipping_status, tracking_number, destination)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (row['order_number'], row['customer_email'], row['product_name'], 
              int(row['quantity']), float(row['total_amount']), row['currency'],
              row['order_status'], row['shipping_status'], row['tracking_number'], row['destination']))

conn.commit()
conn.close()
print("Orders imported successfully!")
```

---

## 备份和恢复

### 备份数据库
```bash
# 复制整个数据库文件
cp backend/email_system.db backend/email_system_backup_$(date +%Y%m%d).db

# 或者导出为 SQL 文件
sqlite3 backend/email_system.db .dump > backup.sql
```

### 恢复数据库
```bash
# 从备份文件恢复
cp backend/email_system_backup_20260426.db backend/email_system.db

# 或者从 SQL 文件恢复
sqlite3 backend/email_system.db < backup.sql
```

---

## 常用查询示例

### 查询特定客户的所有订单
```sql
SELECT * FROM orders WHERE customer_email = 'customer@example.com';
```

### 查询运输中的订单
```sql
SELECT order_number, customer_email, destination, tracking_number 
FROM orders 
WHERE shipping_status = 'in_transit';
```

### 查询异常订单
```sql
SELECT order_number, customer_email, product_name, shipping_status 
FROM orders 
WHERE shipping_status = 'exception';
```

### 统计订单数量
```sql
SELECT order_status, COUNT(*) as count 
FROM orders 
GROUP BY order_status;
```

### 查询最近的订单
```sql
SELECT order_number, customer_email, created_at 
FROM orders 
ORDER BY created_at DESC 
LIMIT 10;
```

### 查询总金额
```sql
SELECT SUM(total_amount) as total_revenue, currency 
FROM orders 
WHERE order_status = 'confirmed' 
GROUP BY currency;
```

---

## 注意事项

1. **备份优先**：在进行大量修改前，务必备份数据库
2. **订单号唯一性**：`order_number` 字段有 UNIQUE 约束，不能重复
3. **邮箱格式**：`customer_email` 应该是有效的邮箱格式
4. **状态值**：使用标准的状态值（见上面的状态说明）
5. **时间戳**：`created_at` 和 `updated_at` 会自动设置，但也可以手动指定
6. **货币单位**：建议使用 CNY 或 USD
7. **金额格式**：使用浮点数，保留两位小数

---

## 重新初始化示例数据

如果需要重置订单数据，可以运行：

```bash
# 删除所有订单
sqlite3 backend/email_system.db "DELETE FROM orders;"

# 重新初始化示例订单
cd backend
python scripts/init_orders.py
```

---

## 故障排查

### 数据库被锁定
如果遇到 "database is locked" 错误：
1. 确保没有其他程序正在访问数据库
2. 关闭所有 SQLite 连接
3. 重启应用程序

### 数据库损坏
如果数据库损坏：
1. 从备份恢复
2. 或者使用 SQLite 的恢复工具：
```bash
sqlite3 backend/email_system.db "PRAGMA integrity_check;"
```

### 权限问题
确保数据库文件有正确的读写权限：
```bash
chmod 644 backend/email_system.db
```
