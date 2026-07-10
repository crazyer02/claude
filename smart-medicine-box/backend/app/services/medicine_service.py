"""
药品服务 - 处理药品CRUD和库存管理
"""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional
from app.database import row_to_dict


class MedicineService:
    """药品服务"""

    # ============== 药品管理 ==============

    @staticmethod
    def create_medicine(conn: sqlite3.Connection, user_id: int, data_dict: dict) -> dict:
        """添加药品"""
        cursor = conn.execute("""
            INSERT INTO medicines (user_id, name, specification, dosage, unit, frequency,
                start_date, end_date, total_stock, remaining_stock, stock_alert_threshold,
                box_position, image_url, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, data_dict["name"], data_dict.get("specification"),
            data_dict["dosage"], data_dict.get("unit", "片"),
            data_dict.get("frequency", "daily"), data_dict.get("start_date"),
            data_dict.get("end_date"), data_dict.get("total_stock", 0),
            data_dict.get("total_stock", 0),  # remaining = total initially
            data_dict.get("stock_alert_threshold", 5),
            data_dict.get("box_position"), data_dict.get("image_url"),
            data_dict.get("notes"),
        ))
        cursor = conn.execute("SELECT * FROM medicines WHERE id = ?", (cursor.lastrowid,))
        return row_to_dict(cursor.fetchone())

    @staticmethod
    def get_medicines(conn: sqlite3.Connection, user_id: int, is_active: Optional[bool] = None) -> List[dict]:
        """获取用户的所有药品"""
        if is_active is not None:
            cursor = conn.execute(
                "SELECT * FROM medicines WHERE user_id = ? AND is_active = ? ORDER BY created_at DESC",
                (user_id, 1 if is_active else 0)
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM medicines WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
        return [row_to_dict(r) for r in cursor.fetchall()]

    @staticmethod
    def get_medicine(conn: sqlite3.Connection, medicine_id: int, user_id: int) -> dict:
        """获取单个药品"""
        cursor = conn.execute(
            "SELECT * FROM medicines WHERE id = ? AND user_id = ?",
            (medicine_id, user_id)
        )
        medicine = cursor.fetchone()
        if not medicine:
            raise ValueError("药品不存在")
        return row_to_dict(medicine)

    @staticmethod
    def update_medicine(conn: sqlite3.Connection, medicine_id: int, user_id: int, data_dict: dict) -> dict:
        """更新药品信息"""
        MedicineService.get_medicine(conn, medicine_id, user_id)  # 验证存在

        update_data = {k: v for k, v in data_dict.items() if v is not None}
        if not update_data:
            return MedicineService.get_medicine(conn, medicine_id, user_id)

        # 库存联动调整
        if "total_stock" in update_data:
            old = MedicineService.get_medicine(conn, medicine_id, user_id)
            ratio = update_data["total_stock"] / old["total_stock"] if old["total_stock"] > 0 else 0
            if ratio > 0:
                new_remaining = int(old["remaining_stock"] * ratio)
                conn.execute("UPDATE medicines SET remaining_stock = ? WHERE id = ?", (new_remaining, medicine_id))

        fields = ", ".join(f"{k} = ?" for k in update_data.keys())
        values = list(update_data.values()) + [medicine_id]
        conn.execute(f"UPDATE medicines SET {fields} WHERE id = ?", values)

        return MedicineService.get_medicine(conn, medicine_id, user_id)

    @staticmethod
    def delete_medicine(conn: sqlite3.Connection, medicine_id: int, user_id: int) -> None:
        """删除药品（软删除）"""
        MedicineService.get_medicine(conn, medicine_id, user_id)
        conn.execute("UPDATE medicines SET is_active = 0 WHERE id = ?", (medicine_id,))

    @staticmethod
    def update_stock(conn: sqlite3.Connection, medicine_id: int, user_id: int, used: int = 1) -> None:
        """扣减库存"""
        conn.execute(
            "UPDATE medicines SET remaining_stock = MAX(0, remaining_stock - ?) WHERE id = ? AND user_id = ?",
            (used, medicine_id, user_id)
        )

    @staticmethod
    def get_low_stock_medicines(conn: sqlite3.Connection, user_id: int) -> List[dict]:
        """获取库存不足的药品"""
        cursor = conn.execute("""
            SELECT * FROM medicines
            WHERE user_id = ? AND is_active = 1 AND remaining_stock <= stock_alert_threshold
        """, (user_id,))
        return [row_to_dict(r) for r in cursor.fetchall()]

    # ============== 用药计划 ==============

    @staticmethod
    def create_schedule(conn: sqlite3.Connection, user_id: int, data_dict: dict) -> dict:
        """创建用药计划"""
        MedicineService.get_medicine(conn, data_dict["medicine_id"], user_id)

        cursor = conn.execute("""
            INSERT INTO medicine_schedules (medicine_id, user_id, period, time_label,
                reminder_time, dosage_at_time, days_of_week)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data_dict["medicine_id"], user_id, data_dict["period"],
            data_dict.get("time_label", ""), data_dict["reminder_time"],
            data_dict["dosage_at_time"], data_dict.get("days_of_week"),
        ))
        cursor = conn.execute("SELECT * FROM medicine_schedules WHERE id = ?", (cursor.lastrowid,))
        return row_to_dict(cursor.fetchone())

    @staticmethod
    def get_schedules(conn: sqlite3.Connection, user_id: int, medicine_id: Optional[int] = None) -> List[dict]:
        """获取用药计划列表"""
        if medicine_id:
            cursor = conn.execute("""
                SELECT s.*, m.name as medicine_name, m.specification as medicine_specification
                FROM medicine_schedules s
                JOIN medicines m ON m.id = s.medicine_id
                WHERE s.user_id = ? AND s.is_active = 1 AND s.medicine_id = ?
                ORDER BY s.reminder_time
            """, (user_id, medicine_id))
        else:
            cursor = conn.execute("""
                SELECT s.*, m.name as medicine_name, m.specification as medicine_specification
                FROM medicine_schedules s
                JOIN medicines m ON m.id = s.medicine_id
                WHERE s.user_id = ? AND s.is_active = 1
                ORDER BY s.reminder_time
            """, (user_id,))
        return [row_to_dict(r) for r in cursor.fetchall()]

    @staticmethod
    def update_schedule(conn: sqlite3.Connection, schedule_id: int, user_id: int, data_dict: dict) -> dict:
        """更新用药计划"""
        cursor = conn.execute(
            "SELECT * FROM medicine_schedules WHERE id = ? AND user_id = ?",
            (schedule_id, user_id)
        )
        if not cursor.fetchone():
            raise ValueError("用药计划不存在")

        update_data = {k: v for k, v in data_dict.items() if v is not None}
        if update_data:
            fields = ", ".join(f"{k} = ?" for k in update_data.keys())
            values = list(update_data.values()) + [schedule_id]
            conn.execute(f"UPDATE medicine_schedules SET {fields} WHERE id = ?", values)

        cursor = conn.execute("SELECT * FROM medicine_schedules WHERE id = ?", (schedule_id,))
        return row_to_dict(cursor.fetchone())

    @staticmethod
    def delete_schedule(conn: sqlite3.Connection, schedule_id: int, user_id: int) -> None:
        """删除用药计划"""
        cursor = conn.execute(
            "SELECT id FROM medicine_schedules WHERE id = ? AND user_id = ?",
            (schedule_id, user_id)
        )
        if not cursor.fetchone():
            raise ValueError("用药计划不存在")
        conn.execute("UPDATE medicine_schedules SET is_active = 0 WHERE id = ?", (schedule_id,))

    # ============== 用药记录 ==============

    @staticmethod
    def create_record(conn: sqlite3.Connection, user_id: int, data_dict: dict) -> dict:
        """记录用药"""
        MedicineService.get_medicine(conn, data_dict["medicine_id"], user_id)

        status = data_dict.get("status", "taken")
        actual_time = data_dict.get("actual_time") or (datetime.utcnow().isoformat() if status == "taken" else None)

        cursor = conn.execute("""
            INSERT INTO medicine_records (schedule_id, medicine_id, user_id, scheduled_time, actual_time, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data_dict.get("schedule_id"), data_dict["medicine_id"], user_id,
            data_dict["scheduled_time"], actual_time, status, data_dict.get("notes"),
        ))

        # 如果已服用，自动减库存
        if status == "taken":
            MedicineService.update_stock(conn, data_dict["medicine_id"], user_id)

        cursor = conn.execute("""
            SELECT r.*, m.name as medicine_name, m.dosage as medicine_dosage
            FROM medicine_records r
            JOIN medicines m ON m.id = r.medicine_id
            WHERE r.id = ?
        """, (cursor.lastrowid,))
        return row_to_dict(cursor.fetchone())

    @staticmethod
    def get_records(
        conn: sqlite3.Connection,
        user_id: int,
        date_str: Optional[str] = None,
        medicine_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """获取用药记录"""
        query = """
            SELECT r.*, m.name as medicine_name, m.dosage as medicine_dosage
            FROM medicine_records r
            JOIN medicines m ON m.id = r.medicine_id
            WHERE r.user_id = ?
        """
        params = [user_id]

        if date_str:
            query += " AND r.scheduled_time LIKE ?"
            params.append(f"{date_str}%")
        if medicine_id is not None:
            query += " AND r.medicine_id = ?"
            params.append(medicine_id)
        if status:
            query += " AND r.status = ?"
            params.append(status)

        query += " ORDER BY r.scheduled_time DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        return [row_to_dict(r) for r in cursor.fetchall()]

    # ============== 今日概览 ==============

    @staticmethod
    def get_today_overview(conn: sqlite3.Connection, user_id: int) -> dict:
        """获取今日用药概览 - 首页核心数据"""
        today = datetime.utcnow()
        today_str = today.strftime("%Y-%m-%d")
        weekday = today.isoweekday()

        # 获取所有活跃的用药计划及关联药品
        cursor = conn.execute("""
            SELECT s.*, m.name as medicine_name, m.dosage as medicine_dosage,
                   m.is_active as med_active, m.start_date, m.end_date, m.box_position
            FROM medicine_schedules s
            JOIN medicines m ON m.id = s.medicine_id
            WHERE s.user_id = ? AND s.is_active = 1 AND m.is_active = 1
        """, (user_id,))
        schedules = cursor.fetchall()

        items = []
        for s in schedules:
            # 检查星期
            if s["days_of_week"]:
                allowed = [int(d.strip()) for d in s["days_of_week"].split(",")]
                if weekday not in allowed:
                    continue
            # 检查日期范围
            if s["start_date"] and s["start_date"] > today_str:
                continue
            if s["end_date"] and s["end_date"] < today_str:
                continue

            scheduled_datetime = f"{today_str}T{s['reminder_time']}:00"

            # 查找今天的记录
            cursor = conn.execute(
                "SELECT status FROM medicine_records WHERE schedule_id = ? AND user_id = ? AND scheduled_time = ?",
                (s["id"], user_id, scheduled_datetime)
            )
            record = cursor.fetchone()

            status = "pending"
            if record:
                status = record["status"]

            items.append({
                "schedule_id": s["id"],
                "medicine_id": s["medicine_id"],
                "medicine_name": s["medicine_name"],
                "dosage_at_time": s["dosage_at_time"],
                "period": s["period"],
                "time_label": s["time_label"],
                "reminder_time": s["reminder_time"],
                "status": status,
                "box_position": s["box_position"],
            })

        # 过去超过1小时的pending视为missed
        now = datetime.utcnow()
        for item in items:
            if item["status"] == "pending":
                h, m = item["reminder_time"].split(":")
                item_dt = datetime(now.year, now.month, now.day, int(h), int(m))
                if now > item_dt + timedelta(hours=1):
                    item["status"] = "missed"

        items.sort(key=lambda x: x["reminder_time"])

        total = len(items)
        taken = sum(1 for i in items if i["status"] == "taken")
        missed = sum(1 for i in items if i["status"] == "missed")
        pending = sum(1 for i in items if i["status"] == "pending")
        rate = (taken / total * 100) if total > 0 else 0.0

        return {
            "date": today_str,
            "total_count": total,
            "taken_count": taken,
            "missed_count": missed,
            "pending_count": pending,
            "adherence_rate": round(rate, 1),
            "schedules": items,
        }
