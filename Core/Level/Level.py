import asyncio
import logging
from typing import Optional, Dict, List, Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

import Core.MongoDB.MongoDB as MongoDB

class Level:
    def __init__(self):
        self.collection_name = "level"
    
    async def _get_collection(self):
        """获取关卡集合"""
        try:
            database = await MongoDB.get_mongodb_database()
            return database[self.collection_name]
        except Exception as e:
            logging.error(f"获取关卡集合失败: {e}")
            raise
    
    async def get_collection(self):
        """获取关卡集合（公共方法，用于外部调用）"""
        return await self._get_collection()
    
    async def create_level(self, level_data: Dict[str, Any]) -> Optional[str]:
        """
        创建新关卡
        
        Args:
            level_data: 关卡数据字典，包含关卡信息
            
        Returns:
            str: 创建成功返回关卡ID，失败返回None
        """
        try:
            collection = await self._get_collection()
            
            # 直接插入关卡数据
            result = await collection.insert_one(level_data)
            
            if result.inserted_id:
                logging.info(f"关卡创建成功，ID: {result.inserted_id}")
                return str(result.inserted_id)
            else:
                logging.error("关卡创建失败")
                return None
                
        except DuplicateKeyError as e:
            logging.error(f"关卡创建失败，数据重复: {e}")
            return None
        except Exception as e:
            logging.error(f"关卡创建时发生错误: {e}")
            return None
    
    async def get_level_by_field(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """
        根据指定字段获取关卡信息
        
        Args:
            field: 字段名
            value: 字段值
            
        Returns:
            Dict: 关卡信息字典，未找到返回None
        """
        try:
            collection = await self._get_collection()
            
            level = await collection.find_one({field: value})
            
            if level:
                # 转换ObjectId为字符串
                level['_id'] = str(level['_id'])
                logging.info(f"成功通过{field}获取关卡信息: {value}")
                return level
            else:
                logging.warning(f"未找到关卡，{field}: {value}")
                return None
                
        except Exception as e:
            logging.error(f"通过{field}获取关卡信息时发生错误: {e}")
            return None
    
    async def update_level(self, level_id: str, update_data: Dict[str, Any]) -> bool:
        """
        更新关卡信息
        
        Args:
            level_id: 关卡ID
            update_data: 要更新的数据字典
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            collection = await self._get_collection()
            
            # 转换为ObjectId
            object_id = ObjectId(level_id)
            
            # 使用$set操作符更新
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            if result.matched_count > 0:
                logging.info(f"关卡信息更新成功: {level_id}")
                return True
            else:
                logging.warning(f"未找到要更新的关卡: {level_id}")
                return False
                
        except Exception as e:
            logging.error(f"更新关卡信息时发生错误: {e}")
            return False
    
    async def delete_level(self, level_id: str) -> bool:
        """
        删除关卡
        
        Args:
            level_id: 关卡ID
            
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        try:
            collection = await self._get_collection()
            
            # 转换为ObjectId
            object_id = ObjectId(level_id)
            
            result = await collection.delete_one({"_id": object_id})
            
            if result.deleted_count > 0:
                logging.info(f"关卡删除成功: {level_id}")
                return True
            else:
                logging.warning(f"未找到要删除的关卡: {level_id}")
                return False
                
        except Exception as e:
            logging.error(f"删除关卡时发生错误: {e}")
            return False
    
    async def get_all_levels(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有关卡列表（分页）"""
        try:
            collection = await self._get_collection()
            cursor = collection.find({}).skip(skip).limit(limit).sort("createTime", -1)
            levels = await cursor.to_list(length=None)
            
            # 转换ObjectId为字符串
            for level in levels:
                level['_id'] = str(level['_id'])
            
            return levels
        except Exception as e:
            logging.error(f"获取关卡列表时发生错误: {e}")
            return []
    
    async def get_level_by_id(self, level_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取关卡信息"""
        return await self.get_level_by_field("_id", ObjectId(level_id))
    
    async def count_levels(self) -> int:
        """获取关卡总数"""
        try:
            collection = await self._get_collection()
            count = await collection.count_documents({})
            return count
        except Exception as e:
            logging.error(f"获取关卡总数时发生错误: {e}")
            return 0