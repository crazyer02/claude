"""
智能药箱小程序 - FastAPI 主入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.database import init_db
from app.routers import user, medicine
from app.services.reminder_service import ReminderService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的操作"""
    print(f"\n{'='*50}")
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"  http://0.0.0.0:8000")
    print(f"  API docs: http://0.0.0.0:8000/docs")
    print(f"{'='*50}\n")

    # 初始化数据库
    init_db()
    print("[OK] SQLite database initialized")

    # 启动定时提醒任务
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        ReminderService.check_and_create_reminders,
        "interval",
        seconds=settings.REMINDER_CHECK_INTERVAL,
        id="check_reminders",
        name="检查用药提醒",
        misfire_grace_time=30,
        max_instances=1,
    )
    scheduler.add_job(
        ReminderService.generate_daily_records,
        "cron",
        hour=0,
        minute=5,
        id="generate_daily_records",
        name="生成次日用药记录",
        max_instances=1,
    )
    scheduler.start()
    print("[OK] Reminder scheduler started")

    yield

    scheduler.shutdown(wait=False)
    print(f"  {settings.APP_NAME} 已关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="智能药箱微信小程序后端 API - 面向老年人的用药提醒系统",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(user.router)
app.include_router(medicine.router)


@app.get("/api/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/", tags=["系统"])
async def root():
    return {"message": f"欢迎使用{settings.APP_NAME} API", "docs": "/docs", "version": settings.APP_VERSION}
