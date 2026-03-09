"""
Application configuration module.
Loads settings from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    PORT = int(os.getenv("FLASK_PORT", 5005))

    # Microsoft Azure AD / Entra ID
    AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
    AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "common")
    AZURE_REDIRECT_URI = os.getenv(
        "AZURE_REDIRECT_URI", "http://localhost:5005/auth/callback"
    )
    AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
    GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

    # Microsoft Graph API scopes
    GRAPH_SCOPES = [
        "User.Read",
        "Mail.Read",
        "Mail.ReadWrite",
        "Mail.Send",
    ]

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.n1n.ai/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Database
    DATABASE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "email_system.db"
    )

    # Classification confidence threshold – emails below this go to manual review
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))

    # Email send retry policy
    SEND_RETRY_MAX_ATTEMPTS = int(os.getenv("SEND_RETRY_MAX_ATTEMPTS", "3"))
    SEND_RETRY_DELAY_SECONDS = float(os.getenv("SEND_RETRY_DELAY_SECONDS", "1.0"))

