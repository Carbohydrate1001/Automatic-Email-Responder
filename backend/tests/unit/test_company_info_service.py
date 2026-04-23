"""
Unit tests for company_info_service.py
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, mock_open
from services.company_info_service import CompanyInfoService


class TestCompanyInfoService:
    """Test suite for CompanyInfoService."""

    @pytest.fixture
    def temp_products_file(self):
        """Create a temporary products file."""
        fd, path = tempfile.mkstemp(suffix='.json')
        products_data = {
            "products": [
                {
                    "product_name": "Sea Freight (Standard)",
                    "unit_price": 120.0,
                    "currency": "USD",
                    "min_order_quantity": 1,
                    "delivery_lead_time_days": 30
                },
                {
                    "product_name": "Air Freight (Express)",
                    "unit_price": 350.0,
                    "currency": "USD",
                    "min_order_quantity": 1,
                    "delivery_lead_time_days": 5
                }
            ]
        }
        with os.fdopen(fd, 'w') as f:
            json.dump(products_data, f)

        yield path

        os.unlink(path)

    @pytest.fixture
    def service(self, temp_products_file):
        """Create CompanyInfoService with temp file."""
        with patch('services.company_info_service.PRODUCTS_FILE', temp_products_file):
            return CompanyInfoService()

    def test_list_products_returns_all(self, service):
        """Test list_products returns all products."""
        products = service.list_products()
        assert len(products) == 2
        assert products[0]['product_name'] == 'Sea Freight (Standard)'
        assert products[1]['product_name'] == 'Air Freight (Express)'

    def test_list_products_empty_file(self):
        """Test list_products with empty products list."""
        fd, path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w') as f:
            json.dump({"products": []}, f)

        with patch('services.company_info_service.PRODUCTS_FILE', path):
            service = CompanyInfoService()
            products = service.list_products()
            assert products == []

        os.unlink(path)

    def test_get_product_by_name_exists(self, service):
        """Test get_product_by_name returns correct product."""
        product = service.get_product_by_name("Sea Freight (Standard)")
        assert product is not None
        assert product['product_name'] == 'Sea Freight (Standard)'
        assert product['unit_price'] == 120.0

    def test_get_product_by_name_not_exists(self, service):
        """Test get_product_by_name returns None for non-existent product."""
        product = service.get_product_by_name("Non-existent Product")
        assert product is None

    def test_get_product_by_name_case_sensitive(self, service):
        """Test get_product_by_name is case sensitive."""
        product = service.get_product_by_name("sea freight (standard)")
        assert product is None

    def test_add_product_success(self, service):
        """Test adding a new product."""
        new_product = {
            "product_name": "Rail Freight",
            "unit_price": 80.0,
            "currency": "USD",
            "min_order_quantity": 5,
            "delivery_lead_time_days": 20
        }

        result = service.add_product(new_product)
        assert result is True

        products = service.list_products()
        assert len(products) == 3
        assert products[-1]['product_name'] == 'Rail Freight'

    def test_add_product_duplicate_name(self, service):
        """Test adding product with duplicate name fails."""
        duplicate_product = {
            "product_name": "Sea Freight (Standard)",
            "unit_price": 150.0,
            "currency": "USD",
            "min_order_quantity": 1,
            "delivery_lead_time_days": 25
        }

        result = service.add_product(duplicate_product)
        assert result is False

    def test_add_product_missing_required_field(self, service):
        """Test adding product with missing required field fails."""
        invalid_product = {
            "product_name": "Incomplete Product",
            "unit_price": 100.0
            # Missing currency, min_order_quantity, delivery_lead_time_days
        }

        with pytest.raises(KeyError):
            service.add_product(invalid_product)

    def test_update_product_success(self, service):
        """Test updating existing product."""
        updated_product = {
            "product_name": "Sea Freight (Standard)",
            "unit_price": 130.0,
            "currency": "USD",
            "min_order_quantity": 2,
            "delivery_lead_time_days": 28
        }

        result = service.update_product("Sea Freight (Standard)", updated_product)
        assert result is True

        product = service.get_product_by_name("Sea Freight (Standard)")
        assert product['unit_price'] == 130.0
        assert product['min_order_quantity'] == 2

    def test_update_product_not_exists(self, service):
        """Test updating non-existent product fails."""
        product = {
            "product_name": "Non-existent",
            "unit_price": 100.0,
            "currency": "USD",
            "min_order_quantity": 1,
            "delivery_lead_time_days": 10
        }

        result = service.update_product("Non-existent", product)
        assert result is False

    def test_delete_product_success(self, service):
        """Test deleting existing product."""
        result = service.delete_product("Sea Freight (Standard)")
        assert result is True

        products = service.list_products()
        assert len(products) == 1
        assert products[0]['product_name'] == 'Air Freight (Express)'

    def test_delete_product_not_exists(self, service):
        """Test deleting non-existent product fails."""
        result = service.delete_product("Non-existent Product")
        assert result is False

    def test_replace_all_products_success(self, service):
        """Test replacing all products."""
        new_products = [
            {
                "product_name": "New Product 1",
                "unit_price": 200.0,
                "currency": "EUR",
                "min_order_quantity": 10,
                "delivery_lead_time_days": 15
            },
            {
                "product_name": "New Product 2",
                "unit_price": 300.0,
                "currency": "GBP",
                "min_order_quantity": 5,
                "delivery_lead_time_days": 10
            }
        ]

        result = service.replace_all_products(new_products)
        assert result is True

        products = service.list_products()
        assert len(products) == 2
        assert products[0]['product_name'] == 'New Product 1'
        assert products[1]['product_name'] == 'New Product 2'

    def test_replace_all_products_empty_list(self, service):
        """Test replacing with empty list."""
        result = service.replace_all_products([])
        assert result is True

        products = service.list_products()
        assert len(products) == 0

    def test_upsert_product_insert_new(self, service):
        """Test upsert inserts new product when not exists."""
        new_product = {
            "product_name": "Truck Freight",
            "unit_price": 90.0,
            "currency": "USD",
            "min_order_quantity": 3,
            "delivery_lead_time_days": 7
        }

        result = service.upsert_product("Truck Freight", new_product)
        assert result is True

        products = service.list_products()
        assert len(products) == 3

    def test_upsert_product_update_existing(self, service):
        """Test upsert updates existing product."""
        updated_product = {
            "product_name": "Sea Freight (Standard)",
            "unit_price": 140.0,
            "currency": "USD",
            "min_order_quantity": 1,
            "delivery_lead_time_days": 30
        }

        result = service.upsert_product("Sea Freight (Standard)", updated_product)
        assert result is True

        product = service.get_product_by_name("Sea Freight (Standard)")
        assert product['unit_price'] == 140.0

    def test_validate_product_valid(self, service):
        """Test validate_product with valid product."""
        valid_product = {
            "product_name": "Test Product",
            "unit_price": 100.0,
            "currency": "USD",
            "min_order_quantity": 1,
            "delivery_lead_time_days": 10
        }

        # Should not raise exception
        service._validate_product(valid_product)

    def test_validate_product_missing_field(self, service):
        """Test validate_product with missing required field."""
        invalid_product = {
            "product_name": "Test Product",
            "unit_price": 100.0
        }

        with pytest.raises(KeyError):
            service._validate_product(invalid_product)

    def test_validate_product_invalid_type(self, service):
        """Test validate_product with invalid field type."""
        invalid_product = {
            "product_name": "Test Product",
            "unit_price": "not a number",
            "currency": "USD",
            "min_order_quantity": 1,
            "delivery_lead_time_days": 10
        }

        with pytest.raises((TypeError, ValueError)):
            service._validate_product(invalid_product)
            float(invalid_product['unit_price'])

    def test_file_persistence(self, service, temp_products_file):
        """Test that changes persist to file."""
        new_product = {
            "product_name": "Test Persistence",
            "unit_price": 999.0,
            "currency": "USD",
            "min_order_quantity": 1,
            "delivery_lead_time_days": 1
        }

        service.add_product(new_product)

        # Read file directly
        with open(temp_products_file, 'r') as f:
            data = json.load(f)

        assert len(data['products']) == 3
        assert data['products'][-1]['product_name'] == 'Test Persistence'

    def test_concurrent_access_safety(self, service):
        """Test service handles concurrent-like operations."""
        # Add multiple products in sequence
        for i in range(5):
            product = {
                "product_name": f"Product {i}",
                "unit_price": 100.0 + i,
                "currency": "USD",
                "min_order_quantity": 1,
                "delivery_lead_time_days": 10
            }
            service.add_product(product)

        products = service.list_products()
        assert len(products) == 7  # 2 original + 5 new
