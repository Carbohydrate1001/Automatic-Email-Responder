"""
Authentication routes using Microsoft Azure AD OAuth2 (MSAL).
Blueprint prefix: /auth
"""

from flask import Blueprint, redirect, request, session, jsonify, url_for
import msal
import requests
from config import Config

auth_bp = Blueprint("auth", __name__)


def _build_msal_app():
    # 创建不走系统代理的 session，避免 ProxyError
    http_session = requests.Session()
    http_session.proxies = {"http": None, "https": None}
    return msal.ConfidentialClientApplication(
        Config.AZURE_CLIENT_ID,
        authority=Config.AZURE_AUTHORITY,
        client_credential=Config.AZURE_CLIENT_SECRET,
        http_client=http_session,
    )


def _build_auth_url(prompt: str = "consent"):
    app = _build_msal_app()
    return app.get_authorization_request_url(
        scopes=Config.GRAPH_SCOPES,
        redirect_uri=Config.AZURE_REDIRECT_URI,
        prompt=prompt,
    )


@auth_bp.route("/login")
def login():
    """Redirect the user to Microsoft login."""
    auth_url = _build_auth_url()
    return redirect(auth_url)


@auth_bp.route("/callback")
def callback():
    """Handle the OAuth2 callback from Microsoft."""
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return jsonify({"error": error, "description": request.args.get("error_description")}), 400

    if not code:
        return jsonify({"error": "No authorization code received"}), 400

    msal_app = _build_msal_app()
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=Config.GRAPH_SCOPES,
        redirect_uri=Config.AZURE_REDIRECT_URI,
    )

    if "error" in result:
        return jsonify({"error": result["error"], "description": result.get("error_description")}), 400

    print(f"[AUTH] token scope: {result.get('scope')}", flush=True)
    print(f"[AUTH] token_type: {result.get('token_type')}", flush=True)

    session["access_token"] = result["access_token"]
    session["user"] = result.get("id_token_claims", {})

    # Redirect to frontend
    return redirect("http://localhost:5173/emails")


@auth_bp.route("/logout")
def logout():
    """Clear the session and redirect to Microsoft logout."""
    session.clear()
    logout_url = (
        f"https://login.microsoftonline.com/{Config.AZURE_TENANT_ID}/oauth2/v2.0/logout"
        "?post_logout_redirect_uri=http://localhost:5173/login"
    )
    return redirect(logout_url)


@auth_bp.route("/me")
def me():
    """Return current logged-in user info from session."""
    if "user" not in session or "access_token" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = session["user"]
    return jsonify({
        "name": user.get("name", ""),
        "email": user.get("preferred_username", user.get("email", "")),
        "oid": user.get("oid", ""),
    })


@auth_bp.route("/status")
def status():
    """Check authentication status without redirecting."""
    if "access_token" in session:
        user = session.get("user", {})
        return jsonify({
            "authenticated": True,
            "user": {
                "name": user.get("name", ""),
                "email": user.get("preferred_username", user.get("email", "")),
            },
        })
    return jsonify({"authenticated": False})
