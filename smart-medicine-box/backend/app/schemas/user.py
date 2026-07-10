"""
用户相关的 Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserLoginRequest(BaseModel):
    """微信小程序登录请求"""
    code: str = Field(..., description="微信登录凭证code")


class UserUpdateRequest(BaseModel):
    """用户信息更新"""
    nickname: Optional[str] = Field(None, max_length=64)
    avatar_url: Optional[str] = Field(None, max_length=512)
    phone: Optional[str] = Field(None, max_length=20)
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[int] = Field(None, ge=0, le=2)
    emergency_contact: Optional[str] = Field(None, max_length=20)
    emergency_contact_name: Optional[str] = Field(None, max_length=32)
    remark: Optional[str] = None


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    nickname: Optional[str]
    avatar_url: Optional[str]
    phone: Optional[str]
    age: Optional[int]
    gender: Optional[int]
    emergency_contact: Optional[str]
    emergency_contact_name: Optional[str]
    is_elderly: bool
    remark: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class FamilyBindRequest(BaseModel):
    """家人绑定请求"""
    elderly_user_id: int = Field(..., description="老年用户ID")
    relationship: str = Field(..., description="关系: son/daughter/spouse/grandson/granddaughter/other")


class FamilyMemberResponse(BaseModel):
    """家庭成员响应"""
    id: int
    nickname: Optional[str]
    avatar_url: Optional[str]
    relationship: str
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ElderlyInfoResponse(BaseModel):
    """老人信息（供子女查看）"""
    id: int
    nickname: Optional[str]
    avatar_url: Optional[str]
    age: Optional[int]
    emergency_contact: Optional[str]
    emergency_contact_name: Optional[str]
    today_taken_count: int = 0
    today_total_count: int = 0
    today_adherence_rate: float = 0.0

    class Config:
        from_attributes = True
