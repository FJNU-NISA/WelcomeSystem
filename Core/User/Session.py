import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

import Core.MongoDB.MongoDB as MongoDB

class Session:
    def __init__(self):
        self.collection_name = "session"
        
    async def _get_collection(self):
        """获取会话集合"""
        try:
            database = await MongoDB.get_mongodb_database()
            return database[self.collection_name]
        except Exception as e:
            logging.error(f"获取会话集合失败: {e}")
            raise
    
    async def create_session(self, user_data: Dict[str, Any], expire_hours: int = 168) -> str:
        """
        创建用户会话
        
        Args:
            user_data: 用户数据
            expire_hours: 会话过期时间（小时，默认168小时=7天）
            
        Returns:
            str: 会话token
        """
        try:
            collection = await self._get_collection()
            
            # 生成会话token
            token = str(uuid.uuid4())
            
            # 计算过期时间
            expire_time = datetime.now() + timedelta(hours=expire_hours)
            
            session_data = {
                "token": token,
                "userId": user_data.get("_id"),
                "stuId": user_data.get("stuId"),
                "role": user_data.get("role", "user"),
                "createTime": datetime.now(),
                "expireTime": expire_time,
                "active": True
            }
            
            # 先删除该用户的旧会话
            await collection.delete_many({"stuId": user_data.get("stuId")})
            
            # 创建新会话
            await collection.insert_one(session_data)
            
            logging.info(f"会话创建成功，用户: {user_data.get('stuId')}, token: {token}")
            return token
            
        except Exception as e:
            logging.error(f"创建会话时发生错误: {e}")
            return ""
    
    async def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """根据token获取会话信息"""
        try:
            # 确保token是字符串类型，而不是Cookie对象
            if not isinstance(token, str) or not token:
                logging.warning(f"Invalid token provided: {type(token)}, value: {token}")
                return None
                
            collection = await self._get_collection()
            
            logging.info(f"🔍 查找会话token: {token[:10]}...")
            
            session = await collection.find_one({
                "token": token,
                "active": True,
                "expireTime": {"$gt": datetime.now()}
            })
            
            if session:
                session['_id'] = str(session['_id'])
                logging.info(f"✅ 找到有效会话: 用户={session.get('stuId')}, 角色={session.get('role')}")
                return session
            else:
                logging.warning(f"❌ 未找到有效会话或会话已过期: {token[:10]}...")
                return None
            
        except Exception as e:
            logging.error(f"获取会话时发生错误: {e}")
            return None
    
    async def delete_session(self, token: str) -> bool:
        """删除会话（登出）"""
        try:
            collection = await self._get_collection()
            
            result = await collection.update_one(
                {"token": token},
                {"$set": {"active": False}}
            )
            
            return result.matched_count > 0
            
        except Exception as e:
            logging.error(f"删除会话时发生错误: {e}")
            return False
    
    async def get_user_by_session(self, token: str) -> Optional[Dict[str, Any]]:
        """根据session token获取用户信息"""
        try:
            session = await self.get_session(token)
            if session:
                # 从数据库获取最新的用户信息
                from Core.User.User import User
                user_manager = User()
                user_collection = await user_manager.get_collection()
                user_data = await user_collection.find_one({"stuId": session["stuId"]})
                
                if user_data:
                    # 导入权限生成函数
                    import sys
                    import os
                    
                    # 添加项目根目录到路径
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    if project_root not in sys.path:
                        sys.path.append(project_root)
                    
                    from app import get_user_permissions
                    
                    user_role = user_data.get("role", "user")
                    permissions = get_user_permissions(user_role, user_data)
                    
                    return {
                        "stuId": user_data["stuId"],
                        "role": user_role,
                        "points": user_data.get("points", 0),
                        "permissions": permissions
                    }
            return None
        except Exception as e:
            logging.error(f"根据会话获取用户信息时发生错误: {e}")
            return None

    async def clean_expired_sessions(self):
        """清理过期会话"""
        try:
            collection = await self._get_collection()
            
            result = await collection.delete_many({
                "expireTime": {"$lt": datetime.now()}
            })
            
            logging.info(f"清理过期会话: {result.deleted_count} 条")
            
        except Exception as e:
            logging.error(f"清理过期会话时发生错误: {e}")

# 全局会话管理器实例
session_manager = Session()