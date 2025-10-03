"""
API依赖注入模块
包含认证、权限检查等依赖项
"""
from typing import Optional
from urllib.parse import quote
from fastapi import HTTPException, Depends, Cookie, Request
from fastapi.responses import RedirectResponse
from Core.User.Session import session_manager
from Core.User.Permission import Permission

async def require_auth(session_token: Optional[str] = Cookie(None)) -> dict:
    """要求用户登录 - API使用"""
    if not session_token:
        raise HTTPException(status_code=401, detail="需要登录")
    
    user_info = await session_manager.get_user_by_session(session_token)
    if not user_info:
        raise HTTPException(status_code=401, detail="会话无效")
    
    return user_info

async def require_auth_redirect(request: Request):
    """要求用户登录 - 页面路由使用，未登录时重定向"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        # 获取当前请求的URL作为回调地址
        current_url = str(request.url)
        callback_url = quote(current_url, safe='')
        return RedirectResponse(url=f"/login?redirect={callback_url}")
    
    user_info = await session_manager.get_user_by_session(session_token)
    if not user_info:
        # 会话无效也重定向到登录页面
        current_url = str(request.url)
        callback_url = quote(current_url, safe='')
        return RedirectResponse(url=f"/login?redirect={callback_url}")
    
    return user_info

async def require_super_admin_redirect(request: Request):
    """要求超级管理员权限 - 页面路由使用，未登录时重定向"""
    session_token = request.cookies.get("session_token")
    
    # 先检查是否已登录
    if not session_token:
        current_url = str(request.url)
        callback_url = quote(current_url, safe='')
        return RedirectResponse(url=f"/login?redirect={callback_url}")
    
    user_info = await session_manager.get_user_by_session(session_token)
    if not user_info:
        current_url = str(request.url)
        callback_url = quote(current_url, safe='')
        return RedirectResponse(url=f"/login?redirect={callback_url}")
    
    # 检查管理员权限
    if not Permission.is_super_admin(user_info.get("role", "user")):
        # 权限不足，重定向到登录页面（或可以重定向到无权限页面）
        current_url = str(request.url)
        callback_url = quote(current_url, safe='')
        return RedirectResponse(url=f"/login?redirect={callback_url}&error=insufficient_permission")
    
    return user_info

async def require_super_admin(current_user: dict = Depends(require_auth)):
    """要求超级管理员权限"""
    if not Permission.is_super_admin(current_user.get("role", "user")):
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return current_user

async def require_admin_redirect(request: Request):
    """要求管理员权限（管理员或超级管理员）- 页面路由使用，未登录时重定向"""
    session_token = request.cookies.get("session_token")
    
    # 先检查是否已登录
    if not session_token:
        current_url = str(request.url)
        callback_url = quote(current_url, safe='')
        return RedirectResponse(url=f"/login?redirect={callback_url}")
    
    user_info = await session_manager.get_user_by_session(session_token)
    if not user_info:
        current_url = str(request.url)
        callback_url = quote(current_url, safe='')
        return RedirectResponse(url=f"/login?redirect={callback_url}")
    
    # 检查管理员权限（管理员或超级管理员）
    user_role = user_info.get("role", "user")
    if not Permission.is_admin_or_above(user_role):
        # 权限不足，重定向到登录页面
        current_url = str(request.url)
        callback_url = quote(current_url, safe='')
        return RedirectResponse(url=f"/login?redirect={callback_url}&error=insufficient_permission")
    
    return user_info

async def require_admin(current_user: dict = Depends(require_auth)):
    """要求管理员权限（管理员或超级管理员）"""
    user_role = current_user.get("role", "user")
    if not Permission.is_admin(user_role) and not Permission.is_super_admin(user_role):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user

async def get_current_user_optional(session_token: Optional[str] = Cookie(None)) -> Optional[dict]:
    """可选的当前用户获取，不强制要求登录"""
    import logging
    logger = logging.getLogger(__name__)
    
    if not session_token:
        logger.info("🔍 没有找到session_token cookie")
        return None
    
    logger.info(f"🔍 检查session_token: {session_token[:10]}...")
    
    user_info = await session_manager.get_user_by_session(session_token)
    if user_info:
        logger.info(f"✅ 用户验证成功: {user_info.get('stuId')} ({user_info.get('role')})")
    else:
        logger.warning(f"❌ 用户验证失败: session_token={session_token[:10]}...")
    
    return user_info