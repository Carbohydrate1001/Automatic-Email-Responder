"""
Initialize sample orders for testing order validation feature.
"""
import sqlite3
from pathlib import Path


def init_sample_orders():
    """Initialize sample order data in the database."""
    db_path = Path(__file__).parent.parent / "email_system.db"
    conn = sqlite3.connect(db_path)

    # Sample order data covering different statuses
    sample_orders = [
        {
            "order_number": "ORD123456",
            "customer_email": "customer@example.com",
            "product_name": "Sea Freight (Standard)",
            "quantity": 2,
            "total_amount": 2400.00,
            "currency": "CNY",
            "order_status": "confirmed",
            "shipping_status": "in_transit",
            "tracking_number": "TRK789012",
            "destination": "洛杉矶, 美国"
        },
        {
            "order_number": "ORD654321",
            "customer_email": "cn_customer@example.com",
            "product_name": "Air Freight (Express)",
            "quantity": 1,
            "total_amount": 2800.00,
            "currency": "CNY",
            "order_status": "confirmed",
            "shipping_status": "not_shipped",
            "tracking_number": None,
            "destination": "北京"
        },
        {
            "order_number": "ORD789012",
            "customer_email": "buyer@example.com",
            "product_name": "Sea Freight (Standard)",
            "quantity": 5,
            "total_amount": 6000.00,
            "currency": "CNY",
            "order_status": "confirmed",
            "shipping_status": "delivered",
            "tracking_number": "TRK456789",
            "destination": "纽约, 美国"
        },
        {
            "order_number": "ORD111222",
            "customer_email": "urgent@example.com",
            "product_name": "Air Freight (Express)",
            "quantity": 3,
            "total_amount": 8400.00,
            "currency": "CNY",
            "order_status": "confirmed",
            "shipping_status": "exception",
            "tracking_number": "ABC123",
            "destination": "伦敦, 英国"
        },
        {
            "order_number": "ORD333444",
            "customer_email": "test@example.com",
            "product_name": "Sea Freight (Economy)",
            "quantity": 10,
            "total_amount": 9500.00,
            "currency": "CNY",
            "order_status": "pending",
            "shipping_status": "not_shipped",
            "tracking_number": None,
            "destination": "上海"
        }
    ]

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
