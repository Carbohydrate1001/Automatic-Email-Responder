"""
Initialize logistics_routes table with sample data.
Loads route data from data/logistics_routes_seed.json.
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.database import get_db_connection


def init_logistics_routes():
    """Insert sample logistics routes into the database."""
    data_path = Path(__file__).parent.parent / "data" / "logistics_routes_seed.json"

    # Load routes from JSON file
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        routes_data = data['routes']

    # Convert to tuple format for database insertion
    routes = [
        (
            r['origin'], r['destination'], r['shipping_method'],
            r['container_type'], r['weight_range'], r['price'],
            r['currency'], r['transit_days']
        )
        for r in routes_data
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
