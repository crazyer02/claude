"""
药品、用药计划、用药记录模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Date, Time, ForeignKey, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from .database import Base


class MedicineFrequency(str, enum.Enum):
    """用药频率"""
    DAILY = "daily"             # 每天
    EVERY_OTHER_DAY = "every_other_day"  # 隔天
    WEEKLY = "weekly"           # 每周
    AS_NEEDED = "as_needed"     # 按需


class RecordStatus(str, enum.Enum):
    """用药记录状态"""
    TAKEN = "taken"       # 已服用
    MISSED = "missed"     # 未服用
    SKIPPED = "skipped"   # 跳过（医生建议）


class Relationship(str, enum.Enum):
    """家庭成员关系"""
    SON = "son"               # 儿子
    DAUGHTER = "daughter"     # 女儿
    SPOUSE = "spouse"         # 配偶
    GRANDSON = "grandson"     # 孙子
    GRANDDAUGHTER = "granddaughter"  # 孙女
    OTHER = "other"           # 其他


class Medicine(Base):
    """药品表 - 存储用户添加的药品信息"""

    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="药品ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    name = Column(String(128), nullable=False, comment="药品名称")
    specification = Column(String(64), nullable=True, comment="规格（如：10mg/片）")
    dosage = Column(String(32), nullable=False, comment="单次用量（如：1片）")
    unit = Column(String(16), default="片", comment="单位（片/粒/毫升/包）")
    frequency = Column(
        SAEnum(MedicineFrequency),
        default=MedicineFrequency.DAILY,
        comment="用药频率"
    )
    start_date = Column(Date, nullable=True, comment="开始日期")
    end_date = Column(Date, nullable=True, comment="结束日期")
    total_stock = Column(Integer, default=0, comment="总库存")
    remaining_stock = Column(Integer, default=0, comment="剩余库存")
    stock_alert_threshold = Column(Integer, default=5, comment="库存告警阈值")
    box_position = Column(String(16), nullable=True, comment="药箱位置编号（1-8号仓）")
    image_url = Column(String(512), nullable=True, comment="药品图片URL")
    notes = Column(Text, nullable=True, comment="备注")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    schedules = relationship("MedicineSchedule", back_populates="medicine", cascade="all, delete-orphan")
    records = relationship("MedicineRecord", back_populates="medicine", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Medicine(id={self.id}, name={self.name})>"


class MedicineSchedule(Base):
    """用药计划表 - 具体的用药时间安排"""

    __tablename__ = "medicine_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="计划ID")
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False, comment="药品ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")

    # 时间段类型
    period = Column(String(16), nullable=False, comment="时间段: morning/noon/evening/night")
    time_label = Column(String(32), nullable=False, comment="时间标签（如：早饭前、早饭后）")
    reminder_time = Column(Time, nullable=False, comment="提醒时间")
    dosage_at_time = Column(String(32), nullable=False, comment="该时段用量（如：1片）")

    days_of_week = Column(String(32), nullable=True, comment="生效星期（用逗号分隔：1,2,3,4,5）")

    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    medicine = relationship("Medicine", back_populates="schedules")

    def __repr__(self):
        return f"<MedicineSchedule(id={self.id}, period={self.period}, time={self.reminder_time})>"


class MedicineRecord(Base):
    """用药记录表 - 每次服药的记录"""

    __tablename__ = "medicine_records"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="记录ID")
    schedule_id = Column(Integer, ForeignKey("medicine_schedules.id", ondelete="SET NULL"), nullable=True, comment="计划ID")
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False, comment="药品ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")

    scheduled_time = Column(DateTime, nullable=False, comment="计划服用时间")
    actual_time = Column(DateTime, nullable=True, comment="实际服用时间")
    status = Column(
        SAEnum(RecordStatus),
        default=RecordStatus.MISSED,
        comment="状态: taken/missed/skipped"
    )
    notes = Column(Text, nullable=True, comment="备注")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 关联关系
    medicine = relationship("Medicine", back_populates="records")

    def __repr__(self):
        return f"<MedicineRecord(id={self.id}, status={self.status})>"


class FamilyBinding(Base):
    """家人绑定表 - 子女绑定老人"""

    __tablename__ = "family_bindings"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="绑定ID")
    elderly_user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="老年用户ID"
    )
    family_user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="家人用户ID"
    )
    relationship = Column(
        SAEnum(Relationship),
        nullable=False, comment="关系"
    )
    is_primary = Column(Boolean, default=False, comment="是否为主要监护人")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<FamilyBinding(elderly={self.elderly_user_id}, family={self.family_user_id})>"
