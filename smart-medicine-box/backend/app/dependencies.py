"""
FastAPI 依赖注入
"""
from fastapi import Request
from app.database import get_connection


def get_db(request: Request):
    """
    获取当前请求的数据库连接。
    连接由中间件管理生命周期（commit/rollback/close）。
    """
    if not hasattr(request.state, "db_conn"):
        request.state.db_conn = get_connection()
    return request.state.db_conn
