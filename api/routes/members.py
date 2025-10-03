"""
成员管理相关路由
包含成员CRUD、统计等功能
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
router = APIRouter(prefix="/api/admin/members", tags=["成员管理"])

# 实例化管理器
user_manager = User()
level_manager = Level()

@router.get("/stats")
async def get_members_stats(current_user: dict = Depends(require_super_admin)):
    """获取成员统计信息"""
    try:
        pipeline = [
            {
                "$group": {
                    "_id": "$role",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        collection = await user_manager.get_collection()
        stats_result = await collection.aggregate(pipeline).to_list(None)
        stats = {item["_id"]: item["count"] for item in stats_result}
        
        return {
            "total": sum(stats.values()),
            "user": stats.get("user", 0),
            "admin": stats.get("admin", 0), 
            "super_admin": stats.get("super_admin", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("")
async def get_members_list(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    role: str = Query(None),
    search: str = Query(None),
    current_user: dict = Depends(require_super_admin)
):
    """获取成员列表"""
    try:
        # 构建过滤条件
        filter_query = {}
        
        if role:
            filter_query["role"] = role
            
        if search:
            filter_query["stuId"] = {"$regex": search, "$options": "i"}
        
        # 计算分页
        skip = (page - 1) * limit
        collection = await user_manager.get_collection()
        total = await collection.count_documents(filter_query)
        
        # 获取数据
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        members = []
        
        # 获取所有关卡信息用于名称映射
        level_collection = await level_manager.get_collection()
        levels = {}
        async for level in level_collection.find():
            levels[str(level["_id"])] = level.get("name", f"关卡{level.get('level', '')}")
        
        async for member in cursor:
            member["_id"] = str(member["_id"])
            
            # 转换通过的关卡ID为关卡名称
            completed_levels = member.get("completedLevels", []) or member.get("passLevel", [])
            if completed_levels and isinstance(completed_levels, list):
                # 关卡ID列表转换为关卡名称
                level_names = []
                for level_id in completed_levels:
                    level_name = levels.get(str(level_id), f"未知关卡({level_id})")
                    level_names.append(level_name)
                member["passedLevelNames"] = level_names
            else:
                member["passedLevelNames"] = []
            
            # 不返回密码
            member.pop("password", None)
            members.append(member)
        
        return {
            "members": members,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成员列表失败: {str(e)}")

@router.post("")
async def create_member(member_data: dict, current_user: dict = Depends(require_super_admin)):
    """创建新成员"""
    try:
        # 验证必填字段
        required_fields = ["stuId", "role"]
        for field in required_fields:
            if field not in member_data or not member_data[field]:
                raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")
        
        # 检查学号是否存在
        collection = await user_manager.get_collection()
        existing = await collection.find_one({"stuId": member_data["stuId"]})
        if existing:
            raise HTTPException(status_code=400, detail="学号已存在")
        
        # 处理密码设置
        from api.routes.auth import hash_password
        if member_data.get("password"):
            # 如果提供了密码，则进行哈希处理
            password_hash = hash_password(member_data["password"])
        else:
            # 如果没有提供密码，默认密码为学号
            password_hash = hash_password(member_data["stuId"])
        
        # 创建用户数据
        user_data = {
            "stuId": member_data["stuId"],
            "role": member_data["role"],
            "points": int(member_data.get("points", 0)),
            "password": password_hash,  # 密码哈希或空字符串
            "completedLevels": [],  # 通过的关卡ID列表
            "pointHistory": [],  # 积分操作历史
            "prizes": [],  # 获得的奖品列表
            "creatTime": datetime.now(),
            "createdBy": current_user["stuId"]
        }
        
        # 插入数据库
        collection = await user_manager.get_collection()
        result = await collection.insert_one(user_data)
        if result.inserted_id:
            user_data["_id"] = str(result.inserted_id)
            user_data.pop("password", None)  # 不返回密码
            return {"message": "成员创建成功", "member": user_data}
        else:
            raise HTTPException(status_code=500, detail="创建成员失败")
            
    except Exception as e:
        logger.error(f"创建成员错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{member_id}")
async def get_member_info(member_id: str, current_user: dict = Depends(require_super_admin)):
    """获取成员基本信息"""
    try:
        collection = await user_manager.get_collection()
        member = await collection.find_one({"_id": ObjectId(member_id)})
        if not member:
            raise HTTPException(status_code=404, detail="成员不存在")
        
        member["_id"] = str(member["_id"])
        # 不返回密码
        member.pop("password", None)
        return member
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成员信息失败: {str(e)}")

@router.get("/{member_id}/detail")
async def get_member_detail(member_id: str, current_user: dict = Depends(require_super_admin)):
    """获取成员详细信息"""
    try:
        collection = await user_manager.get_collection()
        member = await collection.find_one({"_id": ObjectId(member_id)})
        if not member:
            raise HTTPException(status_code=404, detail="成员不存在")
        
        member["_id"] = str(member["_id"])
        # 不返回密码
        member.pop("password", None)
        
        # 获取关卡详情
        if member.get("completedLevels"):
            level_ids = member["completedLevels"]
            if level_ids:
                level_collection = await level_manager.get_collection()
                levels_cursor = level_collection.find({"_id": {"$in": [ObjectId(lid) for lid in level_ids]}})
                levels = await levels_cursor.to_list(None)
                member["levelDetails"] = [{"_id": str(level["_id"]), "name": level["name"]} for level in levels]
        
        return member
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成员详细信息失败: {str(e)}")

@router.put("/{member_id}")
async def update_member(member_id: str, member_data: dict, current_user: dict = Depends(require_super_admin)):
    """更新成员信息 - 保护最后一个超级管理员"""
    try:
        # 检查成员是否存在
        collection = await user_manager.get_collection()
        existing = await collection.find_one({"_id": ObjectId(member_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="成员不存在")
        
        # 如果要修改角色,检查是否是最后一个超级管理员
        if "role" in member_data:
            new_role = member_data["role"]
            old_role = existing.get("role")
            
            # 如果从super_admin改为其他角色,检查是否是最后一个
            if old_role == "super_admin" and new_role != "super_admin":
                super_admin_count = await collection.count_documents({"role": "super_admin"})
                if super_admin_count <= 1:
                    raise HTTPException(
                        status_code=403, 
                        detail="不能修改最后一个超级管理员的角色,系统至少需要保留一个超级管理员"
                    )
        
        # 检查学号是否重复（排除自身）
        if "stuId" in member_data and member_data["stuId"]:
            existing_stuid = await collection.find_one({
                "stuId": member_data["stuId"],
                "_id": {"$ne": ObjectId(member_id)}
            })
            if existing_stuid:
                raise HTTPException(status_code=400, detail="学号已存在")
        
        # 准备更新数据
        update_data = member_data.copy()
        update_data["updatedBy"] = current_user["stuId"]
        
        # 转换积分为整数
        if "points" in update_data:
            update_data["points"] = int(update_data["points"])
        
        # 处理密码更新 - 只有当提供了密码且不为空时才更新
        if "password" in update_data:
            if update_data["password"] and update_data["password"].strip():
                # 如果提供了非空密码，进行哈希处理
                from api.routes.auth import hash_password
                update_data["password"] = hash_password(update_data["password"])
            else:
                # 如果密码为空或只有空白字符，从更新数据中移除密码字段
                update_data.pop("password", None)
        
        # 更新数据库
        await collection.update_one(
            {"_id": ObjectId(member_id)},
            {"$set": update_data}
        )
        
        return {"message": "成员信息更新成功"}
    except HTTPException:
        # 重新抛出 HTTPException，不要被下面的 Exception 捕获
        raise
    except Exception as e:
        logger.error(f"更新成员信息时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新成员信息失败: {str(e)}")

@router.delete("/{member_id}")
async def delete_member(member_id: str, current_user: dict = Depends(require_super_admin)):
    """删除成员 - 保护最后一个超级管理员"""
    try:
        collection = await user_manager.get_collection()
        
        # 获取要删除的成员信息
        member_to_delete = await collection.find_one({"_id": ObjectId(member_id)})
        if not member_to_delete:
            raise HTTPException(status_code=404, detail="成员不存在")
        
        # 如果要删除的是超级管理员,检查是否是最后一个
        if member_to_delete.get("role") == "super_admin":
            super_admin_count = await collection.count_documents({"role": "super_admin"})
            if super_admin_count <= 1:
                raise HTTPException(
                    status_code=403, 
                    detail="不能删除最后一个超级管理员,系统至少需要保留一个超级管理员"
                )
        
        # 执行删除
        result = await collection.delete_one({"_id": ObjectId(member_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="成员不存在")
        
        return {"message": "成员删除成功"}
    except HTTPException:
        # 重新抛出 HTTPException，不要被下面的 Exception 捕获
        raise
    except Exception as e:
        logger.error(f"删除成员时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除成员失败: {str(e)}")

@router.get("/export")
async def export_members(current_user: dict = Depends(require_super_admin)):
    """导出成员数据"""
    try:
        # 获取所有成员数据
        collection = await user_manager.get_collection()
        cursor = collection.find({})
        members = []
        async for member in cursor:
            member["_id"] = str(member["_id"])
            members.append(member)
        
        # 创建CSV内容
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题行
        headers = ["ID", "学号", "角色", "积分", "创建时间", "通过关卡数"]
        writer.writerow(headers)
        
        # 写入数据行
        for member in members:
            row = [
                member.get("_id", ""),
                member.get("stuId", ""),
                member.get("role", ""),
                member.get("points", 0),
                member.get("creatTime", "").strftime("%Y-%m-%d %H:%M:%S") if isinstance(member.get("creatTime"), datetime) else "",
                len(member.get("completedLevels", []))
            ]
            writer.writerow(row)
        
        # 准备响应
        csv_content = output.getvalue().encode('utf-8-sig')
        
        headers = {
            'Content-Disposition': f'attachment; filename="members_{datetime.now().strftime("%Y%m%d")}.csv"',
            'Content-Type': 'text/csv; charset=utf-8'
        }
        
        return Response(content=csv_content, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出成员数据失败: {str(e)}")