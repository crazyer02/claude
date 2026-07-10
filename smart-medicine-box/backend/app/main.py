"""
智能药箱小程序 - FastAPI 主入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.models.database import engine, Base
from app.routers import user, medicine
from app.services.reminder_service import ReminderService


# ==================== 应用生命周期 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的操作"""
    # 启动时：创建数据库表、启动定时任务
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")

    # 创建数据库表（开发环境用，生产环境建议用 Alembic 迁移）
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表检查完成")

    # 启动定时提醒任务
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        ReminderService.check_and_create_reminders,
        "interval",
        seconds=settings.REMINDER_CHECK_INTERVAL,
        id="check_reminders",
        name="检查用药提醒",
        misfire_grace_time=30,
    )
    # 每天凌晨 00:05 生成次日用药记录
    scheduler.add_job(
        ReminderService.generate_daily_records,
        "cron",
        hour=0,
        minute=5,
        id="generate_daily_records",
        name="生成次日用药记录",
        args=[None],  # db session 在函数内部创建
    )
    scheduler.start()
    print("⏰ 定时提醒任务已启动")

    yield

    # 关闭时
    scheduler.shutdown(wait=False)
    print(f"👋 {settings.APP_NAME} 已关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="智能药箱微信小程序后端 API - 面向老年人的用药提醒系统",
    lifespan=lifespan,
)

# ==================== 中间件 ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 路由注册 ====================

app.include_router(user.router)
app.include_router(medicine.router)


# ==================== 健康检查 ====================

@app.get("/api/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用{settings.APP_NAME} API",
        "docs": "/docs",
        "version": settings.APP_VERSION,
    }
