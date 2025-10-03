import logging
from typing import Optional, Dict, Any, List
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

import Core.MongoDB.MongoDB as MongoDB

class User:
    def __init__(self):
        self.collection_name = "user"
    
    async def _get_collection(self):
        """获取用户集合（私有方法）"""
        try:
            database = await MongoDB.get_mongodb_database()
            return database[self.collection_name]
        except Exception as e:
            logging.error(f"获取用户集合失败: {e}")
            raise
    
    async def get_collection(self):
        """获取用户集合（公共方法，用于外部调用）"""
        return await self._get_collection()
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        创建新用户
        
        Args:
            user_data: 用户数据字典，包含用户信息
            
        Returns:
            str: 创建成功返回用户ID，失败返回None
        """
        try:
            collection = await self._get_collection()
            
            # 添加创建时间到用户数据
            from datetime import datetime
            user_data_with_time = {
                **user_data,
                "creatTime": datetime.now()
            }
            
            # 直接插入文档
            result = await collection.insert_one(user_data_with_time)
            
            if result.inserted_id:
                result_id = str(result.inserted_id)
                logging.info(f"用户创建成功，ID: {result_id}")
                return result_id
            else:
                logging.error("用户创建失败")
                return None
                
        except DuplicateKeyError as e:
            logging.error(f"用户创建失败，数据重复: {e}")
            return None
        except Exception as e:
            logging.error(f"用户创建时发生错误: {e}")
            return None
    
    async def get_user_by_field(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """
        根据指定字段获取用户信息
        
        Args:
            field: 字段名
            value: 字段值
            
        Returns:
            Dict: 用户信息字典，未找到返回None
        """
        try:
            collection = await self._get_collection()
            
            user = await collection.find_one({field: value})
            
            if user:
                # 转换ObjectId为字符串
                user['_id'] = str(user['_id'])
                logging.info(f"成功通过{field}获取用户信息: {value}")
                return user
            else:
                logging.warning(f"未找到用户，{field}: {value}")
                return None
                
        except Exception as e:
            logging.error(f"通过{field}获取用户信息时发生错误: {e}")
            return None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            update_data: 要更新的数据字典
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            collection = await self._get_collection()
            
            # 转换为ObjectId
            object_id = ObjectId(user_id)
            
            # 只使用$set操作符更新数据，不更新时间戳
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            if result.matched_count > 0:
                logging.info(f"用户信息更新成功: {user_id}")
                return True
            else:
                logging.warning(f"未找到要更新的用户: {user_id}")
                return False
                
        except Exception as e:
            logging.error(f"更新用户信息时发生错误: {e}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        try:
            collection = await self._get_collection()
            
            # 转换为ObjectId
            object_id = ObjectId(user_id)
            
            result = await collection.delete_one({"_id": object_id})
            
            if result.deleted_count > 0:
                logging.info(f"用户删除成功: {user_id}")
                return True
            else:
                logging.warning(f"未找到要删除的用户: {user_id}")
                return False
                
        except Exception as e:
            logging.error(f"删除用户时发生错误: {e}")
            return False
    
    async def get_user_by_stu_id(self, stu_id: str) -> Optional[Dict[str, Any]]:
        """根据学号获取用户信息"""
        return await self.get_user_by_field("stuId", stu_id)
    
    async def count_users(self) -> int:
        """获取用户总数"""
        try:
            collection = await self._get_collection()
            count = await collection.count_documents({})
            return count
        except Exception as e:
            logging.error(f"获取用户总数时发生错误: {e}")
            return 0
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有用户列表（分页）"""
        try:
            collection = await self._get_collection()
            cursor = collection.find({}).skip(skip).limit(limit).sort("creatTime", -1)
            users = await cursor.to_list(length=None)
            
            # 转换ObjectId为字符串
            for user in users:
                user['_id'] = str(user['_id'])
            
            return users
        except Exception as e:
            logging.error(f"获取用户列表时发生错误: {e}")
            return []
    
    async def update_user_points(self, stu_id: str, points_change: int) -> bool:
        """更新用户积分"""
        try:
            collection = await self._get_collection()
            result = await collection.update_one(
                {"stuId": stu_id},
                {"$inc": {"points": points_change}}
            )
            return result.matched_count > 0
        except Exception as e:
            logging.error(f"更新用户积分时发生错误: {e}")
            return False
    
    async def add_user_prize(self, stu_id: str, prize_id: str, prize_name: str) -> bool:
        """为用户添加奖品"""
        try:
            collection = await self._get_collection()
            prize_data = {
                "prizeId": prize_id,
                "prizeName": prize_name,
                "obtainTime": "$$NOW",
                "redeemed": False,
                "redemptionCode": f"{stu_id}_{prize_id}_{int(__import__('time').time())}"
            }
            
            result = await collection.update_one(
                {"stuId": stu_id},
                {"$push": {"prizes": prize_data}}
            )
            return result.matched_count > 0
        except Exception as e:
            logging.error(f"为用户添加奖品时发生错误: {e}")
            return False
    
    async def redeem_user_prize(self, stu_id: str, redemption_code: str) -> bool:
        """核销用户奖品"""
        try:
            collection = await self._get_collection()
            result = await collection.update_one(
                {"stuId": stu_id, "prizes.redemptionCode": redemption_code},
                {"$set": {"prizes.$.redeemed": True, "prizes.$.redemptionTime": "$$NOW"}}
            )
            return result.matched_count > 0
        except Exception as e:
            logging.error(f"核销用户奖品时发生错误: {e}")
            return False
    
    async def update_user_level(self, stu_id: str, level_id: str, level_name: str) -> bool:
        """更新用户通关关卡"""
        try:
            collection = await self._get_collection()
            level_data = {
                "levelId": level_id,
                "levelName": level_name,
                "passTime": "$$NOW"
            }
            
            result = await collection.update_one(
                {"stuId": stu_id},
                {"$addToSet": {"passedLevels": level_data}}
            )
            return result.matched_count > 0
        except Exception as e:
            logging.error(f"更新用户关卡时发生错误: {e}")
            return False
    
    async def revoke_point_operation(self, stu_id: str, record_id: str, operator: str) -> Dict[str, Any]:
        """
        撤销积分操作
        
        Args:
            stu_id: 用户学号
            record_id: 操作记录ID
            operator: 撤销操作者
            
        Returns:
            Dict: 包含操作结果和信息的字典
        """
        try:
            from datetime import datetime
            from bson import ObjectId
            
            collection = await self._get_collection()
            
            # 查找用户及对应的记录
            user = await collection.find_one({"stuId": stu_id})
            if not user:
                return {"success": False, "message": "用户不存在"}
            
            # 在用户的积分历史中查找该记录
            point_history = user.get("pointHistory", [])
            target_record = None
            record_index = -1
            
            for i, record in enumerate(point_history):
                if record.get("recordId") == record_id:
                    target_record = record
                    record_index = i
                    break
            
            if not target_record:
                return {"success": False, "message": "操作记录不存在"}
            
            # 检查是否已被撤销
            if target_record.get("revoked", False):
                return {"success": False, "message": "该操作已被撤销,无法重复撤销"}
            
            # 计算要回退的积分（与原操作相反）
            points_revert = -target_record.get("pointsChange", 0)
            
            # 判断是否是撤销"撤销操作"(即恢复操作)
            is_revoking_revoke = target_record.get("type") == "revoke"
            
            # 标记原记录为已撤销
            update_path = f"pointHistory.{record_index}.revoked"
            revoked_by_path = f"pointHistory.{record_index}.revokedBy"
            revoked_at_path = f"pointHistory.{record_index}.revokedAt"
            
            # 创建撤销操作的新记录
            revoke_record = {
                "recordId": str(ObjectId()),
                "type": "revoke",
                "pointsChange": points_revert,
                "reason": f"撤销操作: {target_record.get('reason', '未知原因')}",
                "originalRecordId": record_id,
                "originalType": target_record.get("type"),
                "operator": operator,
                "timestamp": datetime.now(),
                "revoked": False,
                "revokedBy": None,
                "revokedAt": None
            }
            
            # 步骤1: 先标记原记录为已撤销,并更新积分
            update_ops_1 = {
                "$inc": {"points": points_revert},
                "$set": {
                    update_path: True,
                    revoked_by_path: operator,
                    revoked_at_path: datetime.now()
                }
            }
            
            # 如果是撤销"撤销操作",需要恢复原始记录的状态
            if is_revoking_revoke:
                original_record_id = target_record.get("originalRecordId")
                if original_record_id:
                    # 查找原始记录的索引
                    original_index = -1
                    original_rec = None
                    for i, rec in enumerate(point_history):
                        if rec.get("recordId") == original_record_id:
                            original_index = i
                            original_rec = rec
                            break
                    
                    if original_index >= 0:
                        # 恢复原始记录(取消revoked标记)
                        update_ops_1["$set"][f"pointHistory.{original_index}.revoked"] = False
                        update_ops_1["$set"][f"pointHistory.{original_index}.revokedBy"] = None
                        update_ops_1["$set"][f"pointHistory.{original_index}.revokedAt"] = None
                        
                        # 如果原始记录是关卡完成,需要重新添加到completedLevels
                        if original_rec and original_rec.get("type") == "level_completion":
                            level_id = original_rec.get("levelId")
                            if level_id:
                                update_ops_1["$addToSet"] = {"completedLevels": level_id}
            else:
                # 如果原操作是关卡完成,需要从completedLevels中移除
                if target_record.get("type") == "level_completion":
                    level_id = target_record.get("levelId")
                    if level_id:
                        update_ops_1["$pull"] = {"completedLevels": level_id}
            
            # 执行第一步更新
            result = await collection.update_one(
                {"stuId": stu_id},
                update_ops_1
            )
            
            if result.modified_count == 0:
                return {"success": False, "message": "撤销操作失败"}
            
            # 步骤2: 添加撤销记录到积分历史
            result2 = await collection.update_one(
                {"stuId": stu_id},
                {"$push": {"pointHistory": revoke_record}}
            )
            
            if result2.modified_count > 0:
                action_desc = "恢复原记录" if is_revoking_revoke else "撤销操作"
                return {
                    "success": True,
                    "message": f"{action_desc}成功",
                    "pointsReverted": points_revert,
                    "revokeRecordId": revoke_record["recordId"],
                    "isRestoringRecord": is_revoking_revoke
                }
            else:
                return {"success": False, "message": "添加撤销记录失败"}
                
        except Exception as e:
            logging.error(f"撤销积分操作时发生错误: {e}")
            return {"success": False, "message": f"撤销操作失败: {str(e)}"}
