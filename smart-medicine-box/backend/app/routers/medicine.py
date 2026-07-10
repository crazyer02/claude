"""
药品、用药计划、用药记录相关 API 路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models import get_db, User
from app.schemas.medicine import (
    MedicineCreate, MedicineUpdate, MedicineResponse, MedicineListResponse,
    ScheduleCreate, ScheduleUpdate, ScheduleResponse,
    RecordCreate, RecordResponse,
    TodayOverview,
)
from app.services.medicine_service import MedicineService
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api", tags=["药品 & 用药"])


# ==================== 药品管理 ====================

@router.post("/medicines", response_model=MedicineResponse, summary="添加药品")
async def create_medicine(
    request: MedicineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """添加新的药品到药箱"""
    try:
        medicine = MedicineService.create_medicine(db, current_user.id, request)
        return MedicineResponse.model_validate(medicine)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/medicines", response_model=MedicineListResponse, summary="获取药品列表")
async def get_medicines(
    is_active: Optional[bool] = Query(None, description="筛选启用/禁用状态"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的所有药品"""
    medicines = MedicineService.get_medicines(db, current_user.id, is_active)
    return MedicineListResponse(
        total=len(medicines),
        items=[MedicineResponse.model_validate(m) for m in medicines],
    )


@router.get("/medicines/{medicine_id}", response_model=MedicineResponse, summary="获取药品详情")
async def get_medicine(
    medicine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取指定药品的详细信息"""
    try:
        medicine = MedicineService.get_medicine(db, medicine_id, current_user.id)
        return MedicineResponse.model_validate(medicine)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/medicines/{medicine_id}", response_model=MedicineResponse, summary="更新药品")
async def update_medicine(
    medicine_id: int,
    request: MedicineUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新药品信息（名称、用量、库存等）"""
    try:
        medicine = MedicineService.update_medicine(db, medicine_id, current_user.id, request)
        return MedicineResponse.model_validate(medicine)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/medicines/{medicine_id}", summary="删除药品")
async def delete_medicine(
    medicine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """软删除药品（标记为不可用）"""
    try:
        MedicineService.delete_medicine(db, medicine_id, current_user.id)
        return {"message": "删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/medicines/low-stock", response_model=MedicineListResponse, summary="获取库存不足的药品")
async def get_low_stock(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取库存低于告警阈值的药品列表"""
    medicines = MedicineService.get_low_stock_medicines(db, current_user.id)
    return MedicineListResponse(
        total=len(medicines),
        items=[MedicineResponse.model_validate(m) for m in medicines],
    )


# ==================== 用药计划 ====================

@router.post("/schedules", response_model=ScheduleResponse, summary="创建用药计划")
async def create_schedule(
    request: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """为指定药品创建用药时间计划（早/中/晚/睡前）"""
    try:
        schedule = MedicineService.create_schedule(db, current_user.id, request)
        # 构造响应（包含药品名）
        result = ScheduleResponse(
            id=schedule.id,
            medicine_id=schedule.medicine_id,
            medicine_name=schedule.medicine.name if schedule.medicine else "",
            medicine_specification=schedule.medicine.specification if schedule.medicine else None,
            period=schedule.period,
            time_label=schedule.time_label,
            reminder_time=schedule.reminder_time.strftime("%H:%M") if schedule.reminder_time else "",
            dosage_at_time=schedule.dosage_at_time,
            days_of_week=schedule.days_of_week,
            is_active=schedule.is_active,
            created_at=schedule.created_at,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/schedules", response_model=list[ScheduleResponse], summary="获取用药计划列表")
async def get_schedules(
    medicine_id: Optional[int] = Query(None, description="按药品筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取所有用药时间计划"""
    return MedicineService.get_schedules(db, current_user.id, medicine_id)


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse, summary="更新用药计划")
async def update_schedule(
    schedule_id: int,
    request: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新用药计划（修改时间、用量等）"""
    try:
        schedule = MedicineService.update_schedule(db, schedule_id, current_user.id, request)
        return ScheduleResponse(
            id=schedule.id,
            medicine_id=schedule.medicine_id,
            medicine_name=schedule.medicine.name if schedule.medicine else "",
            period=schedule.period,
            time_label=schedule.time_label,
            reminder_time=schedule.reminder_time.strftime("%H:%M") if schedule.reminder_time else "",
            dosage_at_time=schedule.dosage_at_time,
            days_of_week=schedule.days_of_week,
            is_active=schedule.is_active,
            created_at=schedule.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/schedules/{schedule_id}", summary="删除用药计划")
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除用药计划"""
    try:
        MedicineService.delete_schedule(db, schedule_id, current_user.id)
        return {"message": "删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== 用药记录 ====================

@router.post("/records", response_model=RecordResponse, summary="记录用药")
async def create_record(
    request: RecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """记录一次用药（已服用/未服用/跳过）"""
    try:
        record = MedicineService.create_record(db, current_user.id, request)
        return RecordResponse(
            id=record.id,
            schedule_id=record.schedule_id,
            medicine_id=record.medicine_id,
            medicine_name=record.medicine.name if record.medicine else "",
            medicine_dosage=record.medicine.dosage if record.medicine else "",
            scheduled_time=record.scheduled_time,
            actual_time=record.actual_time,
            status=record.status.value if hasattr(record.status, 'value') else record.status,
            notes=record.notes,
            created_at=record.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/records", response_model=list[RecordResponse], summary="获取用药记录")
async def get_records(
    date: Optional[str] = Query(None, description="日期 YYYY-MM-DD"),
    medicine_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None, description="taken/missed/skipped"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """分条件查询用药记录"""
    return MedicineService.get_records(db, current_user.id, date, medicine_id, status)


@router.get("/today", response_model=TodayOverview, summary="今日用药概览")
async def get_today_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取今日用药概览 - 首页核心接口"""
    return MedicineService.get_today_overview(db, current_user.id)
