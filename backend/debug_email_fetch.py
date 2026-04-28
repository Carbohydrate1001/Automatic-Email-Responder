"""
邮件拉取诊断工具
用于调试 Render 部署后邮件拉取不工作的问题
"""

import sys
import json
from flask import Flask
from models.database import get_db_connection
from services.graph_service import GraphService

app = Flask(__name__)

def diagnose_email_fetch():
    """诊断邮件拉取问题"""

    print("=" * 60)
    print("邮件拉取诊断工具")
    print("=" * 60)

    # 1. 检查数据库中的用户会话
    print("\n[1] 检查数据库中的用户会话...")
    try:
        with get_db_connection() as conn:
            sessions = conn.execute("""
                SELECT user_email,
                       CASE
                           WHEN access_token IS NULL THEN 'NULL'
                           ELSE substr(access_token, 1, 20) || '...'
                       END as token_preview,
                       expires_at,
                       datetime('now') as current_time,
                       CASE
                           WHEN expires_at > datetime('now') THEN 'VALID'
                           ELSE 'EXPIRED'
                       END as token_status
                FROM user_sessions
                ORDER BY expires_at DESC
                LIMIT 5
            """).fetchall()

            if not sessions:
                print("   ❌ 没有找到任何用户会话")
                print("   → 请先在前端登录以创建会话")
                return False

            print(f"   ✓ 找到 {len(sessions)} 个用户会话:")
            for s in sessions:
                print(f"     - {s['user_email']}")
                print(f"       Token: {s['token_preview']}")
                print(f"       过期时间: {s['expires_at']}")
                print(f"       当前时间: {s['current_time']}")
                print(f"       状态: {s['token_status']}")

            # 获取第一个有效的 token
            valid_session = None
            for s in sessions:
                if s['token_status'] == 'VALID':
                    # 获取完整的 token
                    full_session = conn.execute(
                        "SELECT access_token FROM user_sessions WHERE user_email = ?",
                        (s['user_email'],)
                    ).fetchone()
                    valid_session = {
                        'user_email': s['user_email'],
                        'access_token': full_session['access_token']
                    }
                    break

            if not valid_session:
                print("\n   ❌ 没有找到有效的 token")
                print("   → 所有 token 都已过期，请重新登录")
                return False

    except Exception as e:
        print(f"   ❌ 数据库查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 2. 测试 Graph API 连接
    print(f"\n[2] 测试 Graph API 连接 (用户: {valid_session['user_email']})...")
    try:
        graph = GraphService(valid_session['access_token'])

        # 测试获取用户信息
        print("   测试 /me 端点...")
        me = graph.get_me()
        print(f"   ✓ 成功获取用户信息: {me.get('displayName')} ({me.get('mail')})")

    except Exception as e:
        print(f"   ❌ Graph API 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 3. 测试邮件拉取
    print("\n[3] 测试邮件拉取...")
    try:
        # 测试拉取所有邮件
        print("   尝试拉取最近 20 封邮件...")
        emails = graph.get_emails(top=20)
        print(f"   ✓ 成功拉取 {len(emails)} 封邮件")

        if emails:
            print("\n   前 5 封邮件:")
            for i, email in enumerate(emails[:5], 1):
                subject = email.get('subject', '(无主题)')
                sender = email.get('from', {}).get('emailAddress', {}).get('address', '未知')
                received = email.get('receivedDateTime', '未知')
                is_read = email.get('isRead', False)
                message_id = email.get('id', '')

                print(f"\n   邮件 {i}:")
                print(f"     主题: {subject}")
                print(f"     发件人: {sender}")
                print(f"     接收时间: {received}")
                print(f"     已读: {is_read}")
                print(f"     Message ID: {message_id[:30]}...")

                # 检查是否已在数据库中
                with get_db_connection() as conn:
                    existing = conn.execute(
                        "SELECT id, status FROM emails WHERE message_id = ?",
                        (message_id,)
                    ).fetchone()

                    if existing:
                        print(f"     数据库状态: 已存在 (ID: {existing['id']}, 状态: {existing['status']})")
                    else:
                        print(f"     数据库状态: 未处理 ✓")
        else:
            print("   ⚠️  没有拉取到任何邮件")
            print("   可能原因:")
            print("     1. 收件箱确实是空的")
            print("     2. Graph API 权限不足")
            print("     3. 邮件在其他文件夹中")

        # 测试拉取未读邮件
        print("\n   尝试拉取未读邮件...")
        # 手动添加过滤条件
        try:
            unread_data = graph._get(
                "/me/messages",
                params={
                    "$top": 20,
                    "$orderby": "receivedDateTime desc",
                    "$filter": "isRead eq false",
                    "$select": "id,subject,from,receivedDateTime,isRead",
                }
            )
            unread_emails = unread_data.get("value", [])
            print(f"   ✓ 找到 {len(unread_emails)} 封未读邮件")

            if unread_emails:
                print("\n   未读邮件列表:")
                for i, email in enumerate(unread_emails[:5], 1):
                    print(f"     {i}. {email.get('subject', '(无主题)')} - {email.get('from', {}).get('emailAddress', {}).get('address', '未知')}")
        except Exception as e:
            print(f"   ⚠️  拉取未读邮件失败: {e}")

    except Exception as e:
        print(f"   ❌ 邮件拉取失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 4. 检查数据库中已处理的邮件
    print("\n[4] 检查数据库中已处理的邮件...")
    try:
        with get_db_connection() as conn:
            total = conn.execute(
                "SELECT COUNT(*) as cnt FROM emails WHERE user_email = ?",
                (valid_session['user_email'],)
            ).fetchone()['cnt']

            recent = conn.execute(
                """SELECT subject, sender, status, created_at
                   FROM emails
                   WHERE user_email = ?
                   ORDER BY created_at DESC
                   LIMIT 5""",
                (valid_session['user_email'],)
            ).fetchall()

            print(f"   ✓ 数据库中共有 {total} 封邮件")

            if recent:
                print("\n   最近处理的 5 封邮件:")
                for r in recent:
                    print(f"     - {r['subject'][:50]} ({r['status']}) - {r['created_at']}")
            else:
                print("   ⚠️  数据库中没有任何邮件记录")

    except Exception as e:
        print(f"   ❌ 数据库查询失败: {e}")

    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

    return True


if __name__ == "__main__":
    with app.app_context():
        diagnose_email_fetch()
