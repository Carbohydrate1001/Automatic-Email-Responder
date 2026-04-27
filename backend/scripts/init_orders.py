"""
Initialize sample orders for testing order validation feature.
Loads order data from data/orders_seed.json.
"""
import sqlite3
import json
from pathlib import Path


def init_sample_orders():
    """Initialize sample order data in the database."""
    db_path = Path(__file__).parent.parent / "email_system.db"
    data_path = Path(__file__).parent.parent / "data" / "orders_seed.json"

    # Load orders from JSON file
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        sample_orders = data['orders']

    conn = sqlite3.connect(db_path)

    for order in sample_orders:
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
        except Exception as e:
            print(f"Error inserting order {order['order_number']}: {e}")

    conn.commit()

    # Verify insertion
    cursor = conn.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]

    conn.close()
    print(f"[OK] Initialized {len(sample_orders)} sample orders")
    print(f"[OK] Total orders in database: {count}")
    print("\nSample orders:")
    for order in sample_orders:
        print(f"  - {order['order_number']}: {order['customer_email']} ({order['shipping_status']})")


if __name__ == "__main__":
    init_sample_orders()
