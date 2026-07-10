"""
用户相关 API 路由
"""
import sqlite3
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_db
from app.schemas.user import (
    UserLoginRequest, UserUpdateRequest, UserResponse, LoginResponse,
    FamilyBindRequest, FamilyMemberResponse, ElderlyInfoResponse,
)
from app.services.user_service import UserService
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.post("/login", response_model=LoginResponse, summary="微信登录")
async def login(request: UserLoginRequest, conn: sqlite3.Connection = Depends(get_db)):
    """微信小程序登录：通过临时 code 换取 openid，返回 JWT token"""
    try:
        result = await UserService.login(conn, request.code)
        return LoginResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            user=UserResponse(**result["user"]),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profile", response_model=UserResponse, summary="获取个人信息")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户的个人信息"""
    return UserResponse(**current_user)


@router.put("/profile", response_model=UserResponse, summary="更新个人信息")
async def update_profile(
    request: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """更新用户个人信息（昵称、手机号、紧急联系人等）"""
    user = UserService.update_profile(conn, current_user, request.model_dump())
    return UserResponse(**user)


@router.post("/family/bind", summary="绑定家人")
async def bind_family(
    request: FamilyBindRequest,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """子女绑定老人用户，以便查看老人用药情况"""
    try:
        binding = UserService.bind_family(
            conn, current_user["id"], request.elderly_user_id, request.relationship
        )
        return {"message": "绑定成功", "binding_id": binding["id"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/family/members", response_model=list[FamilyMemberResponse], summary="获取家人列表")
async def get_family_members(
    elderly_user_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """获取某位老人的所有绑定家人"""
    members = UserService.get_family_members(conn, elderly_user_id)
    return [FamilyMemberResponse(**m) for m in members]


@router.get("/family/elderly", response_model=list[ElderlyInfoResponse], summary="获取绑定的老人列表")
async def get_binded_elderly(
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """子女获取自己绑定的所有老人列表及用药概览"""
    elderly_list = UserService.get_binded_elderly(conn, current_user["id"])
    return [ElderlyInfoResponse(**e) for e in elderly_list]


@router.get("/family/elderly/{elderly_id}", response_model=ElderlyInfoResponse, summary="查看老人用药详情")
async def get_elderly_info(
    elderly_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    """子女查看指定老人的用药详情"""
    try:
        info = UserService.get_elderly_info(conn, elderly_id, current_user["id"])
        return ElderlyInfoResponse(**info)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
