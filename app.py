"""
NISA Welcome System 主应用文件
简化版 - 使用模块化架构
"""
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional
import os

from fastapi import FastAPI, Request, HTTPException, Depends, Cookie, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from pydantic import BaseModel
from bson import ObjectId

from config import create_app, setup_routes, get_managers
from api.dependencies import require_auth, get_current_user_optional, require_super_admin, require_auth_redirect, require_super_admin_redirect, require_admin_redirect, require_admin
from Core.Common.Config import Config
from Core.User.Session import session_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建应用
app = create_app()
managers = get_managers()

# 读取配置
config = Config()

# 请求模型
class PointsRequest(BaseModel):
    stuId: str
    points: int
    reason: str

class LevelPointsRequest(BaseModel):
    stuId: str
    levelId: str

# 工具函数
def hash_password(password: str, salt: str = None) -> str:
    """密码加盐哈希"""
    if salt is None:
        try:
            salt = config.get_value('System', 'salt')
        except:
            salt = "nisa_salt_2025"  # 默认盐值
    return hashlib.sha256((password + salt).encode()).hexdigest()

def get_user_permissions(user_role: str, user_info: dict) -> dict:
    """
    获取用户的具体权限信息
    
    Args:
        user_role: 用户角色
        user_info: 用户信息字典
    
    Returns:
        dict: 用户权限信息
    """
    permissions = {
        "pages": [],
        "features": {}
    }
    
    # 基础页面权限
    if user_role == "user":
        # 普通成员: 个人信息 + 抽奖 + 关卡查看
        permissions["pages"] = ["info", "lottery", "levelintroduction", "login", "setpassword"]
        permissions["features"] = {
            "canLottery": True,
            "canModifyPoints": False,
            "canViewMembers": False,
            "canManageMembers": False,
            "canManageLevels": False,
            "canManagePrizes": False
        }
    elif user_role == "admin":
        # 管理员: 个人信息 + 分发积分
        permissions["pages"] = ["info", "modifypoints", "login", "setpassword"]
        permissions["features"] = {
            "canLottery": False,
            "canModifyPoints": True,
            "canViewMembers": False,
            "canManageMembers": False,
            "canManageLevels": False,
            "canManagePrizes": False
        }
            
    elif user_role == "super_admin":
        # 超级管理员: 个人信息 + 分发积分 + 成员管理 + 关卡管理 + 奖品管理
        permissions["pages"] = ["info", "modifypoints", "membermanagement", "levelmanagement", 
                               "prizemanagement", "login", "setpassword"]
        permissions["features"] = {
            "canLottery": False,
            "canModifyPoints": True,
            "canViewMembers": True,
            "canManageMembers": True,
            "canManageLevels": True,
            "canManagePrizes": True
        }
    
    return permissions

# ========== 前端页面路由 ==========

@app.get("/favicon.ico")
async def favicon():
    """Favicon - 返回空响应避免404"""
    from fastapi.responses import Response
    return Response(content="", media_type="image/x-icon")

@app.get("/", response_class=HTMLResponse)
async def root():
    """根路径重定向到登录页面"""
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """登录页面"""
    try:
        with open("Pages/Login/html/login.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="登录页面不存在")

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    """注册页面"""
    try:
        with open("Pages/Login/html/register.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="注册页面不存在")

@app.get("/login/redirect", response_class=HTMLResponse)
async def login_page_redirect():
    """登录页面重定向"""
    return RedirectResponse(url="/login")

@app.get("/setpassword", response_class=HTMLResponse)
async def set_password_page(request: Request):
    """设置密码页面"""
    # 检查认证，未登录自动重定向到登录页面
    auth_result = await require_auth_redirect(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    
    try:
        with open("Pages/Login/html/setpassword.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="设置密码页面不存在")

@app.get("/info", response_class=HTMLResponse)
async def info_page(request: Request):
    """个人信息页面"""
    # 检查认证，未登录自动重定向到登录页面
    auth_result = await require_auth_redirect(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    
    try:
        with open("Pages/Info/html/info.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="信息页面不存在")

@app.get("/lottery", response_class=HTMLResponse)
async def lottery_page(request: Request):
    """抽奖页面"""
    # 检查认证，未登录自动重定向到登录页面
    auth_result = await require_auth_redirect(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    
    try:
        with open("Pages/Lottery/html/lottery.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="抽奖页面不存在")

@app.get("/levelintroduction", response_class=HTMLResponse)
async def level_introduction_page(request: Request):
    """关卡介绍页面（所有用户可访问）"""
    # 检查认证，未登录自动重定向到登录页面
    auth_result = await require_auth_redirect(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    
    try:
        with open("Pages/LevelIntroduction/html/levelintroduction.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="关卡介绍页面不存在")

@app.get("/modifypoints", response_class=HTMLResponse)
async def modify_points_page(request: Request):
    """积分管理页面"""
    # 检查管理员权限（管理员或超级管理员），未登录或权限不足时重定向
    auth_result = await require_admin_redirect(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    
    try:
        with open("Pages/ModifyPoint/html/modifypoints.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="积分管理页面不存在")

# 管理员页面
@app.get("/admin/membermanagement", response_class=HTMLResponse)
async def member_management_page(request: Request):
    """成员管理页面"""
    # 检查管理员权限，未登录或权限不足时重定向
    auth_result = await require_super_admin_redirect(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    
    try:
        with open("Pages/MemberManagement/html/membermanagement.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="成员管理页面不存在")

@app.get("/admin/levelmanagement", response_class=HTMLResponse)
async def level_management_page(request: Request):
    """关卡管理页面"""
    # 检查管理员权限，未登录或权限不足时重定向
    auth_result = await require_super_admin_redirect(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    
    try:
        with open("Pages/LevelManagement/html/levelmanagement.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="关卡管理页面不存在")

@app.get("/admin/prizemanagement", response_class=HTMLResponse)
async def prize_management_page(request: Request):
    """奖品管理页面"""
    # 检查管理员权限，未登录或权限不足时重定向
    auth_result = await require_super_admin_redirect(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    
    try:
        with open("Pages/PrizeManagement/html/prizemanagement.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="奖品管理页面不存在")

@app.get("/admin/giftredemption", response_class=HTMLResponse)
async def gift_redemption_page(request: Request):
    """奖品核销页面"""
    # 检查管理员权限，未登录或权限不足时重定向
    auth_result = await require_super_admin_redirect(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    
    try:
        with open("Pages/Admin/html/giftredemption.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="奖品核销页面不存在")

# ========== 基础API接口 ==========

@app.get("/api/create-default-admin")
async def create_default_admin():
    """创建默认管理员账户"""
    try:
        user_manager = managers["user_manager"]
        collection = await user_manager.get_collection()
        
        # 从配置文件读取默认管理员信息
        try:
            default_stu_id = config.get_value('DefaultAdmin', 'stuId')
            default_password = config.get_value('DefaultAdmin', 'password')
            default_role = config.get_value('DefaultAdmin', 'role')
        except Exception as config_error:
            # 如果配置读取失败，使用默认值
            logger.warning(f"读取默认管理员配置失败，使用默认值: {config_error}")
            default_stu_id = "admin"
            default_password = "admin123"
            default_role = "admin"
        
        # 检查是否已存在管理员账户
        admin_exists = await collection.find_one({"stuId": default_stu_id})
        
        # 准备管理员数据
        admin_data = {
            "stuId": default_stu_id,
            "creatTime": admin_exists.get("creatTime") if admin_exists else datetime.now(),
            "points": admin_exists.get("points", 0) if admin_exists else 0,
            "completedLevels": admin_exists.get("completedLevels", []) if admin_exists else [],
            "role": default_role,
            "password": hash_password(default_password)
        }
        
        if admin_exists:
            # 更新现有管理员
            logger.info(f"正在更新管理员: {default_stu_id}")
            logger.debug(f"更新数据: {admin_data}")
            
            result = await collection.update_one(
                {"stuId": default_stu_id},
                {"$set": admin_data}
            )
            
            logger.info(f"更新结果 - matched: {result.matched_count}, modified: {result.modified_count}")
            
            if result.matched_count > 0:
                return {
                    "message": "默认管理员账户更新成功", 
                    "stuId": default_stu_id,
                    "password": default_password,
                    "role": default_role,
                    "notice": "请尽快修改默认密码",
                    "action": "更新",
                    "matched": result.matched_count,
                    "modified": result.modified_count
                }
            else:
                raise HTTPException(status_code=500, detail="管理员更新失败，未找到匹配的用户")
        else:
            # 创建新管理员
            result = await collection.insert_one(admin_data)
            if result.inserted_id:
                return {
                    "message": "默认管理员账户创建成功", 
                    "stuId": default_stu_id,
                    "password": default_password,
                    "role": default_role,
                    "notice": "请尽快修改默认密码",
                    "action": "创建"
                }
            else:
                raise HTTPException(status_code=500, detail="管理员创建失败")
            
    except Exception as e:
        logger.error(f"创建默认管理员错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/reset-password")
async def reset_admin_password(stuId: str = "admin"):
    """重置指定管理员密码"""
    try:
        user_manager = managers["user_manager"]
        collection = await user_manager.get_collection()
        
        # 从配置文件读取默认密码
        try:
            default_password = config.get_value('DefaultAdmin', 'password')
        except Exception:
            default_password = "admin123"
        
        # 查找指定的管理员
        admin_exists = await collection.find_one({"stuId": stuId})
        if not admin_exists:
            raise HTTPException(status_code=404, detail=f"管理员 {stuId} 不存在")
        
        # 重置密码
        result = await collection.update_one(
            {"stuId": stuId},
            {"$set": {"password": hash_password(default_password)}}
        )
        
        if result.modified_count > 0:
            return {
                "message": f"管理员 {stuId} 密码重置成功",
                "stuId": stuId,
                "password": default_password,
                "notice": "请尽快登录并修改密码"
            }
        else:
            raise HTTPException(status_code=500, detail="密码重置失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置管理员密码错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/permissions")
async def update_admin_permissions(request: dict, current_user: dict = Depends(require_super_admin)):
    """更新管理员权限"""
    try:
        stu_id = request.get("stuId")
        permissions = request.get("permissions", {})
        
        if not stu_id:
            raise HTTPException(status_code=400, detail="学号不能为空")
        
        user_manager = managers["user_manager"]
        collection = await user_manager.get_collection()
        
        # 检查目标用户是否存在且为管理员
        target_user = await collection.find_one({"stuId": stu_id})
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        if target_user.get("role") not in ["admin", "super_admin"]:
            raise HTTPException(status_code=400, detail="只能设置管理员的权限")
        
        # 更新权限
        result = await collection.update_one(
            {"stuId": stu_id},
            {"$set": {"adminPermissions": permissions}}
        )
        
        if result.modified_count > 0:
            return {"message": "权限更新成功", "stuId": stu_id, "permissions": permissions}
        else:
            raise HTTPException(status_code=500, detail="权限更新失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新管理员权限错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/list")
async def list_admins():
    """查看所有管理员账户"""
    try:
        user_manager = managers["user_manager"]
        collection = await user_manager.get_collection()
        
        # 查找所有管理员用户
        admins = await collection.find({
            "role": {"$in": ["admin", "super_admin"]}
        }).to_list(None)
        
        # 清理敏感信息
        admin_list = []
        for admin in admins:
            admin_info = {
                "_id": str(admin["_id"]),
                "stuId": admin.get("stuId"),
                "role": admin.get("role"),
                "points": admin.get("points", 0),
                "completedLevels": admin.get("completedLevels", []),
                "creatTime": admin.get("creatTime"),
                "gift": admin.get("gift", "")
            }
            admin_list.append(admin_info)
        
        return {
            "message": "管理员列表获取成功",
            "total": len(admin_list),
            "admins": admin_list
        }
        
    except Exception as e:
        logger.error(f"获取管理员列表错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/info")
async def get_user_info(stuId: Optional[str] = None, current_user: dict = Depends(require_auth)):
    """获取用户信息，支持查询其他用户信息"""
    try:
        collection = await managers["user_manager"].get_collection()
        
        # 如果没有指定stuId，查询自己的信息
        if not stuId:
            target_stu_id = current_user["stuId"]
        else:
            # 如果指定了stuId，需要检查权限
            target_stu_id = stuId
            
            # 普通用户只能查询自己的信息
            if current_user["role"] == "user" and stuId != current_user["stuId"]:
                raise HTTPException(status_code=403, detail="权限不足，只能查询自己的信息")
            
            # 管理员和超级管理员可以查询所有人的信息
            if current_user["role"] not in ["admin", "super_admin"]:
                if stuId != current_user["stuId"]:
                    raise HTTPException(status_code=403, detail="权限不足，只能查询自己的信息")
        
        user_info = await collection.find_one({"stuId": target_stu_id})
        if user_info:
            user_info["_id"] = str(user_info["_id"])
            user_info.pop("password", None)  # 不返回密码
            
            # 添加用户权限信息
            user_role = user_info.get("role", "user")
            user_info["permissions"] = get_user_permissions(user_role, user_info)
            
            return user_info
        else:
            raise HTTPException(status_code=404, detail="用户不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")

@app.get("/api/user/status")
async def get_user_status(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """检查用户登录状态，不强制要求登录"""
    logger.info(f"🔍 检查用户状态: current_user={current_user}")
    
    if current_user:
        logger.info(f"✅ 用户已认证: {current_user.get('stuId')} ({current_user.get('role')})")
        return {"success": True, "logged_in": True, "user": current_user}
    else:
        logger.info("❌ 用户未认证或会话无效")
        return {"success": True, "logged_in": False, "user": None}

@app.post("/api/levels/details")
async def get_levels_details(request: dict, current_user: dict = Depends(require_auth)):
    """获取关卡详细信息"""
    try:
        level_ids = request.get("levelIds", [])
        if not level_ids:
            return []
        
        # 获取关卡信息
        collection = await managers["level_manager"].get_collection()
        levels = []
        
        for level_id in level_ids:
            # 尝试通过ID查找关卡
            try:
                level = await collection.find_one({"_id": ObjectId(level_id)})
            except:
                # 如果ID无效，尝试通过名称查找
                level = await collection.find_one({"name": level_id})
            
            if level:
                level["_id"] = str(level["_id"])
                levels.append(level)
            else:
                # 如果找不到关卡，创建一个默认的关卡信息
                levels.append({
                    "_id": str(level_id),
                    "name": f"关卡 {len(levels) + 1}",
                    "description": "关卡描述"
                })
        
        return levels
    except Exception as e:
        logger.error(f"获取关卡详情失败: {e}")
        # 返回默认的关卡信息
        level_ids = request.get("levelIds", [])
        return [{"_id": str(lid), "name": f"关卡 {i+1}", "description": "关卡描述"} 
                for i, lid in enumerate(level_ids)]

@app.get("/api/levels/all")
async def get_all_levels(current_user: dict = Depends(require_admin)):
    """获取所有关卡信息（管理员权限）"""
    try:
        collection = await managers["level_manager"].get_collection()
        levels = []
        
        async for level in collection.find({}):
            level["_id"] = str(level["_id"])
            levels.append(level)
        
        return {"success": True, "levels": levels}
    except Exception as e:
        logger.error(f"获取所有关卡失败: {e}")
        return {"success": False, "message": f"获取关卡失败: {str(e)}"}

@app.get("/api/levels/active")
async def get_active_levels(current_user: dict = Depends(require_admin)):
    """获取已激活的关卡信息（用于积分分发）"""
    try:
        collection = await managers["level_manager"].get_collection()
        levels = []
        
        # 只获取激活状态的关卡
        async for level in collection.find({"isActive": True}):
            level["_id"] = str(level["_id"])
            levels.append(level)
        
        return {"success": True, "levels": levels}
    except Exception as e:
        logger.error(f"获取激活关卡失败: {e}")
        return {"success": False, "message": f"获取激活关卡失败: {str(e)}"}

@app.get("/api/levels/public")
async def get_public_levels(current_user: dict = Depends(require_auth)):
    """获取所有关卡信息（所有已登录用户可访问，用于关卡介绍页面）"""
    try:
        collection = await managers["level_manager"].get_collection()
        levels = []
        
        # 获取所有关卡，按创建时间排序
        async for level in collection.find({}).sort("createdAt", 1):
            level["_id"] = str(level["_id"])
            # 只返回必要的信息
            public_level = {
                "_id": level["_id"],
                "name": level.get("name", "未命名关卡"),
                "info": level.get("info", ""),
                "description": level.get("description", ""),  # 兼容旧字段
                "points": level.get("points", 0),
                "isActive": level.get("isActive", True)
            }
            levels.append(public_level)
        
        return {"success": True, "levels": levels}
    except Exception as e:
        logger.error(f"获取关卡列表失败: {e}")
        return {"success": False, "message": f"获取关卡列表失败: {str(e)}"}

@app.get("/api/user/prizes/{stu_id}")
async def get_user_prizes(stu_id: str, current_user: dict = Depends(require_auth)):
    """获取用户的奖品列表"""
    try:
        # 权限检查：普通用户只能查看自己的奖品，管理员可以查看所有人的奖品
        if current_user["role"] == "user" and stu_id != current_user["stuId"]:
            raise HTTPException(status_code=403, detail="权限不足，只能查询自己的奖品")
        
        # 获取用户信息
        user_collection = await managers["user_manager"].get_collection()
        user = await user_collection.find_one({"stuId": stu_id})
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 从用户数据结构中获取奖品列表
        prizes = user.get("prizes", [])
        
        # 格式化时间并添加索引
        for index, prize in enumerate(prizes):
            prize["index"] = index  # 添加数组索引用于更新
            if "drawTime" in prize:
                prize["formatted_draw_time"] = prize["drawTime"].strftime("%Y-%m-%d %H:%M:%S")
            if "redeemedAt" in prize and prize["redeemedAt"]:
                prize["formatted_redeemed_time"] = prize["redeemedAt"].strftime("%Y-%m-%d %H:%M:%S")
        
        return {"success": True, "prizes": prizes}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户奖品失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户奖品失败: {str(e)}")

@app.post("/api/user/prizes/{stu_id}/redeem")
async def toggle_prize_redeem(
    stu_id: str,
    prize_index: int = Query(..., description="奖品在数组中的索引"),
    current_user: dict = Depends(require_auth)
):
    """切换奖品核销状态（管理员专用，支持双向切换）"""
    try:
        # 权限检查：只有管理员可以核销奖品
        from Core.User.Permission import Permission
        if not Permission.can_modify_points(current_user.get("role", "user")):
            raise HTTPException(status_code=403, detail="没有权限进行核销操作")
        
        # 获取用户信息
        user_collection = await managers["user_manager"].get_collection()
        user = await user_collection.find_one({"stuId": stu_id})
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        prizes = user.get("prizes", [])
        if prize_index < 0 or prize_index >= len(prizes):
            raise HTTPException(status_code=400, detail="奖品索引无效")
        
        target_prize = prizes[prize_index]
        current_redeemed = target_prize.get("redeemed", False)
        
        # 切换核销状态
        new_redeemed = not current_redeemed
        update_path_redeemed = f"prizes.{prize_index}.redeemed"
        update_path_by = f"prizes.{prize_index}.redeemedBy"
        update_path_at = f"prizes.{prize_index}.redeemedAt"
        
        update_data = {
            update_path_redeemed: new_redeemed
        }
        
        if new_redeemed:
            # 核销
            update_data[update_path_by] = current_user["stuId"]
            update_data[update_path_at] = datetime.now()
        else:
            # 取消核销
            update_data[update_path_by] = None
            update_data[update_path_at] = None
        
        # 更新数据库
        result = await user_collection.update_one(
            {"stuId": stu_id},
            {"$set": update_data}
        )
        
        # 同时更新奖品集合的redeemed_count统计
        prize_collection = await managers["prize_manager"].get_collection()
        prize_id_obj = ObjectId(target_prize["prizeId"])
        if new_redeemed:
            await prize_collection.update_one(
                {"_id": prize_id_obj},
                {"$inc": {"redeemed_count": 1}}
            )
        else:
            await prize_collection.update_one(
                {"_id": prize_id_obj},
                {"$inc": {"redeemed_count": -1}}
            )
        
        if result.modified_count > 0:
            action = "核销" if new_redeemed else "取消核销"
            return {
                "success": True,
                "message": f"{action}成功",
                "redeemed": new_redeemed
            }
        else:
            return {"success": False, "message": "更新失败"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换奖品核销状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")

@app.get("/api/user/qrcode/{stu_id}")
async def generate_user_qrcode(stu_id: str, current_user: dict = Depends(require_auth)):
    """生成用户身份二维码"""
    try:
        # 权限检查：只能生成自己的二维码，或管理员可以生成任何人的
        if current_user["stuId"] != stu_id:
            if current_user["role"] not in ["admin", "super_admin"]:
                raise HTTPException(status_code=403, detail="只能生成自己的二维码")
        
        # 从配置文件获取NFC URL
        nfc_base_url = config.get_value('NFC', 'URL')
        if not nfc_base_url.endswith('/'):
            nfc_base_url += '/'
        
        # 构造二维码内容：NFC URL + info?stuId=学号
        qrcode_content = f"{nfc_base_url}info?stuId={stu_id}"
        
        return {
            "success": True,
            "qrcode": qrcode_content,
            "stuId": stu_id,
            "message": "二维码生成成功"
        }
        
    except Exception as e:
        logger.error(f"生成二维码失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成二维码失败: {str(e)}")

@app.get("/api/lottery/prizes")
async def get_lottery_prizes():
    """获取可抽奖的奖品列表"""
    try:
        logger.info("开始获取奖品列表")
        
        # 检查managers是否初始化
        if "prize_manager" not in managers:
            logger.error("prize_manager未初始化")
            raise HTTPException(status_code=500, detail="奖品管理器未初始化")
        
        logger.info("获取奖品集合")
        collection = await managers["prize_manager"].get_collection()
        
        # 修正字段名：使用数据库中实际的字段名
        # 查询所有激活的奖品，不限制库存数量(包括库存为0的)
        logger.info("查询所有活跃的奖品数据")
        cursor = collection.find({"isActive": True})
        prizes = []
        
        logger.info("遍历奖品数据")
        async for prize in cursor:
            # 转换字段名以匹配前端期望的格式
            # 处理图片：如果数据库中有 photo 字段且文件存在则使用之，否则回退到 default.png
            photo_name = prize.get('photo') or 'default.png'
            photo_path = os.path.join('Assest', 'Prize', photo_name)
            if not photo_name or not os.path.exists(photo_path):
                photo_name = 'default.png'

            converted_prize = {
                "_id": str(prize["_id"]),
                "name": prize.get("Name", "未知奖品"),  # 数据库中是 Name
                "description": prize.get("description", ""),
                "image": f"/Assest/Prize/{photo_name}",
                "quantity": prize.get("total", 0),  # 数据库中是 total
                "stock": prize.get("total", 0),  # 为了兼容性也保留 stock
                "weight": prize.get("weight", 1),
                "isActive": prize.get("isActive", True)
            }
            prizes.append(converted_prize)
            
        logger.info(f"找到 {len(prizes)} 个符合条件的奖品")
        return {"success": True, "prizes": prizes}
    except Exception as e:
        logger.error(f"获取奖品列表失败: {str(e)}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取奖品列表失败: {str(e)}")

@app.get("/api/lottery/cost")
async def get_lottery_cost():
    """获取抽奖消耗积分"""
    try:
        # 从配置文件中获取抽奖消耗
        lottery_config = config.get_lottery_config()
        return {
            "success": True,
            "cost": lottery_config['points']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取抽奖配置失败: {str(e)}")

@app.post("/api/lottery/draw")
async def draw_lottery(current_user: dict = Depends(require_auth)):
    """执行抽奖"""
    import random
    from datetime import datetime, timedelta
    
    try:
        # 检查用户权限（只有普通会员可以抽奖）
        from Core.User.Permission import Permission
        if not Permission.can_lottery(current_user["role"]):
            raise HTTPException(status_code=403, detail="权限不足，只有普通会员可以抽奖")
        
        # 获取抽奖配置
        lottery_config = config.get_lottery_config()
        
        # 检查用户积分是否足够
        user_collection = await managers["user_manager"].get_collection()
        user = await user_collection.find_one({"stuId": current_user["stuId"]})
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        user_points = user.get("points", 0)
        lottery_cost = lottery_config['points']
        
        if user_points < lottery_cost:
            raise HTTPException(status_code=400, detail=f"积分不足，需要 {lottery_cost} 积分")
        
        # 获取可抽奖的奖品
        prize_collection = await managers["prize_manager"].get_collection()
        all_prizes = await prize_collection.find({"isActive": True}).to_list(None)
        
        if not all_prizes:
            raise HTTPException(status_code=400, detail="当前没有可抽奖的奖品")
        
        # 分离默认奖品（谢谢惠顾）和普通奖品
        default_prize = next((p for p in all_prizes if p.get("isDefault", False)), None)
        normal_prizes = [p for p in all_prizes if not p.get("isDefault", False)]
        
        # 过滤出有库存的普通奖品
        available_prizes = [p for p in normal_prizes if p.get("total", 0) > 0]
        
        # 如果没有可用的普通奖品，只能抽中默认奖品
        if not available_prizes:
            if default_prize:
                selected_prize = default_prize
            else:
                raise HTTPException(status_code=400, detail="所有奖品库存已空，且没有默认奖品")
        else:
            # 将默认奖品也加入抽奖池（如果存在）
            if default_prize:
                available_prizes.append(default_prize)
            
            # 在进行抽奖前校验权重总和：不允许总权重超过100
            # 这里的业务规则：权重字段表示百分比（0-100），整体不应超过100%
            total_weight = sum(float(prize.get("weight", 0) or 0) for prize in available_prizes)
            if total_weight > 100.0:
                # 记录错误并阻止抽奖
                logger.error(f"抽奖失败：奖品权重总和超过100%，当前总和={total_weight}")
                raise HTTPException(status_code=400, detail=f"奖品概率总和超过100%（{total_weight}），请调整奖品权重后重试。")

            # 基于权重的概率抽奖
            # 计算总权重（所有有库存的奖品 + 默认奖品）
            
            # 生成随机数
            rand_value = random.uniform(0, total_weight) if total_weight > 0 else 0
            
            # 根据权重选择奖品
            current_weight = 0
            selected_prize = None
            for prize in available_prizes:
                current_weight += prize.get("weight", 1)
                if rand_value <= current_weight:
                    selected_prize = prize
                    break
            
            # 如果没有选中（理论上不会发生），则选择第一个
            if selected_prize is None:
                selected_prize = available_prizes[0]
        
        # 检查选中的奖品是否是默认奖品
        is_default_prize = selected_prize.get("isDefault", False)
        
        # 创建奖品记录
        prize_id = str(selected_prize["_id"])
        prize_record = {
            "prizeId": prize_id,
            "prizeName": selected_prize.get("Name", selected_prize.get("name", "未知奖品")),
            "prizePhoto": selected_prize.get("photo", ""),
            "drawTime": datetime.now(),
            "redeemed": False,  # 核销状态
            "redeemedBy": None,
            "redeemedAt": None
        }
        
        # 创建积分消耗历史记录
        lottery_history_record = {
            "recordId": str(ObjectId()),
            "type": "lottery_draw",
            "pointsChange": -lottery_config['points'],  # 负数表示消耗
            "reason": f"抽奖消耗: 获得{selected_prize.get('Name', selected_prize.get('name', '未知奖品'))}",
            "prizeId": prize_id,
            "prizeName": selected_prize.get("Name", selected_prize.get("name", "未知奖品")),
            "operator": current_user.get("stuId", "system"),
            "timestamp": datetime.now(),
            "revoked": False,
            "revokedBy": None,
            "revokedAt": None
        }
        
        # 扣除用户积分并添加奖品记录和积分历史记录
        await user_collection.update_one(
            {"stuId": current_user["stuId"]},
            {
                "$inc": {"points": -lottery_config['points']},
                "$push": {
                    "prizes": prize_record,
                    "pointHistory": lottery_history_record
                }
            }
        )
        
        # 更新奖品库存（默认奖品不减库存）
        # 更新drawn_count统计
        if not is_default_prize:
            await prize_collection.update_one(
                {"_id": selected_prize["_id"]},
                {
                    "$inc": {
                        "total": -1,
                        "drawn_count": 1
                    }
                }
            )
        else:
            # 默认奖品只增加抽中次数统计
            await prize_collection.update_one(
                {"_id": selected_prize["_id"]},
                {"$inc": {"drawn_count": 1}}
            )
        
        return {
            "success": True,
            "prize": {
                "id": str(selected_prize["_id"]),
                "name": selected_prize.get("Name", selected_prize.get("name", "未知奖品")),
                "description": selected_prize.get("description", ""),
                "image": selected_prize.get("photo", selected_prize.get("image", "")),
                "rarity": selected_prize.get("rarity", "common")
            },
            "pointsUsed": lottery_config['points'],
            "remainingPoints": user_points - lottery_config['points'],
            "message": f"恭喜获得 {selected_prize.get('Name', selected_prize.get('name', '未知奖品'))}！"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"抽奖执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"抽奖执行失败: {str(e)}")

@app.get("/api/debug/session")
async def debug_session(request: Request, session_token: Optional[str] = Cookie(None)):
    """调试会话信息 - 用于导航栏获取用户信息和权限"""
    try:
        debug_info = {
            "cookie_received": session_token is not None,
            "cookie_value": session_token[:10] + "..." if session_token else None,
            "session_valid": False,
            "user_info": None
        }
        
        if session_token:
            user_info = await session_manager.get_user_by_session(session_token)
            
            if user_info:
                # 移除敏感信息
                user_info.pop("password", None)
                
                # 添加用户权限信息
                user_role = user_info.get("role", "user")
                user_info["permissions"] = get_user_permissions(user_role, user_info)
                
                debug_info["user_info"] = user_info
                debug_info["session_valid"] = True
        
        return debug_info
    except Exception as e:
        logger.error(f"获取会话信息失败: {e}")
        return {"error": str(e), "session_valid": False, "user_info": None}

@app.get("/api/system/status")
async def system_status(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """系统状态检查"""
    try:
        # 检查数据库连接
        user_collection = await managers["user_manager"].get_collection()
        await user_collection.find_one({})
        return {"status": "ok", "message": "系统运行正常"}
    except Exception as e:
        logger.error(f"系统状态检查失败: {e}")
        return {"status": "error", "message": "系统异常"}

@app.post("/api/points/modify")
async def modify_points(request: PointsRequest, current_user: dict = Depends(require_auth)):
    """修改用户积分"""
    try:
        # 验证权限 - 只有管理员可以修改积分
        from Core.User.Permission import Permission
        if not Permission.can_modify_points(current_user.get("role", "user")):
            raise HTTPException(status_code=403, detail="没有权限修改积分")
        
        # 创建操作历史记录
        history_record = {
            "recordId": str(ObjectId()),  # 生成唯一记录ID用于撤销
            "type": "manual_modify",
            "pointsChange": request.points,
            "reason": request.reason,
            "operator": current_user.get("stuId", "unknown"),
            "timestamp": datetime.now(),
            "revoked": False,  # 是否已撤销
            "revokedBy": None,
            "revokedAt": None
        }
        
        # 更新用户积分并添加历史记录
        user_collection = await managers["user_manager"].get_collection()
        result = await user_collection.update_one(
            {"stuId": request.stuId},
            {
                "$inc": {"points": request.points},
                "$push": {"pointHistory": history_record}
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return {
            "message": f"积分修改成功，{request.reason}",
            "recordId": history_record["recordId"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修改积分失败: {str(e)}")

@app.post("/api/points/level")
async def add_level_points(request: LevelPointsRequest, current_user: dict = Depends(require_auth)):
    """关卡积分发放"""
    try:
        # 验证权限
        from Core.User.Permission import Permission
        if not Permission.can_modify_points(current_user.get("role", "user")):
            raise HTTPException(status_code=403, detail="没有权限发放积分")
        
        # 获取关卡信息
        from bson import ObjectId
        level_collection = await managers["level_manager"].get_collection()
        level = await level_collection.find_one({"_id": ObjectId(request.levelId)})
        if not level:
            raise HTTPException(status_code=404, detail="关卡不存在")
        
        # 检查关卡是否激活
        if not level.get("isActive", True):
            raise HTTPException(status_code=400, detail="关卡未激活，无法发放积分")
        
        # 检查用户是否已完成该关卡
        user_collection = await managers["user_manager"].get_collection()
        user = await user_collection.find_one({"stuId": request.stuId})
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        if request.levelId in user.get("completedLevels", []):
            raise HTTPException(status_code=400, detail="用户已完成该关卡")
        
        # 创建操作历史记录
        history_record = {
            "recordId": str(ObjectId()),
            "type": "level_completion",
            "pointsChange": level["points"],
            "reason": f"完成关卡: {level['name']}",
            "levelId": request.levelId,
            "levelName": level["name"],
            "operator": current_user.get("stuId", "system"),
            "timestamp": datetime.now(),
            "revoked": False,
            "revokedBy": None,
            "revokedAt": None
        }
        
        # 添加积分、标记关卡完成并记录历史
        await user_collection.update_one(
            {"stuId": request.stuId},
            {
                "$inc": {"points": level["points"]},
                "$push": {
                    "completedLevels": request.levelId,
                    "pointHistory": history_record
                }
            }
        )
        
        return {
            "message": f"关卡完成，获得 {level['points']} 积分",
            "recordId": history_record["recordId"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"关卡积分发放失败: {str(e)}")

# ========== 操作历史接口 ==========

@app.get("/api/points/history/{stu_id}")
async def get_user_points_history(
    stu_id: str, 
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_auth)
):
    """获取用户的积分操作历史"""
    try:
        # 权限检查：普通用户只能查看自己的历史，管理员可以查看所有人的历史
        if current_user["role"] == "user" and stu_id != current_user["stuId"]:
            raise HTTPException(status_code=403, detail="权限不足，只能查询自己的积分历史")
        
        # 获取用户信息及其积分历史
        user_collection = await managers["user_manager"].get_collection()
        user = await user_collection.find_one(
            {"stuId": stu_id},
            {"pointHistory": {"$slice": -limit}}  # 获取最近的N条记录
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        history = user.get("pointHistory", [])
        
        # 格式化时间并按时间倒序排序
        for record in history:
            if "timestamp" in record:
                record["formatted_time"] = record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        
        history.reverse()  # 最新的在前
        
        return {"history": history, "total": len(history)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取操作历史失败: {str(e)}")

@app.post("/api/points/revoke/{stu_id}/{record_id}")
async def revoke_point_operation(
    stu_id: str,
    record_id: str,
    current_user: dict = Depends(require_auth)
):
    """撤销积分操作（支持撤销的撤销）"""
    try:
        # 验证权限 - 只有管理员可以撤销操作
        from Core.User.Permission import Permission
        if not Permission.can_modify_points(current_user.get("role", "user")):
            raise HTTPException(status_code=403, detail="没有权限撤销积分操作")
        
        # 调用User管理器的撤销方法
        result = await managers["user_manager"].revoke_point_operation(
            stu_id=stu_id,
            record_id=record_id,
            operator=current_user.get("stuId", "unknown")
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "撤销操作失败"))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"撤销操作失败: {str(e)}")

# ========== 初始化接口 ==========

@app.api_route("/api/init", methods=["GET", "POST"])
async def init_system(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    系统完整初始化API
    
    首次访问: 无需登录,自动创建管理员
    再次访问: 需要超级管理员权限
    
    支持GET和POST两种方式访问
    
    包括:
    1. 创建/更新默认管理员
    2. 初始化默认奖品（谢谢惠顾）
    3. 迁移数据库结构
    """
    try:
        # 检查是否是首次访问
        user_collection = await managers["user_manager"].get_collection()
        user_count = await user_collection.count_documents({})
        
        is_first_time = (user_count == 0)
        
        # 如果不是首次访问,需要超级管理员权限
        if not is_first_time:
            if not current_user or current_user.get("role") != "super_admin":
                raise HTTPException(
                    status_code=403, 
                    detail="系统已初始化,再次初始化需要超级管理员权限"
                )
            logger.info(f"超级管理员 {current_user['stuId']} 正在重新初始化系统")
        else:
            logger.info("检测到首次访问,允许无认证初始化")
        result = {
            "success": True,
            "message": "系统初始化完成",
            "details": {
                "admin_status": "",
                "default_prize_status": "",
                "users_migrated": 0,
                "levels_migrated": 0,
                "prizes_migrated": 0,
                "errors": []
            }
        }
        
        # ========== 第一步: 初始化默认管理员 ==========
        logger.info("步骤1: 初始化默认管理员...")
        try:
            # 从配置文件读取默认管理员信息
            try:
                default_stu_id = config.get_value('DefaultAdmin', 'stuId')
                default_password = config.get_value('DefaultAdmin', 'password')
                default_role = config.get_value('DefaultAdmin', 'role')
            except Exception as config_error:
                logger.warning(f"读取默认管理员配置失败，使用默认值: {config_error}")
                default_stu_id = "admin"
                default_password = "admin123"
                default_role = "super_admin"
            
            user_collection = await managers["user_manager"].get_collection()
            admin_exists = await user_collection.find_one({"stuId": default_stu_id})
            
            # 准备管理员数据
            admin_data = {
                "stuId": default_stu_id,
                "creatTime": admin_exists.get("creatTime") if admin_exists else datetime.now(),
                "points": admin_exists.get("points", 0) if admin_exists else 0,
                "completedLevels": admin_exists.get("completedLevels", []) if admin_exists else [],
                "pointHistory": admin_exists.get("pointHistory", []) if admin_exists else [],
                "prizes": admin_exists.get("prizes", []) if admin_exists else [],
                "role": default_role,
                "password": hash_password(default_password)
            }
            
            if admin_exists:
                # 更新现有管理员
                await user_collection.update_one(
                    {"stuId": default_stu_id},
                    {"$set": admin_data}
                )
                result["details"]["admin_status"] = f"管理员账户已更新: {default_stu_id}"
                logger.info(f"✓ 管理员账户已更新: {default_stu_id}")
            else:
                # 创建新管理员
                await user_collection.insert_one(admin_data)
                result["details"]["admin_status"] = f"管理员账户已创建: {default_stu_id} (密码: {default_password})"
                logger.info(f"✓ 管理员账户已创建: {default_stu_id}")
        except Exception as e:
            error_msg = f"初始化管理员失败: {str(e)}"
            logger.error(error_msg)
            result["details"]["errors"].append(error_msg)
        
        # ========== 第二步: 初始化默认奖品 ==========
        logger.info("步骤2: 初始化默认奖品...")
        try:
            prize_collection = await managers["prize_manager"].get_collection()
            
            # 检查是否已存在默认奖品
            default_prize = await prize_collection.find_one({"isDefault": True})
            
            # 计算其他奖品的概率总和
            pipeline = [
                {
                    "$match": {
                        "isDefault": {"$ne": True},
                        "isActive": True
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "totalWeight": {"$sum": "$weight"}
                    }
                }
            ]
            
            agg_result = await prize_collection.aggregate(pipeline).to_list(1)
            other_prizes_weight = agg_result[0]["totalWeight"] if agg_result else 0
            
            # 计算默认奖品的概率
            # 如果其他奖品的权重之和超过100，视为配置错误，不自动创建/更新默认奖品
            if other_prizes_weight > 100:
                error_msg = f"奖品初始化失败：其他奖品权重总和超过100%（{other_prizes_weight}）"
                logger.error(error_msg)
                result["details"]["errors"].append(error_msg)
                # 跳过默认奖品创建/更新，继续后续步骤
                other_prizes_weight = other_prizes_weight
                default_weight = 0
            else:
                default_weight = max(0, 100 - other_prizes_weight)
            
            if default_prize:
                # 更新现有默认奖品
                # 只有在计算出的 default_weight 合法时才更新默认奖品
                if default_weight > 0 or other_prizes_weight <= 100:
                    await prize_collection.update_one(
                        {"_id": default_prize["_id"]},
                        {
                            "$set": {
                                "weight": default_weight,
                                "isActive": True if default_weight > 0 else False,
                                "updated_at": datetime.now()
                            }
                        }
                    )
                    result["details"]["default_prize_status"] = f"默认奖品已更新，概率: {default_weight}%"
                    logger.info(f"✓ 默认奖品已更新，概率: {default_weight}%")
                else:
                    # 当 other_prizes_weight > 100 时，已将错误记录，跳过更新
                    result["details"]["default_prize_status"] = "跳过默认奖品更新，原因: 其他奖品概率总和非法 (>100%)"
                    logger.warning(result["details"]["default_prize_status"])
            else:
                # 创建默认奖品
                if other_prizes_weight > 100:
                    # 已记录错误，跳过创建默认奖品
                    result["details"]["default_prize_status"] = "跳过默认奖品创建，原因: 其他奖品概率总和非法 (>100%)"
                    logger.warning(result["details"]["default_prize_status"])
                else:
                    default_prize_data = {
                        "Name": "谢谢惠顾",
                        "total": 999999,
                        "weight": default_weight,
                        "photo": "",
                        "description": "感谢参与，期待下次好运！",
                        "isActive": True if default_weight > 0 else False,
                        "isDefault": True,
                        "drawn_count": 0,
                        "redeemed_count": 0,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
                    await prize_collection.insert_one(default_prize_data)
                    result["details"]["default_prize_status"] = f"默认奖品已创建，概率: {default_weight}%"
                    logger.info(f"✓ 默认奖品已创建，概率: {default_weight}%")
        except Exception as e:
            error_msg = f"初始化默认奖品失败: {str(e)}"
            logger.error(error_msg)
            result["details"]["errors"].append(error_msg)
        
        # ========== 第三步: 迁移用户数据结构 ==========
        logger.info("步骤3: 迁移用户数据...")
        user_collection = await managers["user_manager"].get_collection()
        users_cursor = user_collection.find({})
        async for user in users_cursor:
            try:
                update_data = {}
                need_update = False
                
                # 删除passLevel字段，迁移到completedLevels
                if "passLevel" in user:
                    old_pass_level = user.get("passLevel", [])
                    if isinstance(old_pass_level, str):
                        old_pass_level = [old_pass_level] if old_pass_level else []
                    update_data["$set"] = update_data.get("$set", {})
                    update_data["$set"]["completedLevels"] = user.get("completedLevels", old_pass_level)
                    update_data["$unset"] = {"passLevel": ""}
                    need_update = True
                
                # 确保新字段存在
                if "pointHistory" not in user:
                    update_data["$set"] = update_data.get("$set", {})
                    update_data["$set"]["pointHistory"] = []
                    need_update = True
                
                if "prizes" not in user:
                    update_data["$set"] = update_data.get("$set", {})
                    update_data["$set"]["prizes"] = []
                    need_update = True
                
                if "completedLevels" not in user:
                    update_data["$set"] = update_data.get("$set", {})
                    update_data["$set"]["completedLevels"] = []
                    need_update = True
                
                if need_update:
                    await user_collection.update_one(
                        {"_id": user["_id"]},
                        update_data
                    )
                    result["details"]["users_migrated"] += 1
                    
            except Exception as e:
                error_msg = f"用户 {user.get('stuId', 'unknown')} 迁移失败: {str(e)}"
                logger.error(error_msg)
                result["details"]["errors"].append(error_msg)
        
        logger.info(f"✓ 用户数据迁移完成，处理了 {result['details']['users_migrated']} 个用户")
        
        # ========== 第四步: 迁移关卡数据结构 ==========
        logger.info("步骤4: 迁移关卡数据...")
        level_collection = await managers["level_manager"].get_collection()
        levels_cursor = level_collection.find({})
        async for level in levels_cursor:
            try:
                update_data = {}
                need_update = False
                
                # 删除participants字段
                if "participants" in level:
                    update_data["$unset"] = {"participants": ""}
                    need_update = True
                
                # 确保使用info字段而不是description
                if "description" in level and "info" not in level:
                    update_data["$set"] = update_data.get("$set", {})
                    update_data["$set"]["info"] = level["description"]
                    need_update = True
                
                if need_update:
                    await level_collection.update_one(
                        {"_id": level["_id"]},
                        update_data
                    )
                    result["details"]["levels_migrated"] += 1
                    
            except Exception as e:
                error_msg = f"关卡 {level.get('name', 'unknown')} 迁移失败: {str(e)}"
                logger.error(error_msg)
                result["details"]["errors"].append(error_msg)
        
        logger.info(f"✓ 关卡数据迁移完成，处理了 {result['details']['levels_migrated']} 个关卡")
        
        # ========== 第五步: 清理奖品数据结构 ==========
        logger.info("步骤5: 清理奖品数据...")
        prize_collection = await managers["prize_manager"].get_collection()
        prizes_cursor = prize_collection.find({})
        async for prize in prizes_cursor:
            try:
                update_data = {}
                need_update = False
                
                # 注意: draw_records 数据需要手动迁移到用户的prizes数组
                # 这里只是标记，不自动删除以防数据丢失
                if "draw_records" in prize and len(prize["draw_records"]) > 0:
                    # 记录警告，需要手动迁移
                    warning_msg = f"奖品 {prize.get('Name', 'unknown')} 包含 {len(prize['draw_records'])} 条抽奖记录，需要手动迁移到用户数据"
                    logger.warning(warning_msg)
                    result["details"]["errors"].append(warning_msg)
                
                # 确保统计字段存在
                if "drawn_count" not in prize:
                    update_data["$set"] = update_data.get("$set", {})
                    update_data["$set"]["drawn_count"] = 0
                    need_update = True
                
                if "redeemed_count" not in prize:
                    update_data["$set"] = update_data.get("$set", {})
                    update_data["$set"]["redeemed_count"] = 0
                    need_update = True
                
                if need_update:
                    await prize_collection.update_one(
                        {"_id": prize["_id"]},
                        update_data
                    )
                    result["details"]["prizes_migrated"] += 1
                    
            except Exception as e:
                error_msg = f"奖品 {prize.get('Name', 'unknown')} 迁移失败: {str(e)}"
                logger.error(error_msg)
                result["details"]["errors"].append(error_msg)
        
        logger.info(f"✓ 奖品数据迁移完成，处理了 {result['details']['prizes_migrated']} 个奖品")
        
        # ========== 完成 ==========
        if len(result["details"]["errors"]) > 0:
            result["message"] = f"系统初始化完成，但有 {len(result['details']['errors'])} 个警告"
            logger.warning(f"系统初始化完成，但有警告: {result['details']['errors']}")
        else:
            result["message"] = "系统初始化完成，所有步骤成功！"
            logger.info("✓ 系统初始化完成，所有步骤成功！")
        
        return result
        
    except Exception as e:
        logger.error(f"系统初始化失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"系统初始化失败: {str(e)}")

# ========== 兼容性接口（重定向到新的统一初始化API） ==========

@app.get("/api/create-default-admin")
async def create_default_admin_compat():
    """创建默认管理员（兼容旧版本，重定向到 /api/init）"""
    logger.info("调用了旧版API，重定向到新的统一初始化API")
    return await init_system()

@app.post("/api/admin/init-database")
async def init_database_compat():
    """数据库迁移（兼容旧版本，重定向到 /api/init）"""
    logger.info("调用了旧版API，重定向到新的统一初始化API")
    return await init_system()

@app.post("/api/admin/create-default")
async def create_default_admin_backup():
    """创建默认管理员（兼容旧版本，重定向到 /api/init）"""
    logger.info("调用了旧版API，重定向到新的统一初始化API")
    return await init_system()

# 设置路由
setup_routes(app)

async def init_default_admin():
    """启动时初始化默认管理员"""
    try:
        # 从配置文件读取默认管理员信息
        try:
            default_stu_id = config.get_value('DefaultAdmin', 'stuId')
            logger.info(f"从配置读取管理员信息: {default_stu_id}")
        except Exception as config_error:
            logger.warning(f"读取默认管理员配置失败，跳过初始化: {config_error}")
            return
        
        # 检查配置的默认管理员是否已存在
        user_manager = managers["user_manager"]
        collection = await user_manager.get_collection()
        admin_exists = await collection.find_one({"stuId": default_stu_id})
        
        if admin_exists:
            current_role = admin_exists.get("role")
            logger.info(f"✅ 配置的管理员已存在: {default_stu_id} ({current_role})")
        else:
            # 管理员不存在，调用创建API逻辑
            logger.info(f"📝 配置的管理员不存在，调用创建API: {default_stu_id}")
            
            # 直接调用创建管理员API的逻辑（不使用HTTP请求）
            response = await create_default_admin()
            logger.info(f"🎉 {response.get('message', '管理员初始化完成')}")
            
    except Exception as e:
        logger.error(f"❌ 初始化默认管理员错误: {e}")

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    await init_default_admin()

def main():
    """主函数"""
    import uvicorn
    
    logger.info("启动NISA Welcome System...")
    logger.info("配置文件盐值: " + config.get_value('System', 'salt'))
    
    # 启动服务器
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 临时禁用自动重载以便调试
        log_level="info"
    )

if __name__ == "__main__":
    main()