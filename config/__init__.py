"""
配置模块初始化文件
"""
from .app_config import create_app, setup_routes, get_managers

__all__ = [
    "create_app",
    "setup_routes",
    "get_managers"
]