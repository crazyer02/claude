"""
提醒服务 - 定时检查用药提醒、发送微信订阅消息
"""
import sqlite3
from datetime import datetime, date, timedelta
from app.database import get_connection, row_to_dict
from app.config import settings


class ReminderService:
    """用药提醒服务"""

    @staticmethod
    def check_and_create_reminders():
        """定时任务：检查当前时间需要提醒的用药计划"""
        conn = get_connection()
        try:
            now = datetime.utcnow()
            today = now.date()
            weekday = today.isoweekday()
            today_str = today.strftime("%Y-%m-%d")

            cursor = conn.execute("""
                SELECT s.*, m.name as medicine_name, m.box_position
                FROM medicine_schedules s
                JOIN medicines m ON m.id = s.medicine_id
                WHERE s.is_active = 1 AND m.is_active = 1
            """)
            schedules = cursor.fetchall()

            for s in schedules:
                s = row_to_dict(s)
                # 检查日期范围
                if s.get("start_date") and s["start_date"] > today_str:
                    continue
                if s.get("end_date") and s["end_date"] < today_str:
                    continue
                # 检查星期
                if s.get("days_of_week"):
                    allowed = [int(d.strip()) for d in s["days_of_week"].split(",")]
                    if weekday not in allowed:
                        continue

                # 解析提醒时间
                parts = s["reminder_time"].split(":")
                reminder_dt = datetime(today.year, today.month, today.day, int(parts[0]), int(parts[1]))
                advance = timedelta(minutes=settings.REMINDER_ADVANCE_MINUTES)
                window_end = reminder_dt + timedelta(minutes=30)

                if reminder_dt - advance <= now <= window_end:
                    scheduled_str = f"{today_str}T{s['reminder_time']}:00"
                    # 检查是否已生成记录
                    cursor2 = conn.execute(
                        "SELECT id FROM medicine_records WHERE schedule_id = ? AND user_id = ? AND scheduled_time = ?",
                        (s["id"], s["user_id"], scheduled_str)
                    )
                    if not cursor2.fetchone():
                        conn.execute("""
                            INSERT INTO medicine_records (schedule_id, medicine_id, user_id, scheduled_time, status)
                            VALUES (?, ?, ?, ?, 'missed')
                        """, (s["id"], s["medicine_id"], s["user_id"], scheduled_str))

                        print(f"[提醒] 用户{s['user_id']} - {s['medicine_name']} {s['dosage_at_time']} - {s['reminder_time']}")

            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"提醒检查异常: {e}")
        finally:
            conn.close()

    @staticmethod
    def generate_daily_records():
        """为所有用户生成明天的用药记录（凌晨运行）"""
        conn = get_connection()
        try:
            tomorrow = date.today() + timedelta(days=1)
            tomorrow_str = tomorrow.strftime("%Y-%m-%d")
            weekday = tomorrow.isoweekday()

            cursor = conn.execute("""
                SELECT s.*, m.start_date, m.end_date
                FROM medicine_schedules s
                JOIN medicines m ON m.id = s.medicine_id
                WHERE s.is_active = 1 AND m.is_active = 1
            """)
            schedules = cursor.fetchall()

            created = 0
            for s in schedules:
                s = row_to_dict(s)
                if s.get("days_of_week"):
                    allowed = [int(d.strip()) for d in s["days_of_week"].split(",")]
                    if weekday not in allowed:
                        continue
                if s.get("start_date") and s["start_date"] > tomorrow_str:
                    continue
                if s.get("end_date") and s["end_date"] < tomorrow_str:
                    continue

                scheduled_str = f"{tomorrow_str}T{s['reminder_time']}:00"
                cursor2 = conn.execute(
                    "SELECT id FROM medicine_records WHERE schedule_id = ? AND scheduled_time = ?",
                    (s["id"], scheduled_str)
                )
                if not cursor2.fetchone():
                    conn.execute("""
                        INSERT INTO medicine_records (schedule_id, medicine_id, user_id, scheduled_time, status)
                        VALUES (?, ?, ?, ?, 'missed')
                    """, (s["id"], s["medicine_id"], s["user_id"], scheduled_str))
                    created += 1

            conn.commit()
            print(f"已为明天({tomorrow_str})生成{created}条用药记录")
            return created
        except Exception as e:
            conn.rollback()
            print(f"生成记录异常: {e}")
        finally:
            conn.close()
