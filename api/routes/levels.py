"""
关卡管理相关路由
包含关卡CRUD、参与者统计等功能
"""
import io
import csv
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from bson import ObjectId

from Core.User.User import User
from Core.Level.Level import Level
from api.dependencies import require_super_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/levels", tags=["关卡管理"])

# 实例化管理器
user_manager = User()
level_manager = Level()

@router.get("/stats")
async def get_levels_stats(current_user: dict = Depends(require_super_admin)):
    """获取关卡统计信息"""
    try:
        # 获取集合
        collection = await level_manager.get_collection()
        
        # 总关卡数
        total = await collection.count_documents({})
        
        # 已激活关卡数
        active = await collection.count_documents({"isActive": True})
        
        # 未激活关卡数
        inactive = await collection.count_documents({"isActive": False})
        
        return {
            "total": total,
            "active": active,
            "inactive": inactive
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关卡统计信息失败: {str(e)}")

@router.get("")
async def get_levels_list(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query(None),
    search: str = Query(None),
    current_user: dict = Depends(require_super_admin)
):
    """获取关卡列表"""
    try:
        # 构建过滤条件
        filter_query = {}
        
        if status == "active":
            filter_query["isActive"] = True
        elif status == "inactive":
            filter_query["isActive"] = False
            
        if search:
            filter_query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        # 计算分页
        skip = (page - 1) * limit
        collection = await level_manager.get_collection()
        total = await collection.count_documents(filter_query)
        
        # 获取数据
        cursor = collection.find(filter_query).skip(skip).limit(limit).sort("createdAt", -1)
        levels = []
        user_collection = await user_manager.get_collection()
        
        async for level in cursor:
            level["_id"] = str(level["_id"])
            # 计算参与者数量
            participant_count = await user_collection.count_documents({
                "completedLevels": str(level["_id"])
            })
            level["participantCount"] = participant_count
            levels.append(level)
        
        return {
            "levels": levels,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关卡列表失败: {str(e)}")

@router.post("")
async def create_level(level_data: dict, current_user: dict = Depends(require_super_admin)):
    """创建新关卡"""
    try:
        # 验证必填字段
        required_fields = ["name", "points"]
        for field in required_fields:
            if field not in level_data or not level_data[field]:
                raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")
        
        # 检查同名关卡
        collection = await level_manager.get_collection()
        existing = await collection.find_one({"name": level_data["name"]})
        if existing:
            raise HTTPException(status_code=400, detail="关卡名称已存在")
        
        # 创建关卡数据 - 使用新的字段结构
        new_level = {
            "name": level_data["name"],
            "info": level_data.get("info", ""),  # 使用 info 字段代替 description
            "points": int(level_data["points"]),
            "isActive": level_data.get("isActive", True),
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
            "createdBy": current_user["stuId"]
        }
        
        # 插入数据库
        result = await collection.insert_one(new_level)
        if result.inserted_id:
            new_level["_id"] = str(result.inserted_id)
            new_level["participantCount"] = 0
            return {"message": "关卡创建成功", "level": new_level}
        else:
            raise HTTPException(status_code=500, detail="创建关卡失败")
            
    except Exception as e:
        logger.error(f"创建关卡错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{level_id}")
async def get_level_info(level_id: str, current_user: dict = Depends(require_super_admin)):
    """获取关卡信息"""
    try:
        collection = await level_manager.get_collection()
        level = await collection.find_one({"_id": ObjectId(level_id)})
        if not level:
            raise HTTPException(status_code=404, detail="关卡不存在")
        
        level["_id"] = str(level["_id"])
        # 计算参与者数量
        user_collection = await user_manager.get_collection()
        participant_count = await user_collection.count_documents({
            "completedLevels": str(level["_id"])
        })
        level["participantCount"] = participant_count
        return level
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关卡信息失败: {str(e)}")

@router.put("/{level_id}")
async def update_level(level_id: str, level_data: dict, current_user: dict = Depends(require_super_admin)):
    """更新关卡信息"""
    try:
        collection = await level_manager.get_collection()
        
        # 检查关卡是否存在
        existing = await collection.find_one({"_id": ObjectId(level_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="关卡不存在")
        
        # 检查名称是否重复（排除自身）
        if "name" in level_data:
            existing_name = await collection.find_one({
                "name": level_data["name"],
                "_id": {"$ne": ObjectId(level_id)}
            })
            if existing_name:
                raise HTTPException(status_code=400, detail="关卡名称已存在")
        
        # 准备更新数据
        update_data = level_data.copy()
        update_data["updatedAt"] = datetime.now()
        update_data["updatedBy"] = current_user["stuId"]
        
        # 转换积分为整数
        if "points" in update_data:
            update_data["points"] = int(update_data["points"])
        
        # 更新数据库
        await collection.update_one(
            {"_id": ObjectId(level_id)},
            {"$set": update_data}
        )
        
        return {"message": "关卡信息更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新关卡信息失败: {str(e)}")

@router.delete("/{level_id}")
async def delete_level(level_id: str, current_user: dict = Depends(require_super_admin)):
    """删除关卡"""
    try:
        collection = await level_manager.get_collection()
        result = await collection.delete_one({"_id": ObjectId(level_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="关卡不存在")
        
        # 同时从用户的完成关卡列表中移除
        user_collection = await user_manager.get_collection()
        await user_collection.update_many(
            {"completedLevels": level_id},
            {"$pull": {"completedLevels": level_id}}
        )
        
        return {"message": "关卡删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除关卡失败: {str(e)}")

@router.get("/{level_id}/participants")
async def get_level_participants(
    level_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(require_super_admin)
):
    """获取关卡参与者列表"""
    try:
        # 计算分页
        skip = (page - 1) * limit
        
        # 获取参与者
        user_collection = await user_manager.get_collection()
        total = await user_collection.count_documents({"completedLevels": level_id})
        cursor = user_collection.find(
            {"completedLevels": level_id},
            {"password": 0}  # 不返回密码
        ).skip(skip).limit(limit)
        
        participants = []
        async for user in cursor:
            user["_id"] = str(user["_id"])
            participants.append(user)
        
        return {
            "participants": participants,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取参与者列表失败: {str(e)}")

@router.get("/export")
async def export_levels(current_user: dict = Depends(require_super_admin)):
    """导出关卡数据"""
    try:
        # 获取所有关卡数据
        collection = await level_manager.get_collection()
        user_collection = await user_manager.get_collection()
        cursor = collection.find({})
        levels = []
        async for level in cursor:
            level["_id"] = str(level["_id"])
            # 计算参与者数量
            participant_count = await user_collection.count_documents({
                "completedLevels": str(level["_id"])
            })
            level["participantCount"] = participant_count
            levels.append(level)
        
        # 创建CSV内容
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题行
        headers = ["ID", "名称", "描述", "积分", "状态", "创建时间", "参与者数量"]
        writer.writerow(headers)
        
        # 写入数据行
        for level in levels:
            row = [
                level.get("_id", ""),
                level.get("name", ""),
                level.get("description", ""),
                level.get("points", 0),
                "启用" if level.get("isActive", False) else "禁用",
                level.get("createdAt", "").strftime("%Y-%m-%d %H:%M:%S") if isinstance(level.get("createdAt"), datetime) else "",
                level.get("participantCount", 0)
            ]
            writer.writerow(row)
        
        # 准备响应
        csv_content = output.getvalue().encode('utf-8-sig')
        
        headers = {
            'Content-Disposition': f'attachment; filename="levels_{datetime.now().strftime("%Y%m%d")}.csv"',
            'Content-Type': 'text/csv; charset=utf-8'
        }
        
        return Response(content=csv_content, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出关卡数据失败: {str(e)}")

@router.patch("/{level_id}/toggle-active")
async def toggle_level_active(level_id: str, current_user: dict = Depends(require_super_admin)):
    """切换关卡激活状态"""
    try:
        collection = await level_manager.get_collection()
        
        # 获取当前关卡状态
        level = await collection.find_one({"_id": ObjectId(level_id)})
        if not level:
            raise HTTPException(status_code=404, detail="关卡不存在")
        
        # 切换激活状态
        new_status = not level.get("isActive", True)
        
        result = await collection.update_one(
            {"_id": ObjectId(level_id)},
            {"$set": {"isActive": new_status, "updatedAt": datetime.now()}}
        )
        
        if result.modified_count > 0:
            return {
                "message": f"关卡已{'激活' if new_status else '停用'}",
                "isActive": new_status
            }
        else:
            raise HTTPException(status_code=500, detail="状态更新失败")
            
    except Exception as e:
        logger.error(f"切换关卡状态错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))