"""
药品、用药计划、用药记录相关 API 路由
"""
import sqlite3
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.dependencies import get_db
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
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """添加新的药品到药箱"""
    medicine = MedicineService.create_medicine(conn, current_user["id"], request.model_dump())
    return MedicineResponse(**medicine)


@router.get("/medicines", response_model=MedicineListResponse, summary="获取药品列表")
async def get_medicines(
    is_active: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """获取当前用户的所有药品"""
    medicines = MedicineService.get_medicines(conn, current_user["id"], is_active)
    return MedicineListResponse(
        total=len(medicines),
        items=[MedicineResponse(**m) for m in medicines],
    )


@router.get("/medicines/low-stock", response_model=MedicineListResponse, summary="库存不足药品")
async def get_low_stock(
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """获取库存低于告警阈值的药品列表"""
    medicines = MedicineService.get_low_stock_medicines(conn, current_user["id"])
    return MedicineListResponse(
        total=len(medicines),
        items=[MedicineResponse(**m) for m in medicines],
    )


@router.get("/medicines/{medicine_id}", response_model=MedicineResponse, summary="获取药品详情")
async def get_medicine(
    medicine_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """获取指定药品的详细信息"""
    try:
        medicine = MedicineService.get_medicine(conn, medicine_id, current_user["id"])
        return MedicineResponse(**medicine)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/medicines/{medicine_id}", response_model=MedicineResponse, summary="更新药品")
async def update_medicine(
    medicine_id: int,
    request: MedicineUpdate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """更新药品信息"""
    try:
        medicine = MedicineService.update_medicine(conn, medicine_id, current_user["id"], request.model_dump())
        return MedicineResponse(**medicine)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/medicines/{medicine_id}", summary="删除药品")
async def delete_medicine(
    medicine_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """软删除药品"""
    try:
        MedicineService.delete_medicine(conn, medicine_id, current_user["id"])
        return {"message": "删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))



# ==================== 用药计划 ====================

@router.post("/schedules", response_model=ScheduleResponse, summary="创建用药计划")
async def create_schedule(
    request: ScheduleCreate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """为指定药品创建用药时间计划"""
    try:
        schedule = MedicineService.create_schedule(conn, current_user["id"], request.model_dump())
        return ScheduleResponse(**schedule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/schedules", response_model=list[ScheduleResponse], summary="获取用药计划列表")
async def get_schedules(
    medicine_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """获取所有用药时间计划"""
    schedules = MedicineService.get_schedules(conn, current_user["id"], medicine_id)
    return [ScheduleResponse(**s) for s in schedules]


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse, summary="更新用药计划")
async def update_schedule(
    schedule_id: int,
    request: ScheduleUpdate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """更新用药计划"""
    try:
        schedule = MedicineService.update_schedule(conn, schedule_id, current_user["id"], request.model_dump())
        return ScheduleResponse(**schedule)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/schedules/{schedule_id}", summary="删除用药计划")
async def delete_schedule(
    schedule_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """删除用药计划"""
    try:
        MedicineService.delete_schedule(conn, schedule_id, current_user["id"])
        return {"message": "删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== 用药记录 ====================

@router.post("/records", response_model=RecordResponse, summary="记录用药")
async def create_record(
    request: RecordCreate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """记录一次用药（已服用/未服用/跳过）"""
    try:
        record = MedicineService.create_record(conn, current_user["id"], request.model_dump())
        return RecordResponse(**record)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/records", response_model=list[RecordResponse], summary="获取用药记录")
async def get_records(
    date: Optional[str] = Query(None),
    medicine_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """分条件查询用药记录"""
    records = MedicineService.get_records(conn, current_user["id"], date, medicine_id, status)
    return [RecordResponse(**r) for r in records]


@router.get("/today", response_model=TodayOverview, summary="今日用药概览")
async def get_today_overview(
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """获取今日用药概览 - 首页核心接口"""
    overview = MedicineService.get_today_overview(conn, current_user["id"])
    return TodayOverview(**overview)
