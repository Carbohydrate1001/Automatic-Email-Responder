"""
Unified database seeding script.
Initializes all tables with seed data from data/ directory.

Usage:
    python seed_database.py              # Seed all tables
    python seed_database.py --orders     # Seed only orders
    python seed_database.py --routes     # Seed only logistics routes
    python seed_database.py --reset      # Clear and reseed all data
"""

import sys
import os
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.database import init_db
from scripts.init_orders import init_sample_orders
from scripts.init_logistics_routes import init_logistics_routes


def seed_all(reset=False):
    """Seed all tables with initial data."""
    print("=" * 60)
    print("Database Seeding")
    print("=" * 60)

    # Ensure database schema exists
    print("\n[1/3] Initializing database schema...")
    init_db()
    print("✓ Database schema ready")

    # Seed orders
    print("\n[2/3] Seeding orders...")
    init_sample_orders()

    # Seed logistics routes
    print("\n[3/3] Seeding logistics routes...")
    init_logistics_routes()

    print("\n" + "=" * 60)
    print("✓ Database seeding completed successfully")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Seed database with initial data"
    )
    parser.add_argument(
        '--orders',
        action='store_true',
        help='Seed only orders table'
    )
    parser.add_argument(
        '--routes',
        action='store_true',
        help='Seed only logistics routes table'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Clear existing data before seeding'
    )

    args = parser.parse_args()

    # If no specific table specified, seed all
    if not args.orders and not args.routes:
        seed_all(reset=args.reset)
    else:
        print("=" * 60)
        print("Database Seeding (Selective)")
        print("=" * 60)

        if args.orders:
            print("\nSeeding orders...")
            init_sample_orders()

        if args.routes:
            print("\nSeeding logistics routes...")
            init_logistics_routes()

        print("\n✓ Seeding completed")


if __name__ == "__main__":
    main()
