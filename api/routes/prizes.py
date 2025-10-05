"""
奖品管理相关路由
包含奖品CRUD、库存管理等功能
"""
import io
import csv
import os
import uuid
import logging
from datetime import datetime
from PIL import Image
from fastapi import APIRouter, HTTPException, Depends, Query, File, UploadFile
from fastapi.responses import Response
from bson import ObjectId

from Core.Prize.Prize import Prize
from Core.Common.Config import Config
from api.dependencies import require_super_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/prizes", tags=["奖品管理"])

# 实例化奖品管理器
prize_manager = Prize()
config_manager = Config()

@router.get("/stats")
async def get_prizes_stats(current_user: dict = Depends(require_super_admin)):
    """获取奖品统计信息"""
    try:
        # 获取集合
        collection = await prize_manager.get_collection()
        
        # 获取奖品种类数量(不包括默认奖品)
        prize_types = await collection.count_documents({"isDefault": {"$ne": True}})
        
        # 剩余奖品数量（排除谢谢惠顾/默认奖品）
        remaining_quantity_pipeline = [
            {"$match": {"isDefault": {"$ne": True}}},
            {"$group": {
                "_id": None,
                "remainingQuantity": {"$sum": "$total"}
            }}
        ]
        remaining_result = await collection.aggregate(remaining_quantity_pipeline).to_list(1)
        remaining_quantity = remaining_result[0]["remainingQuantity"] if remaining_result else 0
        
        # 获取所有奖品数量的总和(不包括默认奖品)
        total_quantity_pipeline = [
            {"$match": {"isDefault": {"$ne": True}}},
            {"$group": {
                "_id": None,
                "totalQuantity": {"$sum": "$total"}
            }}
        ]
        quantity_result = await collection.aggregate(total_quantity_pipeline).to_list(1)
        total_quantity = quantity_result[0]["totalQuantity"] if quantity_result else 0
        
        # 获取可用奖品数量（库存大于0的）
        available_pipeline = [
            {"$match": {"total": {"$gt": 0}}},
            {"$group": {
                "_id": None,
                "availableQuantity": {"$sum": "$total"}
            }}
        ]
        available_result = await collection.aggregate(available_pipeline).to_list(1)
        available_quantity = available_result[0]["availableQuantity"] if available_result else 0
        
        # 获取抽中和兑换统计
        stats = await prize_manager.get_prize_statistics()
        
        # 计算未兑换奖品数 = 总抽中数量 - 总兑换数量
        total_drawn = stats.get("total_drawn", 0)
        total_redeemed = stats.get("total_redeemed", 0)
        unredeemed = total_drawn - total_redeemed
        
        return {
            "total": total_quantity,  # 改为所有奖品数量的总和(不包括默认奖品)
            "prizeTypes": prize_types,  # 奖品种类数量
            "active": remaining_quantity,  # 剩余奖品数量（排除谢谢惠顾）
            "unredeemed": unredeemed,  # 未兑换奖品数
            "available": available_quantity,
            "totalStock": total_quantity,
            "lowStockCount": 0,  # 暂时设为0，可根据需要添加低库存逻辑
            "totalDrawn": total_drawn,  # 总抽中数量
            "totalRedeemed": total_redeemed  # 总兑换数量
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取奖品统计信息失败: {str(e)}")

@router.get("")
async def get_prizes_list(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: str = Query(None),
    status: str = Query(None),
    search: str = Query(None),
    current_user: dict = Depends(require_super_admin)
):
    """获取奖品列表"""
    try:
        # 构建过滤条件
        filter_query = {}
            
        if search:
            filter_query["$or"] = [
                {"Name": {"$regex": search, "$options": "i"}}
            ]
        
        # 计算分页
        skip = (page - 1) * limit
        collection = await prize_manager.get_collection()
        total = await collection.count_documents(filter_query)
        
        # 获取数据
        cursor = collection.find(filter_query).skip(skip).limit(limit).sort("createdAt", -1)
        prizes = []
        
        async for prize in cursor:
            prize["_id"] = str(prize["_id"])

            # 图片回退处理：如果 photo 指定且文件存在则使用，否则回退到 default.png
            photo_name = prize.get('photo') or 'default.png'
            photo_path = os.path.join('Assest', 'Prize', photo_name)
            if not photo_name or not os.path.exists(photo_path):
                photo_name = 'default.png'

            prize["image"] = f"/Assest/Prize/{photo_name}"
            # 兼容旧前端：将 photo 字段也回退为存在的文件名，防止前端直接使用 prize.photo 导致 404
            prize["photo"] = photo_name

            # 如果这是默认奖品，动态计算其概率为 100 - sum(其他激活奖品权重)
            try:
                if prize.get("isDefault"):
                    other_sum = await prize_manager.compute_other_active_weight()
                    default_w = max(0.0, 100.0 - float(other_sum or 0.0))
                    # 保证返回给前端的是一个数字（float）并且不把默认奖品计入其他计算
                    prize["weight"] = default_w
            except Exception:
                # 计算失败时保留原始值并记录异常
                logger.exception("计算默认奖品权重失败")

            prizes.append(prize)
        
        return {
            "prizes": prizes,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取奖品列表失败: {str(e)}")

@router.post("")
async def create_prize(prize_data: dict, current_user: dict = Depends(require_super_admin)):
    """创建新奖品"""
    try:
        # 验证必填字段
        required_fields = ["Name", "total", "weight"]
        for field in required_fields:
            if field not in prize_data or not prize_data[field]:
                raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")
        
        # 验证奖品名称不能为空
        name = prize_data["Name"].strip()
        if not name:
            raise HTTPException(status_code=400, detail="奖品名称不能为空")
        
        # 检查同名奖品
        collection = await prize_manager.get_collection()
        existing = await collection.find_one({"Name": name})
        if existing:
            raise HTTPException(status_code=400, detail="奖品名称已存在")
        
        # 在创建前校验概率总和（排除默认奖品）
        try:
            collection = await prize_manager.get_collection()
            pipeline = [
                {"$match": {"isDefault": {"$ne": True}, "isActive": True}},
                {"$group": {"_id": None, "totalProbability": {"$sum": "$weight"}}}
            ]
            result = await collection.aggregate(pipeline).to_list(1)
            current_total = float(result[0]["totalProbability"]) if result and result[0].get("totalProbability") is not None else 0.0
        except Exception:
            logger.exception("校验当前概率总和时发生错误")
            current_total = 0.0

        # 创建奖品数据
        new_prize = {
            "Name": name,
            "total": int(prize_data["total"]),
            "weight": float(prize_data["weight"]),
            "photo": prize_data.get("photo", "").strip(),
            "isActive": prize_data.get("isActive", True),
            "createdAt": datetime.now(),
            "updatedAt": datetime.now()
        }
        # 校验新加后的总概率是否超过100
        try:
            new_total = current_total + float(new_prize["weight"] or 0)
            if new_total > 100.0:
                raise HTTPException(status_code=400, detail=f"无法创建：激活奖品的概率总和（不含默认奖品）将超过100%（当前: {current_total:.1f}，添加: {new_prize['weight']}，合计: {new_total:.1f}）")
        except HTTPException:
            raise
        except Exception:
            logger.exception("校验新奖品概率时发生错误")
            raise HTTPException(status_code=500, detail="概率校验失败")

        # 创建奖品
        prize_id = await prize_manager.create_prize(new_prize)
        if prize_id:
            # 更新默认奖品的概率
            await prize_manager.update_default_prize_weight()
            return {"success": True, "prizeId": prize_id, "message": "奖品创建成功"}
        else:
            raise HTTPException(status_code=500, detail="奖品创建失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建奖品失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建奖品失败: {str(e)}")

@router.get("/{prize_id}")
async def get_prize(prize_id: str, current_user: dict = Depends(require_super_admin)):
    """获取单个奖品信息"""
    try:
        # 验证奖品ID
        if not ObjectId.is_valid(prize_id):
            raise HTTPException(status_code=400, detail="无效的奖品ID")
        
        # 获取奖品信息
        prize = await prize_manager.get_prize_by_field("_id", ObjectId(prize_id))
        if not prize:
            raise HTTPException(status_code=404, detail="奖品不存在")
        # 格式化返回字段并处理图片回退
        prize["_id"] = str(prize["_id"]) if isinstance(prize.get("_id"), ObjectId) else str(prize.get("_id"))
        photo_name = prize.get('photo') or 'default.png'
        photo_path = os.path.join('Assest', 'Prize', photo_name)
        if not photo_name or not os.path.exists(photo_path):
            photo_name = 'default.png'

        prize["image"] = f"/Assest/Prize/{photo_name}"
        # 兼容旧前端：将 photo 字段也回退为存在的文件名
        prize["photo"] = photo_name

        # 如果这是默认奖品，动态计算其概率并覆盖
        try:
            if prize.get("isDefault"):
                other_sum = await prize_manager.compute_other_active_weight()
                default_w = max(0.0, 100.0 - float(other_sum or 0.0))
                prize["weight"] = default_w
        except Exception:
            logger.exception("计算默认奖品权重失败")

        return prize
        
    except HTTPException:
        raise
    except Exception as e:
        # 使用 exception 以记录完整堆栈，便于服务器端排查
        logger.exception(f"获取奖品信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取奖品信息失败: {str(e)}")

@router.put("/{prize_id}")
async def update_prize(
    prize_id: str, 
    prize_data: dict, 
    current_user: dict = Depends(require_super_admin)
):
    """更新奖品信息"""
    try:
        # 验证奖品ID
        if not ObjectId.is_valid(prize_id):
            raise HTTPException(status_code=400, detail="无效的奖品ID")
        
        # 验证奖品是否存在
        existing_prize = await prize_manager.get_prize_by_field("_id", ObjectId(prize_id))
        if not existing_prize:
            raise HTTPException(status_code=404, detail="奖品不存在")
        
        # 如果更新名称，检查是否重复
        if "Name" in prize_data:
            name = prize_data["Name"].strip()
            if not name:
                raise HTTPException(status_code=400, detail="奖品名称不能为空")
            
            # 检查同名奖品（排除当前奖品）
            collection = await prize_manager.get_collection()
            existing = await collection.find_one({
                "Name": name,
                "_id": {"$ne": ObjectId(prize_id)}
            })
            if existing:
                raise HTTPException(status_code=400, detail="奖品名称已存在")
        
        # 准备更新数据
        update_data = {key: value for key, value in prize_data.items() if key != "_id"}
        update_data["updatedAt"] = datetime.now()
        # 如果更新了 weight 字段，需要校验概率总和（排除默认奖品并排除当前奖品）
        if "weight" in update_data:
            try:
                collection = await prize_manager.get_collection()
                match_condition = {"isDefault": {"$ne": True}, "isActive": True, "_id": {"$ne": ObjectId(prize_id)}}
                pipeline = [
                    {"$match": match_condition},
                    {"$group": {"_id": None, "totalProbability": {"$sum": "$weight"}}}
                ]
                result = await collection.aggregate(pipeline).to_list(1)
                current_total = float(result[0]["totalProbability"]) if result and result[0].get("totalProbability") is not None else 0.0
            except Exception:
                logger.exception("校验更新后概率总和时发生错误")
                current_total = 0.0

            try:
                new_total = current_total + float(update_data.get("weight") or 0)
                if new_total > 100.0:
                    raise HTTPException(status_code=400, detail=f"无法更新：激活奖品的概率总和（不含默认奖品）将超过100%（当前排除自身: {current_total:.1f}，更新为: {update_data.get('weight')}，合计: {new_total:.1f}）")
            except HTTPException:
                raise
            except Exception:
                logger.exception("校验更新奖品概率时发生错误")
                raise HTTPException(status_code=500, detail="概率校验失败")

        # 更新奖品
        success = await prize_manager.update_prize(prize_id, update_data)
        if success:
            # 更新默认奖品的概率
            await prize_manager.update_default_prize_weight()
            return {"success": True, "message": "奖品更新成功"}
        else:
            raise HTTPException(status_code=500, detail="奖品更新失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新奖品失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新奖品失败: {str(e)}")

@router.delete("/{prize_id}")
async def delete_prize(prize_id: str, current_user: dict = Depends(require_super_admin)):
    """删除奖品"""
    try:
        # 验证奖品ID
        if not ObjectId.is_valid(prize_id):
            raise HTTPException(status_code=400, detail="无效的奖品ID")
        
        # 检查是否是默认奖品
        prize = await prize_manager.get_prize_by_field("_id", ObjectId(prize_id))
        if prize and prize.get("isDefault"):
            raise HTTPException(status_code=400, detail="默认奖品（谢谢惠顾）不能删除")
        
        # 删除奖品
        success = await prize_manager.delete_prize(prize_id)
        if success:
            # 更新默认奖品的概率
            await prize_manager.update_default_prize_weight()
            return {"success": True, "message": "奖品删除成功"}
        else:
            raise HTTPException(status_code=404, detail="奖品不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除奖品失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除奖品失败: {str(e)}")

@router.patch("/{prize_id}/toggle-active")
async def toggle_prize_active(prize_id: str, current_user: dict = Depends(require_super_admin)):
    """切换奖品激活状态"""
    try:
        collection = await prize_manager.get_collection()
        
        # 获取当前奖品状态
        prize = await collection.find_one({"_id": ObjectId(prize_id)})
        if not prize:
            raise HTTPException(status_code=404, detail="奖品不存在")
        
        # 检查是否是默认奖品
        if prize.get("isDefault"):
            # 默认奖品只有在概率为0时才能停用
            current_active = prize.get("isActive", True)
            if current_active:  # 尝试停用
                # 计算当前默认奖品的概率
                if prize.get("weight", 0) > 0:
                    raise HTTPException(
                        status_code=400, 
                        detail="默认奖品（谢谢惠顾）的概率不为0，不能停用。只有当其他奖品的概率总和达到100%时才能停用。"
                    )
        
        # 切换激活状态
        new_status = not prize.get("isActive", True)
        
        result = await collection.update_one(
            {"_id": ObjectId(prize_id)},
            {"$set": {"isActive": new_status, "updatedAt": datetime.now()}}
        )
        
        if result.modified_count > 0:
            # 更新默认奖品的概率
            await prize_manager.update_default_prize_weight()
            
            return {
                "message": f"奖品已{'激活' if new_status else '停用'}",
                "isActive": new_status
            }
        else:
            raise HTTPException(status_code=500, detail="状态更新失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换奖品状态错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-image")
async def upload_prize_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_super_admin)
):
    """上传奖品图片"""
    try:
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="文件必须是图片格式")
        
        # 验证文件大小（50MB）
        max_size = 50 * 1024 * 1024
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > max_size:
            raise HTTPException(status_code=400, detail="文件大小不能超过50MB")
        
        # 重置文件指针
        await file.seek(0)
        
        # 生成唯一文件名
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            file_extension = '.jpg'
        
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # 确保上传目录存在
        upload_dir = "Assest/Prize"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(upload_dir, unique_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        return {
            "success": True,
            "filename": unique_filename,
            "originalName": file.filename,
            "size": file_size,
            "message": "图片上传成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传图片失败: {str(e)}")

# 奖品抽中和兑换记录相关API
@router.post("/record-drawn")
async def record_prize_drawn(
    prize_id: str,
    user_id: str,
    current_user: dict = Depends(require_super_admin)
):
    """记录奖品被抽中"""
    try:
        success = await prize_manager.record_prize_drawn(prize_id, user_id)
        if success:
            return {"message": "奖品抽中记录成功"}
        else:
            raise HTTPException(status_code=400, detail="记录奖品抽中失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录奖品抽中失败: {str(e)}")

@router.post("/record-redeemed")
async def record_prize_redeemed(
    prize_id: str,
    user_id: str,
    current_user: dict = Depends(require_super_admin)
):
    """记录奖品被兑换"""
    try:
        success = await prize_manager.record_prize_redeemed(prize_id, user_id)
        if success:
            return {"message": "奖品兑换记录成功"}
        else:
            raise HTTPException(status_code=400, detail="记录奖品兑换失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录奖品兑换失败: {str(e)}")

@router.get("/user-drawn/{user_id}")
async def get_user_drawn_prizes(
    user_id: str,
    current_user: dict = Depends(require_super_admin)
):
    """获取用户抽中的奖品"""
    try:
        prizes = await prize_manager.get_user_drawn_prizes(user_id)
        return {"prizes": prizes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户抽中奖品失败: {str(e)}")

# 需要创建独立的抽奖配置路由
lottery_router = APIRouter(prefix="/api/admin/lottery-config", tags=["抽奖配置"])

@lottery_router.get("")
async def get_lottery_config(current_user: dict = Depends(require_super_admin)):
    """获取抽奖配置"""
    try:
        config = config_manager.get_lottery_config()
        return {
            "lotteryPoints": config.get('points', 1)
        }
    except Exception as e:
        logger.error(f"获取抽奖配置失败: {e}")
        return {
            "lotteryPoints": 1
        }

@lottery_router.post("")
async def update_lottery_config(config_data: dict, current_user: dict = Depends(require_super_admin)):
    """更新抽奖配置"""
    try:
        # 验证配置数据
        lottery_points = config_data.get("lotteryPoints", 1)
        
        # 验证数值
        if not isinstance(lottery_points, int) or lottery_points < 1:
            raise HTTPException(status_code=400, detail="抽奖积分必须是大于0的整数")
        
        # 保存到配置文件
        config_manager.update_lottery_config({
            "lotteryPoints": lottery_points
        })
        
        return {
            "message": "抽奖配置更新成功",
            "lotteryPoints": lottery_points
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新抽奖配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新抽奖配置失败: {str(e)}")

@router.post("/validate-probability")
async def validate_probability(data: dict, current_user: dict = Depends(require_super_admin)):
    """验证奖品概率"""
    try:
        new_weight = data.get("weight", 0)
        exclude_id = data.get("excludeId")
        
        collection = await prize_manager.get_collection()
        
        # 构建查询条件（编辑时排除当前奖品）
        # 仅统计激活且非默认的奖品
        match_condition = {"isDefault": {"$ne": True}, "isActive": True}
        if exclude_id:
            # 编辑时排除当前奖品
            match_condition["_id"] = {"$ne": ObjectId(exclude_id)}

        pipeline = [
            {"$match": match_condition},
            {"$group": {
                "_id": None,
                "totalProbability": {"$sum": "$weight"}
            }}
        ]
        
        result = await collection.aggregate(pipeline).to_list(1)
        current_total = result[0]["totalProbability"] if result else 0
        new_total = current_total + new_weight
        
        valid = (new_total <= 100.0)
        return {
            "valid": valid,
            "totalProbability": new_total,
            "currentTotal": current_total,
            "message": f"当前总概率: {current_total:.1f}%, 添加后: {new_total:.1f}%",
            "canProceed": valid
        }
    except Exception as e:
        logger.error(f"验证概率失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证概率失败: {str(e)}")

@router.get("/probability-summary")
async def get_probability_summary(current_user: dict = Depends(require_super_admin)):
    """获取概率总和信息"""
    try:
        collection = await prize_manager.get_collection()
        
        # 首先计算非默认奖品的概率总和
        non_default_pipeline = [
            {"$match": {
                "isActive": {"$ne": False},
                "isDefault": {"$ne": True}
            }},
            {"$group": {
                "_id": None,
                "totalProbability": {"$sum": "$weight"}
            }}
        ]
        
        non_default_result = await collection.aggregate(non_default_pipeline).to_list(1)
        non_default_total = float(non_default_result[0]["totalProbability"]) if non_default_result and non_default_result[0].get("totalProbability") is not None else 0.0
        
        # 计算默认奖品（谢谢惠顾）的概率
        thanks_probability = max(0.0, 100.0 - non_default_total)
        
        # 获取所有激活奖品的实际概率总和（包括动态计算的默认奖品）
        all_active_pipeline = [
            {"$match": {
                "isActive": {"$ne": False}
            }}
        ]
        
        all_prizes = await collection.find({"isActive": {"$ne": False}}).to_list(None)
        actual_total = 0.0
        
        for prize in all_prizes:
            if prize.get("isDefault"):
                # 默认奖品使用动态计算的概率
                actual_total += thanks_probability
            else:
                # 非默认奖品使用存储的权重
                actual_total += float(prize.get("weight", 0))
        
        return {
            "totalProbability": non_default_total,  # 这里应该返回非默认奖品的总和
            "nonDefaultTotal": non_default_total,
            "thanksProbability": thanks_probability,
            "actualTotal": actual_total,  # 实际总概率（包括谢谢惠顾）
            "message": f"实际总概率: {actual_total:.1f}%, 普通奖品: {non_default_total:.1f}%, 谢谢惠顾: {thanks_probability:.1f}%"
        }
    except Exception as e:
        logger.error(f"获取概率总和失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取概率总和失败: {str(e)}")