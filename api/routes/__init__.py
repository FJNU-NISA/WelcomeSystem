"""
API路由模块初始化文件
"""
from .auth import router as auth_router
from .members import router as members_router
from .levels import router as levels_router
from .prizes import router as prizes_router

__all__ = [
    "auth_router",
    "members_router", 
    "levels_router",
    "prizes_router"
]