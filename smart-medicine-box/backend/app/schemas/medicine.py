"""
药品、用药计划、用药记录相关的 Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, time


# ============== 药品 ==============

class MedicineCreate(BaseModel):
    """添加药品"""
    name: str = Field(..., min_length=1, max_length=128, description="药品名称")
    specification: Optional[str] = Field(None, max_length=64, description="规格")
    dosage: str = Field(..., max_length=32, description="单次用量")
    unit: str = Field(default="片", max_length=16, description="单位")
    frequency: str = Field(default="daily", description="用药频率: daily/every_other_day/weekly/as_needed")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_stock: int = Field(default=0, ge=0, description="总库存")
    stock_alert_threshold: int = Field(default=5, ge=1, description="库存告警阈值")
    box_position: Optional[str] = Field(None, max_length=16, description="药箱位置")
    image_url: Optional[str] = None
    notes: Optional[str] = None


class MedicineUpdate(BaseModel):
    """更新药品"""
    name: Optional[str] = Field(None, max_length=128)
    specification: Optional[str] = Field(None, max_length=64)
    dosage: Optional[str] = Field(None, max_length=32)
    unit: Optional[str] = Field(None, max_length=16)
    frequency: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_stock: Optional[int] = Field(None, ge=0)
    stock_alert_threshold: Optional[int] = Field(None, ge=1)
    box_position: Optional[str] = Field(None, max_length=16)
    image_url: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class MedicineResponse(BaseModel):
    """药品响应"""
    id: int
    name: str
    specification: Optional[str]
    dosage: str
    unit: str
    frequency: str
    start_date: Optional[date]
    end_date: Optional[date]
    total_stock: int
    remaining_stock: int
    stock_alert_threshold: int
    box_position: Optional[str]
    image_url: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MedicineListResponse(BaseModel):
    """药品列表响应"""
    total: int
    items: List[MedicineResponse]


# ============== 用药计划 ==============

class ScheduleCreate(BaseModel):
    """创建用药计划"""
    medicine_id: int = Field(..., description="药品ID")
    period: str = Field(..., description="时间段: morning/noon/evening/night")
    time_label: str = Field(..., max_length=32, description="时间标签（如：早饭后）")
    reminder_time: str = Field(..., description="提醒时间 HH:MM")
    dosage_at_time: str = Field(..., max_length=32, description="该时段用量")
    days_of_week: Optional[str] = Field(None, description="生效星期 1,2,3,4,5")


class ScheduleUpdate(BaseModel):
    """更新用药计划"""
    period: Optional[str] = None
    time_label: Optional[str] = Field(None, max_length=32)
    reminder_time: Optional[str] = None
    dosage_at_time: Optional[str] = Field(None, max_length=32)
    days_of_week: Optional[str] = None
    is_active: Optional[bool] = None


class ScheduleResponse(BaseModel):
    """用药计划响应"""
    id: int
    medicine_id: int
    medicine_name: str = ""
    medicine_specification: Optional[str] = None
    period: str
    time_label: str
    reminder_time: str
    dosage_at_time: str
    days_of_week: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============== 用药记录 ==============

class RecordCreate(BaseModel):
    """记录用药"""
    schedule_id: Optional[int] = None
    medicine_id: int = Field(..., description="药品ID")
    scheduled_time: datetime = Field(..., description="计划服用时间")
    actual_time: Optional[datetime] = None
    status: str = Field(default="taken", description="taken/missed/skipped")
    notes: Optional[str] = None


class RecordResponse(BaseModel):
    """用药记录响应"""
    id: int
    schedule_id: Optional[int]
    medicine_id: int
    medicine_name: str = ""
    medicine_dosage: str = ""
    scheduled_time: datetime
    actual_time: Optional[datetime]
    status: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============== 今日概览 ==============

class TodayScheduleItem(BaseModel):
    """今日用药计划项"""
    schedule_id: int
    medicine_id: int
    medicine_name: str
    dosage_at_time: str
    period: str
    time_label: str
    reminder_time: str
    status: str = "pending"  # pending/taken/missed
    box_position: Optional[str] = None


class TodayOverview(BaseModel):
    """今日用药概览"""
    date: str
    total_count: int = 0
    taken_count: int = 0
    missed_count: int = 0
    pending_count: int = 0
    adherence_rate: float = 0.0  # 依从率
    schedules: List[TodayScheduleItem] = []
