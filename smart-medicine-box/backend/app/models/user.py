"""
用户模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """用户表 - 存储小程序用户信息"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    openid = Column(String(64), unique=True, nullable=False, index=True, comment="微信OpenID")
    unionid = Column(String(64), nullable=True, comment="微信UnionID")
    nickname = Column(String(64), nullable=True, comment="昵称")
    avatar_url = Column(String(512), nullable=True, comment="头像URL")
    phone = Column(String(20), nullable=True, comment="手机号")
    age = Column(Integer, nullable=True, comment="年龄")
    gender = Column(Integer, nullable=True, comment="性别: 0-未知, 1-男, 2-女")
    emergency_contact = Column(String(20), nullable=True, comment="紧急联系人电话")
    emergency_contact_name = Column(String(32), nullable=True, comment="紧急联系人姓名")
    is_elderly = Column(Boolean, default=True, comment="是否为老年用户")
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    remark = Column(Text, nullable=True, comment="备注（如过敏信息、基础疾病等）")

    def __repr__(self):
        return f"<User(id={self.id}, nickname={self.nickname})>"
