"""
提醒服务 - 定时检查用药提醒、发送微信订阅消息
"""
import asyncio
from datetime import datetime, date, time, timedelta
from typing import List
from sqlalchemy.orm import Session

from app.config import settings
from app.models import MedicineSchedule, MedicineRecord, Medicine
from app.models.medicine import RecordStatus
from app.models.database import SessionLocal


class ReminderService:
    """用药提醒服务"""

    @staticmethod
    async def check_and_create_reminders():
        """
        定时任务：检查当前时间需要提醒的用药计划，生成待处理记录
        建议通过 APScheduler 每60秒运行一次
        """
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            today = now.date()
            weekday = today.isoweekday()
            current_time = now.time()

            # 获取所有活跃的用药计划
            schedules = db.query(MedicineSchedule).filter(
                MedicineSchedule.is_active == True,
            ).all()

            for s in schedules:
                # 检查药品是否启用
                medicine = db.query(Medicine).filter(
                    Medicine.id == s.medicine_id,
                    Medicine.is_active == True,
                ).first()
                if not medicine:
                    continue

                # 检查日期范围
                if medicine.start_date and medicine.start_date > today:
                    continue
                if medicine.end_date and medicine.end_date < today:
                    continue

                # 检查星期
                if s.days_of_week:
                    allowed_days = [int(d.strip()) for d in s.days_of_week.split(",")]
                    if weekday not in allowed_days:
                        continue

                # 计算提醒时间窗口
                reminder_dt = datetime.combine(today, s.reminder_time)
                advance = timedelta(minutes=settings.REMINDER_ADVANCE_MINUTES)
                window_start = reminder_dt - advance
                window_end = reminder_dt + timedelta(minutes=30)  # 30分钟窗口

                if window_start <= now <= window_end:
                    # 检查是否已生成记录
                    existing = db.query(MedicineRecord).filter(
                        MedicineRecord.schedule_id == s.id,
                        MedicineRecord.user_id == s.user_id,
                        MedicineRecord.scheduled_time == reminder_dt,
                    ).first()

                    if not existing:
                        # 生成待处理记录
                        record = MedicineRecord(
                            schedule_id=s.id,
                            medicine_id=s.medicine_id,
                            user_id=s.user_id,
                            scheduled_time=reminder_dt,
                            status=RecordStatus.MISSED,  # 初始状态为未服用
                        )
                        db.add(record)
                        db.flush()

                        # 发送微信订阅消息提醒
                        await ReminderService.send_wechat_reminder(
                            db=db,
                            user_id=s.user_id,
                            medicine_name=medicine.name,
                            dosage=s.dosage_at_time,
                            schedule_id=s.id,
                            box_position=medicine.box_position,
                        )

            db.commit()
        except Exception as e:
            db.rollback()
            print(f"提醒检查异常: {e}")
        finally:
            db.close()

    @staticmethod
    async def send_wechat_reminder(
        db: Session,
        user_id: int,
        medicine_name: str,
        dosage: str,
        schedule_id: int,
        box_position: str = None,
    ):
        """
        发送微信小程序订阅消息提醒
        https://developers.weixin.qq.com/miniprogram/dev/api-backend/open-api/subscribe-message/subscribeMessage.send.html
        """
        # 获取用户的 openid
        from app.models import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        # 微信订阅消息模板ID（需在微信公众平台申请）
        template_id = "your-subscribe-template-id"

        # 构造消息体
        message_data = {
            "touser": user.openid,
            "template_id": template_id,
            "page": f"pages/index/index?schedule_id={schedule_id}",
            "data": {
                "thing1": {"value": medicine_name[:20]},      # 药品名称
                "thing2": {"value": dosage[:20]},             # 用量
                "time3": {"value": datetime.utcnow().strftime("%H:%M")},  # 提醒时间
                "thing4": {"value": f"请按时服药" if not box_position else f"请在{box_position}号仓取药"}
            },
            "miniprogram_state": "formal",  # formal/trial/developer
        }

        # 调用微信发送接口
        # 这里需要 access_token，实际项目中应缓存 access_token
        # access_token = await WechatService.get_access_token()
        # httpx.post(f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}", json=message_data)

        print(f"[提醒] 用户{user_id} - {medicine_name} {dosage} - 提醒时间: {datetime.utcnow()}")
        # TODO: 接入实际微信订阅消息发送

    @staticmethod
    def generate_daily_records(db: Session):
        """
        为所有用户生成明天的用药记录（凌晨运行）
        可通过 APScheduler cron 任务在每天00:00执行
        """
        tomorrow = date.today() + timedelta(days=1)
        weekday = tomorrow.isoweekday()

        schedules = db.query(MedicineSchedule).filter(
            MedicineSchedule.is_active == True,
        ).all()

        created = 0
        for s in schedules:
            # 检查星期
            if s.days_of_week:
                allowed_days = [int(d.strip()) for d in s.days_of_week.split(",")]
                if weekday not in allowed_days:
                    continue

            # 检查药品
            medicine = db.query(Medicine).filter(
                Medicine.id == s.medicine_id,
                Medicine.is_active == True,
            ).first()
            if not medicine:
                continue
            if medicine.start_date and medicine.start_date > tomorrow:
                continue
            if medicine.end_date and medicine.end_date < tomorrow:
                continue

            # 生成记录
            scheduled_dt = datetime.combine(tomorrow, s.reminder_time)
            existing = db.query(MedicineRecord).filter(
                MedicineRecord.schedule_id == s.id,
                MedicineRecord.scheduled_time == scheduled_dt,
            ).first()
            if not existing:
                record = MedicineRecord(
                    schedule_id=s.id,
                    medicine_id=s.medicine_id,
                    user_id=s.user_id,
                    scheduled_time=scheduled_dt,
                    status=RecordStatus.MISSED,
                )
                db.add(record)
                created += 1

        db.commit()
        print(f"已为明天({tomorrow})生成{created}条用药记录")
        return created


# 单例
reminder_service = ReminderService()
