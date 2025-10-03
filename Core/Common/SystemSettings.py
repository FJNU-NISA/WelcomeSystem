import logging
from typing import Optional, Dict, Any
from bson import ObjectId

import Core.MongoDB.MongoDB as MongoDB

class SystemSettings:
    def __init__(self):
        self.collection_name = "system_settings"
        
    async def _get_collection(self):
        """获取系统设置集合"""
        try:
            database = await MongoDB.get_mongodb_database()
            return database[self.collection_name]
        except Exception as e:
            logging.error(f"获取系统设置集合失败: {e}")
            raise
    
    async def get_setting(self, key: str) -> Optional[Any]:
        """获取系统设置值"""
        try:
            collection = await self._get_collection()
            setting = await collection.find_one({"key": key})
            
            if setting:
                return setting.get("value")
            return None
            
        except Exception as e:
            logging.error(f"获取系统设置时发生错误: {e}")
            return None
    
    async def set_setting(self, key: str, value: Any) -> bool:
        """设置系统配置值"""
        try:
            collection = await self._get_collection()
            
            result = await collection.update_one(
                {"key": key},
                {
                    "$set": {
                        "key": key,
                        "value": value,
                        "updateTime": "$$NOW"
                    }
                },
                upsert=True
            )
            
            return result.upserted_id is not None or result.matched_count > 0
            
        except Exception as e:
            logging.error(f"设置系统配置时发生错误: {e}")
            return False
    
    async def get_lottery_cost(self) -> int:
        """获取抽奖消耗积分"""
        cost = await self.get_setting("lottery_cost")
        return cost if cost is not None else 10  # 默认10积分
    
    async def set_lottery_cost(self, cost: int) -> bool:
        """设置抽奖消耗积分"""
        return await self.set_setting("lottery_cost", cost)
    
    async def initialize_default_settings(self):
        """初始化默认系统设置"""
        try:
            # 默认设置列表
            default_settings = [
                {"key": "lottery_cost", "value": 10, "description": "抽奖消耗积分"},
                {"key": "system_name", "value": "NISA Welcome System", "description": "系统名称"},
                {"key": "welcome_message", "value": "欢迎来到NISA社团迎新系统", "description": "欢迎信息"}
            ]
            
            collection = await self._get_collection()
            
            for setting in default_settings:
                # 检查设置是否已存在
                existing = await collection.find_one({"key": setting["key"]})
                if not existing:
                    setting["createTime"] = "$$NOW"
                    await collection.insert_one(setting)
                    
            logging.info("默认系统设置初始化完成")
            
        except Exception as e:
            logging.error(f"初始化默认系统设置时发生错误: {e}")

# 全局系统设置管理器实例
system_settings = SystemSettings()