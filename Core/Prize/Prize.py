import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

import Core.MongoDB.MongoDB as MongoDB

class Prize:
    def __init__(self):
        self.collection_name = "prize"
    
    async def _get_collection(self):
        """获取奖品集合"""
        try:
            database = await MongoDB.get_mongodb_database()
            return database[self.collection_name]
        except Exception as e:
            logging.error(f"获取奖品集合失败: {e}")
            raise
    
    async def get_collection(self):
        """获取奖品集合（公共方法，用于外部调用）"""
        return await self._get_collection()
    
    async def create_prize(self, prize_data: Dict[str, Any]) -> Optional[str]:
        """
        创建新奖品
        
        Args:
            prize_data: 奖品数据字典，包含奖品信息
            
        Returns:
            str: 创建成功返回奖品ID，失败返回None
        """
        try:
            collection = await self._get_collection()
            
            # 添加统计字段
            prize_data.update({
                "drawn_count": 0,      # 已抽中数量
                "redeemed_count": 0,   # 已兑换数量
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            
            # 直接插入奖品数据
            result = await collection.insert_one(prize_data)
            
            if result.inserted_id:
                logging.info(f"奖品创建成功，ID: {result.inserted_id}")
                return str(result.inserted_id)
            else:
                logging.error("奖品创建失败")
                return None
                
        except DuplicateKeyError as e:
            logging.error(f"奖品创建失败，数据重复: {e}")
            return None
        except Exception as e:
            logging.error(f"奖品创建时发生错误: {e}")
            return None
    
    async def get_prize_by_field(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """
        根据指定字段获取奖品信息
        
        Args:
            field: 字段名
            value: 字段值
            
        Returns:
            Dict: 奖品信息字典，未找到返回None
        """
        try:
            collection = await self._get_collection()
            
            prize = await collection.find_one({field: value})
            
            if prize:
                # 转换ObjectId为字符串
                prize['_id'] = str(prize['_id'])
                logging.info(f"成功通过{field}获取奖品信息: {value}")
                return prize
            else:
                logging.warning(f"未找到奖品，{field}: {value}")
                return None
                
        except Exception as e:
            logging.error(f"通过{field}获取奖品信息时发生错误: {e}")
            return None
    
    async def update_prize(self, prize_id: str, update_data: Dict[str, Any]) -> bool:
        """
        更新奖品信息
        
        Args:
            prize_id: 奖品ID
            update_data: 要更新的数据字典
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            collection = await self._get_collection()
            
            # 转换为ObjectId
            object_id = ObjectId(prize_id)
            
            # 使用$set操作符更新
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            if result.matched_count > 0:
                logging.info(f"奖品信息更新成功: {prize_id}")
                return True
            else:
                logging.warning(f"未找到要更新的奖品: {prize_id}")
                return False
                
        except Exception as e:
            logging.error(f"更新奖品信息时发生错误: {e}")
            return False
    
    async def delete_prize(self, prize_id: str) -> bool:
        """
        删除奖品
        
        Args:
            prize_id: 奖品ID
            
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        try:
            collection = await self._get_collection()
            
            # 转换为ObjectId
            object_id = ObjectId(prize_id)
            
            result = await collection.delete_one({"_id": object_id})
            
            if result.deleted_count > 0:
                logging.info(f"奖品删除成功: {prize_id}")
                return True
            else:
                logging.warning(f"未找到要删除的奖品: {prize_id}")
                return False
                
        except Exception as e:
            logging.error(f"删除奖品时发生错误: {e}")
            return False
    
    async def get_all_prizes(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有奖品列表（分页）"""
        try:
            collection = await self._get_collection()
            cursor = collection.find({}).skip(skip).limit(limit).sort("createTime", -1)
            prizes = await cursor.to_list(length=None)
            
            # 转换ObjectId为字符串
            for prize in prizes:
                prize['_id'] = str(prize['_id'])
            
            return prizes
        except Exception as e:
            logging.error(f"获取奖品列表时发生错误: {e}")
            return []
    
    async def get_available_prizes(self) -> List[Dict[str, Any]]:
        """获取所有可用（有库存）的奖品"""
        try:
            collection = await self._get_collection()
            cursor = collection.find({"quantity": {"$gt": 0}}).sort("createTime", -1)
            prizes = await cursor.to_list(length=None)
            
            # 转换ObjectId为字符串
            for prize in prizes:
                prize['_id'] = str(prize['_id'])
            
            return prizes
        except Exception as e:
            logging.error(f"获取可用奖品列表时发生错误: {e}")
            return []
    
    async def decrease_prize_quantity(self, prize_id: str, quantity: int = 1) -> bool:
        """减少奖品数量"""
        try:
            collection = await self._get_collection()
            object_id = ObjectId(prize_id)
            
            result = await collection.update_one(
                {"_id": object_id, "quantity": {"$gte": quantity}},
                {"$inc": {"quantity": -quantity}}
            )
            
            return result.matched_count > 0
        except Exception as e:
            logging.error(f"减少奖品数量时发生错误: {e}")
            return False
    
    async def count_prizes(self) -> int:
        """获取奖品总数"""
        try:
            collection = await self._get_collection()
            count = await collection.count_documents({})
            return count
        except Exception as e:
            logging.error(f"获取奖品总数时发生错误: {e}")
            return 0

    async def record_prize_drawn(self, prize_id: str, user_id: str, draw_time: datetime = None) -> bool:
        """
        记录奖品被抽中
        
        Args:
            prize_id: 奖品ID
            user_id: 用户ID
            draw_time: 抽中时间（可选，默认为当前时间）
            
        Returns:
            bool: 记录成功返回True，失败返回False
        """
        try:
            collection = await self._get_collection()
            
            if draw_time is None:
                draw_time = datetime.now()
            
            # 更新奖品的抽中数量
            result = await collection.update_one(
                {"_id": ObjectId(prize_id)},
                {
                    "$inc": {"drawn_count": 1},
                    "$set": {"updated_at": datetime.now()},
                    "$push": {
                        "draw_records": {
                            "user_id": user_id,
                            "draw_time": draw_time,
                            "redeemed": False,
                            "redeem_time": None
                        }
                    }
                }
            )
            
            if result.matched_count > 0:
                logging.info(f"奖品抽中记录成功: {prize_id} - {user_id}")
                return True
            else:
                logging.warning(f"未找到奖品: {prize_id}")
                return False
                
        except Exception as e:
            logging.error(f"记录奖品抽中时发生错误: {e}")
            return False

    async def record_prize_redeemed(self, prize_id: str, user_id: str, redeem_time: datetime = None) -> bool:
        """
        记录奖品被兑换
        
        Args:
            prize_id: 奖品ID
            user_id: 用户ID
            redeem_time: 兑换时间（可选，默认为当前时间）
            
        Returns:
            bool: 记录成功返回True，失败返回False
        """
        try:
            collection = await self._get_collection()
            
            if redeem_time is None:
                redeem_time = datetime.now()
            
            # 更新奖品的兑换数量，并标记对应的抽中记录为已兑换
            result = await collection.update_one(
                {
                    "_id": ObjectId(prize_id),
                    "draw_records.user_id": user_id,
                    "draw_records.redeemed": False
                },
                {
                    "$inc": {"redeemed_count": 1},
                    "$set": {
                        "updated_at": datetime.now(),
                        "draw_records.$.redeemed": True,
                        "draw_records.$.redeem_time": redeem_time
                    }
                }
            )
            
            if result.matched_count > 0:
                logging.info(f"奖品兑换记录成功: {prize_id} - {user_id}")
                return True
            else:
                logging.warning(f"未找到未兑换的奖品记录: {prize_id} - {user_id}")
                return False
                
        except Exception as e:
            logging.error(f"记录奖品兑换时发生错误: {e}")
            return False

    async def get_user_drawn_prizes(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户抽中的奖品
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Dict]: 用户抽中的奖品列表
        """
        try:
            collection = await self._get_collection()
            
            # 使用聚合查询获取用户抽中的奖品
            pipeline = [
                {"$match": {"draw_records.user_id": user_id}},
                {"$unwind": "$draw_records"},
                {"$match": {"draw_records.user_id": user_id}},
                {"$project": {
                    "Name": 1,
                    "photo": 1,
                    "draw_time": "$draw_records.draw_time",
                    "redeemed": "$draw_records.redeemed",
                    "redeem_time": "$draw_records.redeem_time"
                }}
            ]
            
            cursor = collection.aggregate(pipeline)
            prizes = await cursor.to_list(length=None)
            
            # 转换ObjectId为字符串
            for prize in prizes:
                prize['_id'] = str(prize['_id'])
            
            return prizes
            
        except Exception as e:
            logging.error(f"获取用户抽中奖品时发生错误: {e}")
            return []

    async def get_prize_statistics(self) -> Dict[str, int]:
        """
        获取奖品统计信息
        
        Returns:
            Dict: 包含总抽中数量和总兑换数量的字典
        """
        try:
            collection = await self._get_collection()
            
            # 使用聚合查询获取统计信息
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_drawn": {"$sum": "$drawn_count"},
                        "total_redeemed": {"$sum": "$redeemed_count"},
                        "total_prizes": {"$sum": "$total"}
                    }
                }
            ]
            
            result = await collection.aggregate(pipeline).to_list(1)
            
            if result:
                stats = result[0]
                return {
                    "total_drawn": stats.get("total_drawn", 0),
                    "total_redeemed": stats.get("total_redeemed", 0),
                    "total_prizes": stats.get("total_prizes", 0)
                }
            else:
                return {
                    "total_drawn": 0,
                    "total_redeemed": 0,
                    "total_prizes": 0
                }
                
        except Exception as e:
            logging.error(f"获取奖品统计信息时发生错误: {e}")
            return {
                "total_drawn": 0,
                "total_redeemed": 0,
                "total_prizes": 0
            }
    
    async def ensure_default_prize(self) -> bool:
        """
        确保默认的"谢谢惠顾"奖品存在
        如果不存在则创建，如果存在则更新其概率为 100% - 其他奖品概率总和
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            collection = await self._get_collection()
            
            # 检查是否已存在默认奖品
            default_prize = await collection.find_one({"isDefault": True})
            
            # 计算其他奖品的概率总和（排除默认奖品，只计算激活的）
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
            
            result = await collection.aggregate(pipeline).to_list(1)
            other_prizes_weight = result[0]["totalWeight"] if result else 0
            
            # 计算默认奖品的概率（100% - 其他奖品概率）
            default_weight = max(0, 100 - other_prizes_weight)
            
            if default_prize:
                # 更新现有默认奖品的概率
                await collection.update_one(
                    {"_id": default_prize["_id"]},
                    {
                        "$set": {
                            "weight": default_weight,
                            "updated_at": datetime.now()
                        }
                    }
                )
                logging.info(f"默认奖品概率已更新: {default_weight}%")
            else:
                # 创建默认奖品
                default_prize_data = {
                    "Name": "谢谢惠顾",
                    "total": 999999,  # 设置一个很大的数量，表示无限
                    "weight": default_weight,
                    "photo": "",
                    "isActive": True if default_weight > 0 else False,  # 如果概率为0则停用
                    "isDefault": True,  # 标记为默认奖品
                    "drawn_count": 0,
                    "redeemed_count": 0,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                
                await collection.insert_one(default_prize_data)
                logging.info(f"默认奖品已创建，概率: {default_weight}%")
            
            return True
            
        except Exception as e:
            logging.error(f"确保默认奖品存在时发生错误: {e}")
            return False

    async def compute_other_active_weight(self) -> float:
        """
        计算当前所有激活且非默认奖品的权重总和（返回浮点数）
        """
        try:
            collection = await self._get_collection()
            pipeline = [
                {"$match": {"isDefault": {"$ne": True}, "isActive": True}},
                {"$group": {"_id": None, "totalWeight": {"$sum": "$weight"}}}
            ]
            result = await collection.aggregate(pipeline).to_list(1)
            total = float(result[0]["totalWeight"]) if result and result[0].get("totalWeight") is not None else 0.0
            return total
        except Exception as e:
            logging.exception(f"计算其他激活奖品权重总和时发生错误: {e}")
            return 0.0
    
    async def update_default_prize_weight(self) -> bool:
        """
        更新默认奖品的概率为 100% - 其他奖品概率总和
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            collection = await self._get_collection()
            
            # 计算其他奖品的概率总和（排除默认奖品，只计算激活的）
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
            
            result = await collection.aggregate(pipeline).to_list(1)
            other_prizes_weight = result[0]["totalWeight"] if result else 0
            
            # 计算默认奖品的概率（不包含默认奖品自身）
            default_weight = max(0, 100 - float(other_prizes_weight or 0))
            
            # 更新默认奖品
            update_result = await collection.update_one(
                {"isDefault": True},
                {
                    "$set": {
                        "weight": default_weight,
                        "isActive": True if default_weight > 0 else False,
                        "updated_at": datetime.now()
                    }
                }
            )
            
            if update_result.matched_count > 0:
                logging.info(f"默认奖品概率已更新: {default_weight}%")
                return True
            else:
                logging.warning("未找到默认奖品")
                return False
                
        except Exception as e:
            logging.error(f"更新默认奖品概率时发生错误: {e}")
            return False
