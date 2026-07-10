"""
智能药箱小程序 - 配置文件
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "智能药箱"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/smart_medicine_box?charset=utf8mb4"

    # Redis 配置（用于消息队列和缓存）
    REDIS_URL: str = "redis://localhost:6379/0"

    # 微信小程序配置
    WECHAT_APPID: str = "your-wechat-appid"
    WECHAT_SECRET: str = "your-wechat-secret"

    # JWT 配置
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # 定时任务
    REMINDER_CHECK_INTERVAL: int = 60  # 每60秒检查一次提醒

    # 用药提醒提前量（分钟）
    REMINDER_ADVANCE_MINUTES: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
