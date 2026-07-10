"""
微信登录认证 & JWT 工具
"""
import httpx
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.database import get_db, row_to_dict

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """生成 JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """解析 JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


async def wechat_login(code: str) -> Dict[str, str]:
    """微信小程序登录 - 通过 code 换取 openid 和 session_key"""
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        result = resp.json()

    if "errcode" in result and result["errcode"] != 0:
        raise HTTPException(status_code=400, detail=f"微信登录失败: {result.get('errmsg', '未知错误')}")

    return result


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    """从请求的 Authorization Header 中提取当前用户"""
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="无效的认证凭证")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效的认证信息")

    cursor = conn.execute(
        "SELECT * FROM users WHERE id = ? AND is_active = 1", (int(user_id),)
    )
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在或已禁用")

    return row_to_dict(user)
