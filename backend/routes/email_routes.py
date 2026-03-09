"""
Email API routes.
Blueprint prefix: /api
"""

from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, session
from models.database import get_db_connection
from services.graph_service import GraphService
from services.classification_service import ClassificationService
from services.reply_service import ReplyService

email_bp = Blueprint("email", __name__)

classification_svc = ClassificationService()
reply_svc = ReplyService()


def _require_auth():
    """Return (access_token, user_email) or raise if not authenticated."""
    token = session.get("access_token")
    if not token:
        return None, None
    user = session.get("user", {})
    email = user.get("preferred_username", user.get("email", "system"))
    return token, email


# ---------------------------------------------------------------------------
# POST /api/fetch  – Pull new emails from Outlook and process them
# ---------------------------------------------------------------------------
@email_bp.route("/fetch", methods=["POST"])
def fetch_emails():
    token, operator = _require_auth()
    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    graph = GraphService(token)
    top = int(request.json.get("top", 10)) if request.is_json else 10

    print(f"[FETCH] 开始拉取邮件，top={top}", flush=True)
    try:
        emails = graph.get_emails(top=top)
    except Exception as e:
        print(f"[FETCH] Graph API 调用失败: {e}", flush=True)
        return jsonify({"error": f"Graph API 调用失败: {str(e)}"}), 500

    print(f"[FETCH] Graph 返回 {len(emails)} 封邮件", flush=True)
    if emails:
        print(f"[FETCH] 第一封邮件主题: {emails[0].get('subject')}, 发件人: {emails[0].get('from', {}).get('emailAddress', {}).get('address')}", flush=True)

    processed = []
    skipped = []

    for msg in emails:
        message_id = msg["id"]

        # Skip already-processed emails
        with get_db_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM emails WHERE message_id = ?", (message_id,)
            ).fetchone()

        if existing:
            skipped.append(message_id)
            continue

        subject = msg.get("subject", "(No Subject)")
        sender = msg.get("from", {}).get("emailAddress", {}).get("address", "unknown")
        received_at = msg.get("receivedDateTime", "")
        body = msg.get("body", {}).get("content", msg.get("bodyPreview", ""))

        classification = classification_svc.classify_email(subject, body)
        result = reply_svc.process_email(
            message_id=message_id,
            subject=subject,
            sender=sender,
            received_at=received_at,
            body=body,
            classification=classification,
            graph_service=graph,
            operator=operator,
        )
        processed.append(result)

    return jsonify({
        "processed": len(processed),
        "skipped": len(skipped),
        "emails": processed,
    })


# ---------------------------------------------------------------------------
# GET /api/emails  – List emails with optional filters and pagination
# ---------------------------------------------------------------------------
@email_bp.route("/emails", methods=["GET"])
def list_emails():
    token, _ = _require_auth()
    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    status_filter = request.args.get("status")
    category_filter = request.args.get("category")
    search = request.args.get("search", "").strip()

    offset = (page - 1) * per_page

    where_clauses = []
    params = []

    if status_filter:
        where_clauses.append("e.status = ?")
        params.append(status_filter)
    if category_filter:
        where_clauses.append("e.category = ?")
        params.append(category_filter)
    if search:
        where_clauses.append("(e.subject LIKE ? OR e.sender LIKE ?)")
        params += [f"%{search}%", f"%{search}%"]

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    with get_db_connection() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) as cnt FROM emails e {where_sql}", params
        ).fetchone()["cnt"]

        rows = conn.execute(
            f"""
            SELECT e.id, e.message_id, e.subject, e.sender, e.received_at,
                   e.category, e.confidence, e.status, e.created_at,
                   r.reply_text
            FROM emails e
            LEFT JOIN replies r ON r.email_id = e.id
            {where_sql}
            ORDER BY e.created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset],
        ).fetchall()

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "emails": [dict(r) for r in rows],
    })


# ---------------------------------------------------------------------------
# GET /api/emails/<id>  – Single email detail
# ---------------------------------------------------------------------------
@email_bp.route("/emails/<int:email_id>", methods=["GET"])
def get_email(email_id):
    token, _ = _require_auth()
    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    with get_db_connection() as conn:
        row = conn.execute(
            """
            SELECT e.*, r.reply_text, r.sent_at
            FROM emails e
            LEFT JOIN replies r ON r.email_id = e.id
            WHERE e.id = ?
            """,
            (email_id,),
        ).fetchone()

    if not row:
        return jsonify({"error": "Email not found"}), 404

    return jsonify(dict(row))


# ---------------------------------------------------------------------------
# POST /api/emails/<id>/approve  – Approve and send a pending email reply
# ---------------------------------------------------------------------------
@email_bp.route("/emails/<int:email_id>/approve", methods=["POST"])
def approve_email(email_id):
    token, operator = _require_auth()
    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT e.*, r.reply_text FROM emails e LEFT JOIN replies r ON r.email_id = e.id WHERE e.id = ?",
            (email_id,),
        ).fetchone()

        if not row:
            return jsonify({"error": "Email not found"}), 404

        if row["status"] not in ("pending_review",):
            return jsonify({"error": f"Cannot approve email with status '{row['status']}'"}), 400

    # Allow overriding reply text
    reply_text = row["reply_text"]
    if request.is_json and request.json.get("reply_text"):
        reply_text = request.json["reply_text"]

    graph = GraphService(token)
    graph.send_reply(row["message_id"], reply_text)
    graph.mark_as_read(row["message_id"])
    sent_at = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE emails SET status = 'approved' WHERE id = ?", (email_id,)
        )
        conn.execute(
            "UPDATE replies SET reply_text = ?, sent_at = ? WHERE email_id = ?",
            (reply_text, sent_at, email_id),
        )
        conn.execute(
            "INSERT INTO audit_log (email_id, action, operator) VALUES (?, 'approved', ?)",
            (email_id, operator),
        )
        conn.commit()

    return jsonify({"success": True, "status": "approved", "sent_at": sent_at})


# ---------------------------------------------------------------------------
# POST /api/emails/<id>/reject  – Reject a pending email
# ---------------------------------------------------------------------------
@email_bp.route("/emails/<int:email_id>/reject", methods=["POST"])
def reject_email(email_id):
    token, operator = _require_auth()
    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id, status FROM emails WHERE id = ?", (email_id,)
        ).fetchone()

        if not row:
            return jsonify({"error": "Email not found"}), 404

        if row["status"] not in ("pending_review",):
            return jsonify({"error": f"Cannot reject email with status '{row['status']}'"}), 400

        conn.execute(
            "UPDATE emails SET status = 'rejected' WHERE id = ?", (email_id,)
        )
        conn.execute(
            "INSERT INTO audit_log (email_id, action, operator) VALUES (?, 'rejected', ?)",
            (email_id, operator),
        )
        conn.commit()

    return jsonify({"success": True, "status": "rejected"})


# ---------------------------------------------------------------------------
# GET /api/stats  – Aggregate statistics for the dashboard
# ---------------------------------------------------------------------------
@email_bp.route("/stats", methods=["GET"])
def get_stats():
    token, _ = _require_auth()
    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    with get_db_connection() as conn:
        total = conn.execute("SELECT COUNT(*) as cnt FROM emails").fetchone()["cnt"]

        status_rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM emails GROUP BY status"
        ).fetchall()

        category_rows = conn.execute(
            "SELECT category, COUNT(*) as cnt FROM emails GROUP BY category"
        ).fetchall()

        avg_confidence = conn.execute(
            "SELECT AVG(confidence) as avg FROM emails"
        ).fetchone()["avg"] or 0.0

        # Last 7 days daily counts
        daily_rows = conn.execute(
            """
            SELECT date(created_at) as day,
                   SUM(CASE WHEN status IN ('auto_sent','approved') THEN 1 ELSE 0 END) as handled,
                   SUM(CASE WHEN status = 'pending_review' THEN 1 ELSE 0 END) as pending
            FROM emails
            WHERE created_at >= date('now', '-6 days')
            GROUP BY day
            ORDER BY day
            """
        ).fetchall()

    status_map = {r["status"]: r["cnt"] for r in status_rows}
    auto_sent = status_map.get("auto_sent", 0)
    approved = status_map.get("approved", 0)
    pending_review = status_map.get("pending_review", 0)
    rejected = status_map.get("rejected", 0)

    auto_rate = round((auto_sent + approved) / total * 100, 1) if total > 0 else 0.0

    return jsonify({
        "total": total,
        "auto_sent": auto_sent,
        "approved": approved,
        "pending_review": pending_review,
        "rejected": rejected,
        "auto_rate": auto_rate,
        "avg_confidence": round(avg_confidence * 100, 1),
        "categories": [dict(r) for r in category_rows],
        "daily": [dict(r) for r in daily_rows],
    })
