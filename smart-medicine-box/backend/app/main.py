"""
智能药箱小程序 - FastAPI 主入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.database import init_db, get_connection, close_db, get_db
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

    init_db()
    print("[OK] SQLite database initialized")

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        ReminderService.check_and_create_reminders,
        "interval",
        seconds=settings.REMINDER_CHECK_INTERVAL,
        id="check_reminders",
        name="check reminders",
        misfire_grace_time=30,
        max_instances=1,
    )
    scheduler.add_job(
        ReminderService.generate_daily_records,
        "cron",
        hour=0,
        minute=5,
        id="generate_daily_records",
        name="generate daily records",
        max_instances=1,
    )
    scheduler.start()
    print("[OK] Reminder scheduler started")

    yield

    scheduler.shutdown(wait=False)
    print(f"  {settings.APP_NAME} stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="智能药箱微信小程序后端 API",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 数据库中间件：每个请求自动打开/提交/关闭连接
@app.middleware("http")
async def db_middleware(request: Request, call_next):
    conn = get_connection()
    # 存入线程本地存储
    import app.database as db_module
    db_module._local.conn = conn
    try:
        response = await call_next(request)
        conn.commit()
        return response
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
        db_module._local.conn = None


app.include_router(user.router)
app.include_router(medicine.router)


@app.get("/api/health", tags=["system"])
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/", tags=["system"])
async def root():
    return {"message": f"欢迎使用{settings.APP_NAME} API", "docs": "/docs", "version": settings.APP_VERSION}
