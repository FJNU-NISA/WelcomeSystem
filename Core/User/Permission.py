import logging
from typing import Dict, List, Optional
from enum import Enum

class UserRole(Enum):
    """用户角色枚举"""
    USER = "user"           # 普通成员
    ADMIN = "admin"         # 管理员  
    SUPER_ADMIN = "super_admin"  # 超级管理员

class Permission:
    """权限控制类"""
    
    # 定义各角色可访问的页面
    ROLE_PERMISSIONS = {
        UserRole.USER: [
            "info",          # 个人信息查询界面
            "lottery",       # 抽奖界面（仅普通会员可用）
            "login",         # 登录界面
            "setpassword"    # 设置密码界面
        ],
        UserRole.ADMIN: [
            "info",              # 个人信息查询界面
            "modifypoints",      # 分发积分界面
            "login",             # 登录界面
            "setpassword"        # 设置密码界面
            # 管理员只能看到个人信息和分发积分
        ],
        UserRole.SUPER_ADMIN: [
            "info",              # 个人信息查询界面
            "modifypoints",      # 分发积分界面
            "membermanagement",  # 成员管理界面
            "levelmanagement",   # 关卡管理界面
            "prizemanagement",   # 奖品管理界面
            "login",             # 登录界面
            "setpassword"        # 设置密码界面
            # 超级管理员可以访问所有管理功能，但不能抽奖
        ]
    }
    
    @classmethod
    def check_permission(cls, user_role: str, page: str) -> bool:
        """
        检查用户是否有权限访问指定页面
        
        Args:
            user_role: 用户角色字符串
            page: 页面名称
            
        Returns:
            bool: 有权限返回True，否则返回False
        """
        try:
            # 转换角色字符串为枚举
            role_enum = UserRole(user_role)
            
            # 获取该角色的权限列表
            permissions = cls.ROLE_PERMISSIONS.get(role_enum, [])
            
            # 检查页面是否在权限列表中
            return page.lower() in permissions
            
        except ValueError:
            logging.error(f"未知的用户角色: {user_role}")
            return False
        except Exception as e:
            logging.error(f"检查权限时发生错误: {e}")
            return False
    
    @classmethod
    def get_user_pages(cls, user_role: str) -> List[str]:
        """
        获取用户可访问的所有页面
        
        Args:
            user_role: 用户角色字符串
            
        Returns:
            List[str]: 可访问的页面列表
        """
        try:
            role_enum = UserRole(user_role)
            return cls.ROLE_PERMISSIONS.get(role_enum, [])
        except ValueError:
            logging.error(f"未知的用户角色: {user_role}")
            return []
    
    @classmethod
    def is_admin_or_above(cls, user_role: str) -> bool:
        """检查是否为管理员或更高权限"""
        return user_role in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]
    
    @classmethod
    def is_admin(cls, user_role: str) -> bool:
        """检查是否为管理员（不包括超级管理员）"""
        return user_role == UserRole.ADMIN.value
    
    @classmethod
    def is_super_admin(cls, user_role: str) -> bool:
        """检查是否为超级管理员"""
        return user_role == UserRole.SUPER_ADMIN.value
    
    @classmethod
    def can_lottery(cls, user_role: str) -> bool:
        """检查是否可以抽奖（只有普通会员可以抽奖）"""
        return user_role == UserRole.USER.value
    
    @classmethod
    def can_modify_points(cls, user_role: str) -> bool:
        """检查是否可以分发积分（管理员或超级管理员）"""
        return user_role in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]
    
    @classmethod
    def can_modify_points_custom(cls, user_role: str) -> bool:
        """检查是否可以自定义分发积分（超级管理员权限）"""
        return user_role == UserRole.SUPER_ADMIN.value