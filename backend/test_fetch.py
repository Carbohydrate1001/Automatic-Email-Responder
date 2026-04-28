"""
本地测试邮件拉取功能
运行此脚本前请确保：
1. 已经在前端登录过，数据库中有有效的 token
2. Outlook 收件箱中有邮件
"""

import sys
import os

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models.database import get_db_connection
from services.graph_service import GraphService

app = Flask(__name__)

def test_email_fetch():
    print("=" * 60)
    print("测试邮件拉取功能")
    print("=" * 60)

    # 1. 从数据库获取有效的 token
    print("\n[1] 从数据库获取用户 token...")
    with get_db_connection() as conn:
        session = conn.execute("""
            SELECT user_email, access_token, expires_at
            FROM user_sessions
            WHERE access_token IS NOT NULL
            AND expires_at > datetime('now')
            ORDER BY expires_at DESC
            LIMIT 1
        """).fetchone()

    if not session:
        print("❌ 没有找到有效的用户会话")
        print("请先在前端登录: http://localhost:5173")
        return

    print(f"✓ 找到用户: {session['user_email']}")
    print(f"  Token 过期时间: {session['expires_at']}")

    # 2. 测试 Graph API
    print("\n[2] 测试 Graph API 连接...")
    try:
        graph = GraphService(session['access_token'])
        me = graph.get_me()
        print(f"✓ 成功连接到 Graph API")
        print(f"  用户: {me.get('displayName')} ({me.get('mail')})")
    except Exception as e:
        print(f"❌ Graph API 连接失败: {e}")
        return

    # 3. 拉取邮件
    print("\n[3] 拉取邮件...")
    try:
        emails = graph.get_emails(top=20)
        print(f"\n✓ 成功拉取 {len(emails)} 封邮件")

        if not emails:
            print("\n⚠️  没有拉取到邮件")
            print("可能原因:")
            print("  1. 收件箱确实是空的")
            print("  2. 所有邮件都已经被处理过")
            print("  3. Graph API 权限不足")
            return

        # 显示邮件列表
        print("\n邮件列表:")
        print("-" * 60)
        for i, email in enumerate(emails, 1):
            subject = email.get('subject', '(无主题)')
            sender = email.get('from', {}).get('emailAddress', {}).get('address', '未知')
            received = email.get('receivedDateTime', '未知')
            is_read = email.get('isRead', False)
            message_id = email.get('id', '')

            print(f"\n{i}. {subject}")
            print(f"   发件人: {sender}")
            print(f"   时间: {received}")
            print(f"   已读: {'是' if is_read else '否'}")

            # 检查是否已在数据库中
            with get_db_connection() as conn:
                existing = conn.execute(
                    "SELECT id, status FROM emails WHERE message_id = ?",
                    (message_id,)
                ).fetchone()

                if existing:
                    print(f"   状态: 已处理 (数据库 ID: {existing['id']}, 状态: {existing['status']})")
                else:
                    print(f"   状态: 未处理 ✓ (这封邮件会被处理)")

    except Exception as e:
        print(f"❌ 拉取邮件失败: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    with app.app_context():
        test_email_fetch()
