"""
Automated Customer Service Email Reply System
Main Flask application entry point.
"""

from flask import Flask, session
from flask_cors import CORS
from config import Config
from models.database import init_db
from routes.auth_routes import auth_bp
from routes.email_routes import email_bp


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY

    # Cookie 跨端口兼容（开发环境）
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    # Enable CORS for Vue.js frontend (dev on port 5173)
    CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

    # Initialize database
    init_db()

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(email_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return {"message": "Automated Email Reply System API", "status": "running"}

    return app


if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print("  Automated Customer Service Email Reply System")
    print(f"  Server running at: http://127.0.0.1:{Config.PORT}")
    print("=" * 60)
    app.run(debug=Config.DEBUG, port=Config.PORT)
