"""
药品服务 - 处理药品CRUD和库存管理
"""
from typing import List, Optional
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session

from app.models import Medicine, MedicineSchedule, MedicineRecord
from app.models.medicine import MedicineFrequency, RecordStatus
from app.schemas.medicine import (
    MedicineCreate, MedicineUpdate, MedicineResponse,
    ScheduleCreate, ScheduleUpdate, ScheduleResponse,
    RecordCreate, RecordResponse,
    TodayScheduleItem, TodayOverview,
)


class MedicineService:
    """药品服务"""

    # ============== 药品管理 ==============

    @staticmethod
    def create_medicine(db: Session, user_id: int, data: MedicineCreate) -> Medicine:
        """添加药品"""
        medicine = Medicine(
            user_id=user_id,
            name=data.name,
            specification=data.specification,
            dosage=data.dosage,
            unit=data.unit,
            frequency=MedicineFrequency(data.frequency),
            start_date=data.start_date,
            end_date=data.end_date,
            total_stock=data.total_stock,
            remaining_stock=data.total_stock,  # 初始剩余=总库存
            stock_alert_threshold=data.stock_alert_threshold,
            box_position=data.box_position,
            image_url=data.image_url,
            notes=data.notes,
        )
        db.add(medicine)
        db.commit()
        db.refresh(medicine)
        return medicine

    @staticmethod
    def get_medicines(
        db: Session,
        user_id: int,
        is_active: Optional[bool] = None,
    ) -> List[Medicine]:
        """获取用户的所有药品"""
        query = db.query(Medicine).filter(Medicine.user_id == user_id)
        if is_active is not None:
            query = query.filter(Medicine.is_active == is_active)
        return query.order_by(Medicine.created_at.desc()).all()

    @staticmethod
    def get_medicine(db: Session, medicine_id: int, user_id: int) -> Medicine:
        """获取单个药品"""
        medicine = db.query(Medicine).filter(
            Medicine.id == medicine_id,
            Medicine.user_id == user_id,
        ).first()
        if not medicine:
            raise ValueError("药品不存在")
        return medicine

    @staticmethod
    def update_medicine(
        db: Session, medicine_id: int, user_id: int, data: MedicineUpdate
    ) -> Medicine:
        """更新药品信息"""
        medicine = MedicineService.get_medicine(db, medicine_id, user_id)
        update_data = data.model_dump(exclude_unset=True)

        # 如果更新了总库存，同步调整剩余库存
        if "total_stock" in update_data:
            old_total = medicine.total_stock
            old_remaining = medicine.remaining_stock
            # 按比例调整
            if old_total > 0:
                ratio = update_data["total_stock"] / old_total
                update_data["remaining_stock"] = int(old_remaining * ratio)
            else:
                update_data["remaining_stock"] = update_data["total_stock"]

        for key, value in update_data.items():
            setattr(medicine, key, value)
        db.commit()
        db.refresh(medicine)
        return medicine

    @staticmethod
    def delete_medicine(db: Session, medicine_id: int, user_id: int) -> bool:
        """删除药品（软删除）"""
        medicine = MedicineService.get_medicine(db, medicine_id, user_id)
        medicine.is_active = False
        db.commit()
        return True

    @staticmethod
    def update_stock(db: Session, medicine_id: int, user_id: int, used: int = 1) -> Medicine:
        """更新药品库存（-1等）"""
        medicine = MedicineService.get_medicine(db, medicine_id, user_id)
        medicine.remaining_stock = max(0, medicine.remaining_stock - used)
        db.commit()
        db.refresh(medicine)
        return medicine

    @staticmethod
    def get_low_stock_medicines(db: Session, user_id: int) -> List[Medicine]:
        """获取库存不足的药品"""
        return db.query(Medicine).filter(
            Medicine.user_id == user_id,
            Medicine.is_active == True,
            Medicine.remaining_stock <= Medicine.stock_alert_threshold,
        ).all()

    # ============== 用药计划 ==============

    @staticmethod
    def create_schedule(db: Session, user_id: int, data: ScheduleCreate) -> MedicineSchedule:
        """创建用药计划"""
        # 验证药品属于该用户
        MedicineService.get_medicine(db, data.medicine_id, user_id)

        # 解析提醒时间
        hour, minute = map(int, data.reminder_time.split(":"))
        reminder_time = time(hour=hour, minute=minute)

        schedule = MedicineSchedule(
            medicine_id=data.medicine_id,
            user_id=user_id,
            period=data.period,
            time_label=data.time_label,
            reminder_time=reminder_time,
            dosage_at_time=data.dosage_at_time,
            days_of_week=data.days_of_week,
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def get_schedules(db: Session, user_id: int, medicine_id: Optional[int] = None) -> List[ScheduleResponse]:
        """获取用药计划列表"""
        query = db.query(MedicineSchedule).filter(
            MedicineSchedule.user_id == user_id,
            MedicineSchedule.is_active == True,
        )
        if medicine_id:
            query = query.filter(MedicineSchedule.medicine_id == medicine_id)
        schedules = query.order_by(MedicineSchedule.reminder_time).all()

        result = []
        for s in schedules:
            result.append(ScheduleResponse(
                id=s.id,
                medicine_id=s.medicine_id,
                medicine_name=s.medicine.name if s.medicine else "",
                medicine_specification=s.medicine.specification if s.medicine else None,
                period=s.period,
                time_label=s.time_label,
                reminder_time=s.reminder_time.strftime("%H:%M") if s.reminder_time else "",
                dosage_at_time=s.dosage_at_time,
                days_of_week=s.days_of_week,
                is_active=s.is_active,
                created_at=s.created_at,
            ))
        return result

    @staticmethod
    def update_schedule(
        db: Session, schedule_id: int, user_id: int, data: ScheduleUpdate
    ) -> MedicineSchedule:
        """更新用药计划"""
        schedule = db.query(MedicineSchedule).filter(
            MedicineSchedule.id == schedule_id,
            MedicineSchedule.user_id == user_id,
        ).first()
        if not schedule:
            raise ValueError("用药计划不存在")

        update_data = data.model_dump(exclude_unset=True)
        if "reminder_time" in update_data and isinstance(update_data["reminder_time"], str):
            hour, minute = map(int, update_data["reminder_time"].split(":"))
            update_data["reminder_time"] = time(hour=hour, minute=minute)

        for key, value in update_data.items():
            setattr(schedule, key, value)
        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def delete_schedule(db: Session, schedule_id: int, user_id: int) -> bool:
        """删除用药计划"""
        schedule = db.query(MedicineSchedule).filter(
            MedicineSchedule.id == schedule_id,
            MedicineSchedule.user_id == user_id,
        ).first()
        if not schedule:
            raise ValueError("用药计划不存在")
        schedule.is_active = False
        db.commit()
        return True

    # ============== 用药记录 ==============

    @staticmethod
    def create_record(db: Session, user_id: int, data: RecordCreate) -> MedicineRecord:
        """记录用药"""
        MedicineService.get_medicine(db, data.medicine_id, user_id)

        record = MedicineRecord(
            schedule_id=data.schedule_id,
            medicine_id=data.medicine_id,
            user_id=user_id,
            scheduled_time=data.scheduled_time,
            actual_time=data.actual_time or datetime.utcnow(),
            status=RecordStatus(data.status),
            notes=data.notes,
        )
        db.add(record)

        # 如果已服用，自动减库存
        if data.status == "taken":
            MedicineService.update_stock(db, data.medicine_id, user_id)

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_records(
        db: Session,
        user_id: int,
        date_str: Optional[str] = None,
        medicine_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[RecordResponse]:
        """获取用药记录"""
        query = db.query(MedicineRecord).filter(MedicineRecord.user_id == user_id)

        if date_str:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            day_start = datetime.combine(target_date, datetime.min.time())
            day_end = datetime.combine(target_date, datetime.max.time())
            query = query.filter(
                MedicineRecord.scheduled_time >= day_start,
                MedicineRecord.scheduled_time <= day_end,
            )

        if medicine_id:
            query = query.filter(MedicineRecord.medicine_id == medicine_id)

        if status:
            query = query.filter(MedicineRecord.status == RecordStatus(status))

        records = query.order_by(MedicineRecord.scheduled_time.desc()).limit(limit).all()

        return [
            RecordResponse(
                id=r.id,
                schedule_id=r.schedule_id,
                medicine_id=r.medicine_id,
                medicine_name=r.medicine.name if r.medicine else "",
                medicine_dosage=r.medicine.dosage if r.medicine else "",
                scheduled_time=r.scheduled_time,
                actual_time=r.actual_time,
                status=r.status.value if hasattr(r.status, 'value') else r.status,
                notes=r.notes,
                created_at=r.created_at,
            )
            for r in records
        ]

    # ============== 今日概览 ==============

    @staticmethod
    def get_today_overview(db: Session, user_id: int) -> TodayOverview:
        """获取今日用药概览 - 首页核心数据"""
        today = datetime.utcnow().date()
        weekday = today.isoweekday()  # 1-7 (周一至周日)

        # 获取所有活跃的用药计划
        schedules = db.query(MedicineSchedule).filter(
            MedicineSchedule.user_id == user_id,
            MedicineSchedule.is_active == True,
        ).all()

        # 过滤今天应该执行的计划
        today_items: List[TodayScheduleItem] = []
        for s in schedules:
            # 检查星期
            if s.days_of_week:
                allowed_days = [int(d.strip()) for d in s.days_of_week.split(",")]
                if weekday not in allowed_days:
                    continue

            # 检查药品是否启用
            if not s.medicine or not s.medicine.is_active:
                continue

            # 检查日期范围
            if s.medicine.start_date and s.medicine.start_date > today:
                continue
            if s.medicine.end_date and s.medicine.end_date < today:
                continue

            # 构造计划时间
            scheduled_datetime = datetime.combine(today, s.reminder_time)

            # 查找今天的记录
            record = db.query(MedicineRecord).filter(
                MedicineRecord.schedule_id == s.id,
                MedicineRecord.user_id == user_id,
                MedicineRecord.scheduled_time == scheduled_datetime,
            ).first()

            status = "pending"
            if record:
                status = record.status.value if hasattr(record.status, 'value') else record.status

            today_items.append(TodayScheduleItem(
                schedule_id=s.id,
                medicine_id=s.medicine_id,
                medicine_name=s.medicine.name,
                dosage_at_time=s.dosage_at_time,
                period=s.period,
                time_label=s.time_label,
                reminder_time=s.reminder_time.strftime("%H:%M") if s.reminder_time else "",
                status=status,
                box_position=s.medicine.box_position,
            ))

        # 排序：按时间
        today_items.sort(key=lambda x: x.reminder_time)

        total = len(today_items)
        taken = sum(1 for item in today_items if item.status == "taken")
        missed = sum(1 for item in today_items if item.status == "missed")
        pending = sum(1 for item in today_items if item.status == "pending")

        # 过去时间的 pending 视为 missed
        now = datetime.utcnow()
        for item in today_items:
            if item.status == "pending":
                item_time = datetime.combine(today, time.fromisoformat(item.reminder_time))
                if item_time < now - timedelta(hours=1):  # 超过1小时未服用
                    item.status = "missed"
                    missed += 1
                    pending -= 1

        # 重新计算
        taken = sum(1 for item in today_items if item.status == "taken")
        rate = (taken / total * 100) if total > 0 else 0.0

        return TodayOverview(
            date=today.strftime("%Y-%m-%d"),
            total_count=total,
            taken_count=taken,
            missed_count=missed,
            pending_count=max(0, pending),
            adherence_rate=round(rate, 1),
            schedules=today_items,
        )
