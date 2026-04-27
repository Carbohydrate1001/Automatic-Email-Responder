# Data Directory

This directory contains seed data, configuration files, and datasets for the email response system.

## Structure

```
data/
├── README.md                      # This file
├── orders_seed.json              # Sample order data for testing
├── logistics_routes_seed.json    # Logistics pricing and routes
├── company_products.json         # Company product catalog
└── calibration_dataset.json      # ML model calibration data
```

## Seed Data Files

### orders_seed.json
Sample order data used for testing order validation, tracking, and cancellation features.

**Schema:**
- `order_number`: Unique order identifier (e.g., "ORD123456")
- `customer_email`: Customer email address
- `product_name`: Product/service name
- `quantity`: Order quantity
- `total_amount`: Total order amount
- `currency`: Currency code (CNY, USD, EUR, etc.)
- `order_status`: Order status (pending, confirmed, cancelled, completed)
- `shipping_status`: Shipping status (not_shipped, in_transit, delivered, exception)
- `tracking_number`: Tracking number (nullable)
- `destination`: Shipping destination

### logistics_routes_seed.json
Logistics routes with pricing information for sea and air freight.

**Schema:**
- `origin`: Origin city/port
- `destination`: Destination city/port
- `shipping_method`: sea_freight or air_freight
- `container_type`: Container size for sea freight (20ft, 40ft) or null
- `weight_range`: Weight range for air freight (e.g., "0-100") or null
- `price`: Price per unit
- `currency`: Currency code
- `transit_days`: Estimated transit time in days

### company_products.json
Company product catalog and service offerings.

### calibration_dataset.json
Human-labeled dataset for confidence score calibration. Used to:
- Calculate calibration error (reliability)
- Train calibration models (Platt scaling, isotonic regression)
- Validate threshold settings

**Structure:**
```json
{
  "metadata": {...},
  "samples": [
    {
      "id": "unique_id",
      "subject": "email subject",
      "body": "email body",
      "predicted_category": "category from classifier",
      "true_category": "human-labeled ground truth",
      "confidence": 0.85,
      "correct": true/false
    }
  ]
}
```

**Target Size:** 200+ samples across all categories

## Usage

### Loading Seed Data

Use the unified seeding script:

```bash
# Seed all tables
python scripts/seed_database.py

# Seed specific tables
python scripts/seed_database.py --orders
python scripts/seed_database.py --routes

# Reset and reseed
python scripts/seed_database.py --reset
```

### Individual Scripts

```bash
python scripts/init_orders.py
python scripts/init_logistics_routes.py
```

### Calibration Tools

- `scripts/calibration_analysis.py` - Analyzes calibration quality
- `scripts/threshold_optimization.py` - Optimizes decision thresholds
- `services/scoring_service.py` - Loads calibration model for inference

## Modifying Seed Data

1. Edit the JSON files directly
2. Maintain the schema structure
3. Ensure data consistency (e.g., valid email formats, positive amounts)
4. Run the seeding script to apply changes

## Data Versioning

Each seed data file includes a `version` field. Increment this when making schema changes:
- Major version (1.0 → 2.0): Breaking schema changes
- Minor version (1.0 → 1.1): Backward-compatible additions
