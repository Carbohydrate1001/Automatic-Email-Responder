"""
Pytest configuration and shared fixtures.
"""

import pytest
import sqlite3
import tempfile
import os
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone


@pytest.fixture
def temp_db():
    """Create a temporary test database."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    # Create test schema
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS emails (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id  TEXT UNIQUE NOT NULL,
            subject     TEXT,
            sender      TEXT,
            received_at TEXT,
            body        TEXT,
            category    TEXT,
            confidence  REAL,
            reasoning   TEXT,
            status      TEXT DEFAULT 'pending_review',
            retry_count INTEGER DEFAULT 0,
            last_error  TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS replies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id    INTEGER REFERENCES emails(id),
            reply_text  TEXT,
            sent_at     TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id    INTEGER REFERENCES emails(id),
            action      TEXT,
            operator    TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()

    yield conn

    conn.close()
    os.unlink(path)


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_choice = Mock()
    mock_message = Mock()

    mock_message.content = '{"category": "pricing_inquiry", "confidence": 0.85, "reasoning": "Test reasoning"}'
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    return mock_client


@pytest.fixture
def mock_graph_service():
    """Mock Graph API service for testing."""
    mock_service = Mock()

    # Mock get_emails
    mock_service.get_emails.return_value = [
        {
            'id': 'msg-001',
            'subject': 'Price inquiry for sea freight',
            'from': {'emailAddress': {'address': 'customer@example.com', 'name': 'John Doe'}},
            'receivedDateTime': '2026-04-23T10:00:00Z',
            'body': {'content': 'I would like to know the price for sea freight service.'}
        }
    ]

    # Mock send_reply
    mock_service.send_reply.return_value = None

    # Mock mark_as_read
    mock_service.mark_as_read.return_value = None

    return mock_service


@pytest.fixture
def sample_email_data():
    """Sample email data for testing."""
    return {
        'message_id': 'test-msg-001',
        'subject': 'Price inquiry for sea freight',
        'sender': 'customer@example.com',
        'received_at': '2026-04-23T10:00:00Z',
        'body': 'I would like to know the price for sea freight service. Please send me a quotation.',
        'category': 'pricing_inquiry',
        'confidence': 0.85,
        'reasoning': 'Email contains pricing inquiry keywords',
        'status': 'pending_review'
    }


@pytest.fixture
def sample_classification_result():
    """Sample classification result for testing."""
    return {
        'category': 'pricing_inquiry',
        'confidence': 0.85,
        'reasoning': 'Email contains pricing inquiry keywords',
        'category_label': '询价/报价',
        'is_business_related': True,
        'business_confidence': 0.90
    }


@pytest.fixture
def sample_products():
    """Sample product catalog for testing."""
    return [
        {
            'product_name': 'Sea Freight (Standard)',
            'unit_price': 120.0,
            'currency': 'USD',
            'min_order_quantity': 1,
            'delivery_lead_time_days': 30
        },
        {
            'product_name': 'Air Freight (Express)',
            'unit_price': 350.0,
            'currency': 'USD',
            'min_order_quantity': 1,
            'delivery_lead_time_days': 5
        }
    ]


@pytest.fixture
def mock_config(monkeypatch):
    """Mock configuration for testing."""
    monkeypatch.setenv('OPENAI_API_KEY', 'test-api-key')
    monkeypatch.setenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    monkeypatch.setenv('OPENAI_MODEL', 'gpt-4o-mini')
    monkeypatch.setenv('CONFIDENCE_THRESHOLD', '0.75')
    monkeypatch.setenv('SEND_RETRY_MAX_ATTEMPTS', '3')
    monkeypatch.setenv('SEND_RETRY_DELAY_SECONDS', '1.0')


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing."""
    fixed_time = datetime(2026, 4, 23, 10, 0, 0, tzinfo=timezone.utc)
    return fixed_time
