"""
用户服务 - 处理用户相关的业务逻辑
"""
import sqlite3
from datetime import datetime
from typing import List

from app.config import settings
from app.utils.auth import wechat_login, create_access_token
from app.database import row_to_dict


class UserService:
    """用户服务"""

    @staticmethod
    async def login(conn: sqlite3.Connection, code: str):
        """微信小程序登录（开发模式绕过微信 API）"""
        if settings.DEV_MODE:
            # 开发模式：用小程序传来的 code 或随机值作为 openid
            openid = f"dev_openid_{code}"
            unionid = f"dev_unionid_{code}"
        else:
            wx_data = await wechat_login(code)
            openid = wx_data["openid"]
            unionid = wx_data.get("unionid")

        # 查找或创建用户
        cursor = conn.execute("SELECT * FROM users WHERE openid = ?", (openid,))
        user = cursor.fetchone()

        if user is None:
            cursor = conn.execute(
                "INSERT INTO users (openid, unionid, is_elderly) VALUES (?, ?, 1)",
                (openid, unionid)
            )
            conn.commit()  # 立即提交以获取 id
            cursor = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,))
            user = cursor.fetchone()
        else:
            # 更新登录时间
            conn.execute(
                "UPDATE users SET last_login_at = ?, unionid = COALESCE(?, unionid) WHERE id = ?",
                (datetime.utcnow().isoformat(), unionid, user["id"])
            )

        user_dict = row_to_dict(user)
        access_token = create_access_token(data={"sub": str(user_dict["id"])})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_dict,
        }

    @staticmethod
    def get_profile(user: dict) -> dict:
        """获取用户个人信息"""
        return user

    @staticmethod
    def update_profile(conn: sqlite3.Connection, user: dict, data_dict: dict) -> dict:
        """更新用户个人信息"""
        update_data = {k: v for k, v in data_dict.items() if v is not None}
        if not update_data:
            return user

        fields = ", ".join(f"{k} = ?" for k in update_data.keys())
        values = list(update_data.values()) + [user["id"]]
        conn.execute(f"UPDATE users SET {fields} WHERE id = ?", values)

        cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],))
        return row_to_dict(cursor.fetchone())

    @staticmethod
    def bind_family(conn: sqlite3.Connection, family_user_id: int, elderly_user_id: int, relationship: str) -> dict:
        """家人绑定老人"""
        # 检查老人用户是否存在
        cursor = conn.execute("SELECT id FROM users WHERE id = ? AND is_active = 1", (elderly_user_id,))
        if not cursor.fetchone():
            raise ValueError("未找到该用户")

        # 检查是否已绑定
        cursor = conn.execute(
            "SELECT id FROM family_bindings WHERE elderly_user_id = ? AND family_user_id = ?",
            (elderly_user_id, family_user_id)
        )
        if cursor.fetchone():
            raise ValueError("已经绑定过该用户")

        cursor = conn.execute(
            "INSERT INTO family_bindings (elderly_user_id, family_user_id, relationship) VALUES (?, ?, ?)",
            (elderly_user_id, family_user_id, relationship)
        )
        return {"id": cursor.lastrowid, "elderly_user_id": elderly_user_id, "family_user_id": family_user_id}

    @staticmethod
    def get_family_members(conn: sqlite3.Connection, elderly_user_id: int) -> List[dict]:
        """获取老人的家人列表"""
        cursor = conn.execute("""
            SELECT f.id, u.nickname, u.avatar_url, f.relationship, f.is_primary, f.created_at
            FROM family_bindings f
            JOIN users u ON u.id = f.family_user_id
            WHERE f.elderly_user_id = ?
        """, (elderly_user_id,))
        return [row_to_dict(r) for r in cursor.fetchall()]

    @staticmethod
    def get_elderly_info(conn: sqlite3.Connection, elderly_user_id: int, family_user_id: int) -> dict:
        """获取老人用药概览（供子女查看）"""
        # 验证绑定关系
        cursor = conn.execute(
            "SELECT id FROM family_bindings WHERE elderly_user_id = ? AND family_user_id = ?",
            (elderly_user_id, family_user_id)
        )
        if not cursor.fetchone():
            raise ValueError("无权限查看该用户信息")

        cursor = conn.execute("SELECT * FROM users WHERE id = ?", (elderly_user_id,))
        user = cursor.fetchone()
        if not user:
            raise ValueError("用户不存在")

        today = datetime.utcnow().strftime("%Y-%m-%d")
        cursor = conn.execute(
            "SELECT status FROM medicine_records WHERE user_id = ? AND scheduled_time LIKE ?",
            (elderly_user_id, f"{today}%")
        )
        records = cursor.fetchall()
        total = len(records)
        taken = sum(1 for r in records if r["status"] == "taken")
        rate = (taken / total * 100) if total > 0 else 0.0

        result = row_to_dict(user)
        result["today_taken_count"] = taken
        result["today_total_count"] = total
        result["today_adherence_rate"] = round(rate, 1)
        return result

    @staticmethod
    def get_binded_elderly(conn: sqlite3.Connection, family_user_id: int) -> List[dict]:
        """获取家人绑定的所有老人"""
        cursor = conn.execute(
            "SELECT elderly_user_id FROM family_bindings WHERE family_user_id = ?",
            (family_user_id,)
        )
        bindings = cursor.fetchall()

        result = []
        today = datetime.utcnow().strftime("%Y-%m-%d")
        for b in bindings:
            eid = b["elderly_user_id"]
            cursor = conn.execute("SELECT * FROM users WHERE id = ?", (eid,))
            user = cursor.fetchone()
            if not user:
                continue

            cursor = conn.execute(
                "SELECT status FROM medicine_records WHERE user_id = ? AND scheduled_time LIKE ?",
                (eid, f"{today}%")
            )
            records = cursor.fetchall()
            total = len(records)
            taken = sum(1 for r in records if r["status"] == "taken")
            rate = (taken / total * 100) if total > 0 else 0.0

            u = row_to_dict(user)
            u["today_taken_count"] = taken
            u["today_total_count"] = total
            u["today_adherence_rate"] = round(rate, 1)
            result.append(u)

        return result
