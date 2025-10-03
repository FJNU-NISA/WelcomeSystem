"""
认证相关路由
包含登录、设置密码等功能
"""
import hashlib
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Response
from fastapi.responses import RedirectResponse, JSONResponse
import json
from pydantic import BaseModel

from Core.User.User import User
from Core.User.Session import session_manager
from api.dependencies import get_current_user_optional, require_auth
from Core.Common.Config import Config

logger = logging.getLogger(__name__)
router = APIRouter()

# 实例化用户管理器和配置
user_manager = User()
config = Config()

# 请求模型
class LoginRequest(BaseModel):
    stuId: str
    password: str

class SetPasswordRequest(BaseModel):
    newPassword: str

class RegisterRequest(BaseModel):
    stuId: str
    password: str
    name: str = None
    email: str = None
    phone: str = None

def hash_password(password: str, salt: str = None) -> str:
    """密码加盐哈希"""
    if salt is None:
        try:
            salt = config.get_value('System', 'salt')
        except:
            salt = "nisa_salt_2025"  # 默认盐值
    return hashlib.sha256((password + salt).encode()).hexdigest()

@router.post("/api/register")
async def api_register(register_data: RegisterRequest):
    """用户注册API"""
    try:
        # 检查学号是否已存在
        logger.info(f"🔐 开始注册新用户: {register_data.stuId}")
        existing_user = await user_manager.get_user_by_field("stuId", register_data.stuId)
        if existing_user:
            logger.warning(f"❌ 用户已存在: {register_data.stuId}")
            raise HTTPException(status_code=400, detail="该学号已被注册")
        
        # 验证密码长度
        if len(register_data.password) < 6:
            raise HTTPException(status_code=400, detail="密码长度至少为6位")
        
        # 验证密码不能和学号相同
        if register_data.password == register_data.stuId:
            raise HTTPException(status_code=400, detail="密码不能与学号相同")
        
        # 加密密码
        hashed_password = hash_password(register_data.password)
        
        # 构建用户数据
        user_data = {
            "stuId": register_data.stuId,
            "password": hashed_password,
            "role": "user",  # 默认角色为普通用户
            "points": 0,     # 初始积分为0
            "levelProgress": {}  # 初始关卡进度为空
        }
        
        # 添加可选字段
        if register_data.name:
            user_data["name"] = register_data.name
        else:
            user_data["name"] = f"用户{register_data.stuId}"  # 如果没有提供姓名，使用学号作为默认姓名
            
        if register_data.email:
            user_data["email"] = register_data.email
        if register_data.phone:
            user_data["phone"] = register_data.phone
        
        # 创建用户
        user_id = await user_manager.create_user(user_data)
        
        if not user_id:
            logger.error("❌ 用户创建失败")
            raise HTTPException(status_code=500, detail="注册失败，请稍后重试")
        
        logger.info(f"✅ 用户注册成功: {register_data.stuId}, ID: {user_id}")
        
        return {
            "message": "注册成功",
            "userId": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册错误: {e}")
        raise HTTPException(status_code=500, detail="注册失败")

@router.post("/api/login")
async def api_login(login_data: LoginRequest):
    """用户登录API"""
    try:
        # 验证用户凭据
        logger.info(f"🔐 开始验证用户: {login_data.stuId}")
        user_info = await verify_user_credentials(login_data.stuId, login_data.password)
        if not user_info:
            logger.warning(f"❌ 用户验证失败: {login_data.stuId}")
            raise HTTPException(status_code=401, detail="学号或密码错误")
        
        logger.info(f"✅ 用户验证成功: {user_info['stuId']}, 角色: {user_info.get('role', 'user')}")
        
        # 检查是否使用默认密码（密码和学号相同）
        is_default_password = login_data.password == login_data.stuId
        logger.info(f"🔍 默认密码检查: {'是' if is_default_password else '否'}")
        
        # 创建会话
        logger.info(f"🔄 开始创建会话...")
        session_token = await session_manager.create_session(user_info)
        
        if not session_token:
            logger.error("❌ 会话创建失败，返回空token")
            raise HTTPException(status_code=500, detail="会话创建失败")
            
        logger.info(f"✅ 会话创建成功: {session_token[:10]}... (用户: {user_info['stuId']})")
        
        # 创建响应数据
        response_data = {
            "message": "登录成功",
            "user": {
                "stuId": user_info["stuId"],
                "role": user_info["role"]
            },
            "requirePasswordChange": is_default_password  # 添加标识是否需要修改密码
        }
        
        # 使用FastAPI标准方式设置Cookie
        response = JSONResponse(content=response_data)
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=604800,  # 7天 (7 * 24 * 60 * 60)
            path="/",
            httponly=False,  # 允许JavaScript访问Cookie（暂时用于调试）
            samesite="lax",
            secure=False  # 本地开发环境设为False，生产环境应设为True
        )
        
        logger.info(f"🍪 设置Cookie成功: session_token={session_token[:10]}...")
        
        return response
        
    except Exception as e:
        logger.error(f"登录错误: {e}")
        raise HTTPException(status_code=500, detail="登录失败")

@router.get("/api/user-stats")
async def get_user_stats():
    """获取用户统计信息（无需认证）"""
    try:
        collection = await user_manager.get_collection()
        total_users = await collection.count_documents({})
        
        return {
            "totalUsers": total_users,
            "message": "统计信息获取成功"
        }
    except Exception as e:
        logger.error(f"获取用户统计信息错误: {e}")
        # 即使出错也返回一个默认值，避免前端显示错误
        return {
            "totalUsers": 0,
            "message": "统计信息获取失败"
        }

@router.get("/api/current-user")
async def get_current_user(current_user: dict = Depends(require_auth)):
    """获取当前登录用户信息"""
    try:
        return {
            "user": {
                "stuId": current_user["stuId"],
                "role": current_user["role"],
                "name": current_user.get("name", "")
            }
        }
    except Exception as e:
        logger.error(f"获取当前用户信息错误: {e}")
        raise HTTPException(status_code=500, detail="获取用户信息失败")

@router.post("/api/set-password")
async def api_set_password(request: SetPasswordRequest, current_user: dict = Depends(require_auth)):
    """设置/修改密码"""
    try:
        # 从session中获取当前用户信息，确保安全性
        stu_id = current_user["stuId"]
        
        # 验证旧密码（检查是否为默认密码）
        old_password_hash = hash_password(stu_id)  # 默认密码是学号
        user_info = await verify_user_credentials(stu_id, stu_id)
        if not user_info:
            raise HTTPException(status_code=401, detail="身份验证失败")
        
        # 检查新密码不能是学号（默认密码）
        if request.newPassword == stu_id:
            raise HTTPException(status_code=400, detail="新密码不能与学号相同，请设置更安全的密码")
        
        # 检查新密码长度
        if len(request.newPassword) < 6:
            raise HTTPException(status_code=400, detail="新密码长度至少为6位")
        
        # 更新密码
        new_password_hash = hash_password(request.newPassword)
        collection = await user_manager.get_collection()
        result = await collection.update_one(
            {"stuId": stu_id},
            {"$set": {"password": new_password_hash}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return {"message": "密码设置成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置密码错误: {e}")
        raise HTTPException(status_code=500, detail="设置密码失败")

@router.post("/api/logout")
async def api_logout(request: Request, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """用户登出"""
    try:
        session_token = request.cookies.get("session_token")
        if session_token:
            await session_manager.delete_session(session_token)
        
        response = JSONResponse(content={"message": "登出成功"})
        response.delete_cookie("session_token")
        return response
        
    except Exception as e:
        logger.error(f"登出错误: {e}")
        return JSONResponse(content={"message": "登出完成"})

async def verify_user_credentials(stu_id: str, password: str) -> Optional[dict]:
    """验证用户凭据"""
    try:
        # 获取用户信息
        collection = await user_manager.get_collection()
        user = await collection.find_one({"stuId": stu_id})
        if not user:
            return None
        
        # 验证密码
        stored_password = user.get("password", "")
        input_password_hash = hash_password(password)
        
        # 如果密码为空或者哈希匹配，则验证成功
        if not stored_password or stored_password == input_password_hash:
            return {
                "stuId": user["stuId"],
                "role": user.get("role", "user"),
                "points": user.get("points", 0)
            }
        
        return None
        
    except Exception as e:
        logger.error(f"验证用户凭据错误: {e}")
        return None