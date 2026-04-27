"""
Generate realistic sample data for testing.
Creates diverse orders with various statuses, products, and destinations.
"""
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path


# Realistic data pools
PRODUCTS = [
    ("Sea Freight (Standard)", 1200, 3000),
    ("Sea Freight (Economy)", 800, 2000),
    ("Sea Freight (Express)", 1800, 4000),
    ("Air Freight (Standard)", 2500, 5000),
    ("Air Freight (Express)", 3500, 7000),
    ("Rail Freight", 1000, 2500),
    ("Truck Freight", 600, 1500),
]

DESTINATIONS = [
    "洛杉矶, 美国", "纽约, 美国", "芝加哥, 美国", "休斯顿, 美国",
    "伦敦, 英国", "曼彻斯特, 英国", "利物浦, 英国",
    "汉堡, 德国", "慕尼黑, 德国", "柏林, 德国",
    "鹿特丹, 荷兰", "阿姆斯特丹, 荷兰",
    "东京, 日本", "大阪, 日本", "横滨, 日本",
    "首尔, 韩国", "釜山, 韩国",
    "新加坡", "悉尼, 澳大利亚", "墨尔本, 澳大利亚",
    "迪拜, 阿联酋", "多伦多, 加拿大", "温哥华, 加拿大",
    "上海", "北京", "深圳", "广州", "天津"
]

ORDER_STATUSES = [
    ("pending", 0.10),
    ("confirmed", 0.70),
    ("cancelled", 0.10),
    ("completed", 0.10),
]

SHIPPING_STATUSES = [
    ("not_shipped", 0.15),
    ("in_transit", 0.50),
    ("delivered", 0.25),
    ("exception", 0.10),
]

CURRENCIES = ["CNY", "USD", "EUR", "GBP"]

# Customer name pools for generating emails
FIRST_NAMES = [
    "zhang", "wang", "li", "zhao", "chen", "liu", "yang", "huang", "wu", "xu",
    "john", "mary", "david", "sarah", "michael", "lisa", "james", "jennifer",
    "robert", "emily", "william", "jessica", "richard", "amanda", "thomas"
]

LAST_NAMES = [
    "wei", "ming", "hua", "jing", "feng", "lei", "yun", "xin", "bo", "tao",
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller",
    "davis", "rodriguez", "martinez", "hernandez", "lopez", "gonzalez"
]

DOMAINS = [
    "gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "163.com",
    "qq.com", "126.com", "sina.com", "company.com", "business.com"
]


def weighted_choice(choices):
    """Select item based on weights."""
    items, weights = zip(*choices)
    return random.choices(items, weights=weights)[0]


def generate_email():
    """Generate a realistic email address."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    domain = random.choice(DOMAINS)

    # Various email formats
    formats = [
        f"{first}.{last}@{domain}",
        f"{first}{last}@{domain}",
        f"{first}_{last}@{domain}",
        f"{first}{random.randint(1, 999)}@{domain}",
    ]
    return random.choice(formats)


def generate_tracking_number(shipping_status):
    """Generate tracking number based on status."""
    if shipping_status in ["not_shipped", "exception"]:
        return None if random.random() < 0.7 else f"TRK{random.randint(100000, 999999)}"

    prefixes = ["TRK", "ABC", "XYZ", "SF", "DHL", "FDX", "UPS"]
    return f"{random.choice(prefixes)}{random.randint(100000, 999999)}"


def generate_order(index):
    """Generate a single realistic order."""
    product_name, min_price, max_price = random.choice(PRODUCTS)
    quantity = random.randint(1, 20)
    unit_price = random.uniform(min_price, max_price)
    total_amount = round(quantity * unit_price, 2)

    order_status = weighted_choice(ORDER_STATUSES)
    shipping_status = weighted_choice(SHIPPING_STATUSES)

    # Adjust shipping status based on order status
    if order_status == "pending":
        shipping_status = "not_shipped"
    elif order_status == "cancelled":
        shipping_status = random.choice(["not_shipped", "exception"])
    elif order_status == "completed":
        shipping_status = "delivered"

    # Generate order number with timestamp-like format
    date_part = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%y%m")
    order_number = f"ORD{date_part}{random.randint(1000, 9999)}"

    return {
        "order_number": order_number,
        "customer_email": generate_email(),
        "product_name": product_name,
        "quantity": quantity,
        "total_amount": total_amount,
        "currency": random.choice(CURRENCIES),
        "order_status": order_status,
        "shipping_status": shipping_status,
        "tracking_number": generate_tracking_number(shipping_status),
        "destination": random.choice(DESTINATIONS),
    }


def generate_sample_data(num_orders=100):
    """Generate and insert sample orders into database."""
    db_path = Path(__file__).parent.parent / "email_system.db"
    conn = sqlite3.connect(db_path)

    print(f"Generating {num_orders} sample orders...")

    # Keep track of used order numbers to avoid duplicates
    used_numbers = set()
    cursor = conn.execute("SELECT order_number FROM orders")
    used_numbers.update(row[0] for row in cursor.fetchall())

    orders = []
    attempts = 0
    max_attempts = num_orders * 3

    while len(orders) < num_orders and attempts < max_attempts:
        attempts += 1
        order = generate_order(len(orders))

        if order["order_number"] not in used_numbers:
            orders.append(order)
            used_numbers.add(order["order_number"])

    # Insert orders
    inserted = 0
    for order in orders:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO orders
                (order_number, customer_email, product_name, quantity, total_amount,
                 currency, order_status, shipping_status, tracking_number, destination)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order["order_number"], order["customer_email"], order["product_name"],
                order["quantity"], order["total_amount"], order["currency"],
                order["order_status"], order["shipping_status"],
                order["tracking_number"], order["destination"]
            ))
            inserted += 1
        except Exception as e:
            print(f"Error inserting order {order['order_number']}: {e}")

    conn.commit()

    # Statistics
    cursor = conn.execute("SELECT COUNT(*) FROM orders")
    total_count = cursor.fetchone()[0]

    cursor = conn.execute("""
        SELECT order_status, COUNT(*)
        FROM orders
        GROUP BY order_status
    """)
    status_counts = dict(cursor.fetchall())

    cursor = conn.execute("""
        SELECT shipping_status, COUNT(*)
        FROM orders
        GROUP BY shipping_status
    """)
    shipping_counts = dict(cursor.fetchall())

    conn.close()

    print(f"\n✓ Successfully inserted {inserted} orders")
    print(f"✓ Total orders in database: {total_count}")
    print(f"\nOrder Status Distribution:")
    for status, count in status_counts.items():
        print(f"  - {status}: {count}")
    print(f"\nShipping Status Distribution:")
    for status, count in shipping_counts.items():
        print(f"  - {status}: {count}")


if __name__ == "__main__":
    import sys

    num_orders = 100
    if len(sys.argv) > 1:
        try:
            num_orders = int(sys.argv[1])
        except ValueError:
            print(f"Invalid number: {sys.argv[1]}, using default 100")

    generate_sample_data(num_orders)
