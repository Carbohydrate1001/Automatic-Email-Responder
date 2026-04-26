"""
Initialize logistics_routes table with sample data.
Run this script once to populate the database with common routes.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.database import get_db_connection


def init_logistics_routes():
    """Insert sample logistics routes into the database."""

    routes = [
        # Sea freight routes - 20ft container
        ('深圳', '纽约', 'sea_freight', '20ft', None, 2800.0, 'USD', 28),
        ('深圳', '洛杉矶', 'sea_freight', '20ft', None, 2200.0, 'USD', 18),
        ('上海', '纽约', 'sea_freight', '20ft', None, 2900.0, 'USD', 30),
        ('上海', '洛杉矶', 'sea_freight', '20ft', None, 2300.0, 'USD', 20),
        ('上海', '伦敦', 'sea_freight', '20ft', None, 3200.0, 'USD', 35),
        ('深圳', '伦敦', 'sea_freight', '20ft', None, 3100.0, 'USD', 33),
        ('香港', '纽约', 'sea_freight', '20ft', None, 2850.0, 'USD', 29),

        # Sea freight routes - 40ft container
        ('深圳', '纽约', 'sea_freight', '40ft', None, 4200.0, 'USD', 28),
        ('深圳', '洛杉矶', 'sea_freight', '40ft', None, 3500.0, 'USD', 18),
        ('上海', '纽约', 'sea_freight', '40ft', None, 4300.0, 'USD', 30),
        ('上海', '洛杉矶', 'sea_freight', '40ft', None, 3600.0, 'USD', 20),
        ('上海', '伦敦', 'sea_freight', '40ft', None, 4800.0, 'USD', 35),

        # Air freight routes - weight ranges
        ('深圳', '纽约', 'air_freight', None, '0-100', 8.5, 'USD', 5),
        ('深圳', '纽约', 'air_freight', None, '100-500', 7.2, 'USD', 5),
        ('深圳', '纽约', 'air_freight', None, '500-1000', 6.5, 'USD', 5),

        ('上海', '纽约', 'air_freight', None, '0-100', 8.8, 'USD', 5),
        ('上海', '纽约', 'air_freight', None, '100-500', 7.5, 'USD', 5),
        ('上海', '纽约', 'air_freight', None, '500-1000', 6.8, 'USD', 5),

        ('上海', '伦敦', 'air_freight', None, '0-100', 9.2, 'USD', 6),
        ('上海', '伦敦', 'air_freight', None, '100-500', 7.8, 'USD', 6),
        ('上海', '伦敦', 'air_freight', None, '500-1000', 7.0, 'USD', 6),

        ('深圳', '伦敦', 'air_freight', None, '0-100', 9.0, 'USD', 6),
        ('深圳', '伦敦', 'air_freight', None, '100-500', 7.6, 'USD', 6),

        ('上海', '洛杉矶', 'air_freight', None, '0-100', 7.5, 'USD', 4),
        ('上海', '洛杉矶', 'air_freight', None, '100-500', 6.5, 'USD', 4),
        ('上海', '洛杉矶', 'air_freight', None, '500-1000', 5.8, 'USD', 4),

        ('深圳', '洛杉矶', 'air_freight', None, '0-100', 7.3, 'USD', 4),
        ('深圳', '洛杉矶', 'air_freight', None, '100-500', 6.3, 'USD', 4),
    ]

    with get_db_connection() as conn:
        # Clear existing routes (for clean re-initialization)
        conn.execute("DELETE FROM logistics_routes")

        # Insert new routes
        conn.executemany("""
            INSERT INTO logistics_routes
            (origin, destination, shipping_method, container_type, weight_range, price, currency, transit_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, routes)

        conn.commit()

        # Verify insertion
        count = conn.execute("SELECT COUNT(*) FROM logistics_routes").fetchone()[0]
        print(f"✓ Initialized {count} logistics routes")

        # Show sample routes
        print("\nSample routes:")
        cursor = conn.execute("""
            SELECT origin, destination, shipping_method, container_type, weight_range, price, currency
            FROM logistics_routes
            LIMIT 5
        """)
        for row in cursor.fetchall():
            origin, dest, method, container, weight, price, currency = row
            spec = container or weight or 'N/A'
            print(f"  {origin} -> {dest} ({method}, {spec}): {currency} {price}")


if __name__ == "__main__":
    init_logistics_routes()
