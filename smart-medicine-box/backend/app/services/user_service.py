"""
用户服务 - 处理用户相关的业务逻辑
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import User, FamilyBinding, MedicineRecord
from app.models.medicine import RecordStatus, Relationship
from app.schemas.user import (
    UserUpdateRequest, FamilyBindRequest,
    FamilyMemberResponse, ElderlyInfoResponse
)
from app.utils.auth import wechat_login, create_access_token


class UserService:
    """用户服务"""

    @staticmethod
    async def login(db: Session, code: str):
        """微信小程序登录"""
        # 通过微信 code 获取 openid
        wx_data = await wechat_login(code)
        openid = wx_data["openid"]
        unionid = wx_data.get("unionid")

        # 查找或创建用户
        user = db.query(User).filter(User.openid == openid).first()
        if user is None:
            user = User(
                openid=openid,
                unionid=unionid,
                is_elderly=True,
            )
            db.add(user)
            db.flush()

        # 更新登录时间
        user.last_login_at = datetime.utcnow()
        if unionid and not user.unionid:
            user.unionid = unionid
        db.commit()
        db.refresh(user)

        # 生成 JWT token
        access_token = create_access_token(data={"sub": str(user.id)})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user,
        }

    @staticmethod
    def get_profile(user: User) -> User:
        """获取用户个人信息"""
        return user

    @staticmethod
    def update_profile(db: Session, user: User, data: UserUpdateRequest) -> User:
        """更新用户个人信息"""
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def bind_family(
        db: Session,
        family_user: User,
        data: FamilyBindRequest,
    ) -> FamilyBinding:
        """家人绑定老人"""
        # 检查老人用户是否存在
        elderly_user = db.query(User).filter(
            User.id == data.elderly_user_id,
            User.is_active == True,
        ).first()
        if not elderly_user:
            raise ValueError("未找到该用户")

        # 检查是否已绑定
        existing = db.query(FamilyBinding).filter(
            FamilyBinding.elderly_user_id == data.elderly_user_id,
            FamilyBinding.family_user_id == family_user.id,
        ).first()
        if existing:
            raise ValueError("已经绑定过该用户")

        binding = FamilyBinding(
            elderly_user_id=data.elderly_user_id,
            family_user_id=family_user.id,
            relationship=Relationship(data.relationship),
        )
        db.add(binding)
        db.commit()
        db.refresh(binding)
        return binding

    @staticmethod
    def get_family_members(db: Session, elderly_user_id: int) -> List[FamilyMemberResponse]:
        """获取老人的家人列表"""
        bindings = db.query(FamilyBinding).filter(
            FamilyBinding.elderly_user_id == elderly_user_id,
        ).all()
        return [
            FamilyMemberResponse(
                id=b.id,
                nickname=b.family_user.nickname if hasattr(b, 'family_user') else None,
                avatar_url=b.family_user.avatar_url if hasattr(b, 'family_user') else None,
                relationship=b.relationship.value if hasattr(b.relationship, 'value') else b.relationship,
                is_primary=b.is_primary,
                created_at=b.created_at,
            )
            for b in bindings
        ]

    @staticmethod
    def get_elderly_info(db: Session, elderly_user_id: int, family_user_id: int) -> ElderlyInfoResponse:
        """获取老人用药概览（供子女查看）"""
        # 验证绑定关系
        binding = db.query(FamilyBinding).filter(
            FamilyBinding.elderly_user_id == elderly_user_id,
            FamilyBinding.family_user_id == family_user_id,
        ).first()
        if not binding:
            raise ValueError("无权限查看该用户信息")

        user = db.query(User).filter(User.id == elderly_user_id).first()
        if not user:
            raise ValueError("用户不存在")

        # 获取今日用药统计
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        records = db.query(MedicineRecord).filter(
            MedicineRecord.user_id == elderly_user_id,
            MedicineRecord.scheduled_time >= today_start,
            MedicineRecord.scheduled_time <= today_end,
        ).all()

        total = len(records)
        taken = sum(1 for r in records if r.status == RecordStatus.TAKEN)
        rate = (taken / total * 100) if total > 0 else 0.0

        return ElderlyInfoResponse(
            id=user.id,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            age=user.age,
            emergency_contact=user.emergency_contact,
            emergency_contact_name=user.emergency_contact_name,
            today_taken_count=taken,
            today_total_count=total,
            today_adherence_rate=round(rate, 1),
        )

    @staticmethod
    def get_binded_elderly(db: Session, family_user_id: int) -> List[ElderlyInfoResponse]:
        """获取家人绑定的所有老人"""
        bindings = db.query(FamilyBinding).filter(
            FamilyBinding.family_user_id == family_user_id,
        ).all()

        result = []
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        for b in bindings:
            user = db.query(User).filter(User.id == b.elderly_user_id).first()
            if not user:
                continue

            records = db.query(MedicineRecord).filter(
                MedicineRecord.user_id == user.id,
                MedicineRecord.scheduled_time >= today_start,
                MedicineRecord.scheduled_time <= today_end,
            ).all()

            total = len(records)
            taken = sum(1 for r in records if r.status == RecordStatus.TAKEN)
            rate = (taken / total * 100) if total > 0 else 0.0

            result.append(ElderlyInfoResponse(
                id=user.id,
                nickname=user.nickname,
                avatar_url=user.avatar_url,
                age=user.age,
                emergency_contact=user.emergency_contact,
                emergency_contact_name=user.emergency_contact_name,
                today_taken_count=taken,
                today_total_count=total,
                today_adherence_rate=round(rate, 1),
            ))

        return result
