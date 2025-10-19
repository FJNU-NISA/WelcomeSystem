"""
汇总看板相关路由
包含各类统计数据的API
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from Core.User.User import User
from Core.Level.Level import Level
from Core.Prize.Prize import Prize
from api.dependencies import require_super_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/dashboard", tags=["汇总看板"])

# 实例化管理器
user_manager = User()
level_manager = Level()
prize_manager = Prize()

@router.get("/stats/members-distribution")
async def get_members_distribution(current_user: dict = Depends(require_super_admin)):
    """
    获取普通成员学院分布统计
    按学号前缀区分：12开头为计网学院，其他为其他学院
    """
    try:
        collection = await user_manager.get_collection()
        
        # 获取所有普通成员
        users = await collection.find({"role": "user"}).to_list(None)
        
        # 统计各学院人数
        jiwang_count = 0  # 计网学院
        other_count = 0   # 其他学院
        
        for user in users:
            stu_id = user.get("stuId", "")
            if stu_id.startswith("12"):
                jiwang_count += 1
            else:
                other_count += 1
        
        return {
            "jiwang": jiwang_count,
            "other": other_count
        }
    except Exception as e:
        logger.error(f"获取成员学院分布失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取成员学院分布失败: {str(e)}")


@router.get("/stats/level-completion")
async def get_level_completion(current_user: dict = Depends(require_super_admin)):
    """
    获取关卡闯关人数统计
    不包括"欢迎给我们投票!!!"关卡
    """
    try:
        level_collection = await level_manager.get_collection()
        user_collection = await user_manager.get_collection()
        
        # 获取所有关卡，排除"欢迎给我们投票!!!"
        levels = await level_collection.find({
            "name": {"$ne": "欢迎给我们投票!!!"}
        }).to_list(None)
        
        level_stats = []
        
        for level in levels:
            level_id = str(level["_id"])
            level_name = level.get("name", f"关卡{level.get('level', '')}")
            
            # 统计通过该关卡的用户数
            # 检查 completedLevels 或 passLevel 字段
            count = await user_collection.count_documents({
                "$or": [
                    {"completedLevels": level_id},
                    {"passLevel": level_id}
                ]
            })
            
            level_stats.append({
                "name": level_name,
                "count": count
            })
        
        return level_stats
    except Exception as e:
        logger.error(f"获取关卡闯关统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取关卡闯关统计失败: {str(e)}")


@router.get("/stats/prize-draw")
async def get_prize_draw_stats(current_user: dict = Depends(require_super_admin)):
    """
    获取奖品抽奖状态统计
    只统计抽中情况，不考虑核销状态
    """
    try:
        collection = await prize_manager.get_collection()
        
        # 获取所有奖品及其抽中数量
        prizes = await collection.find({}).to_list(None)
        
        prize_stats = []
        
        for prize in prizes:
            # 奖品名称字段是大写的 Name
            prize_name = prize.get("Name", prize.get("name", "未命名奖品"))
            drawn_count = prize.get("drawn_count", 0)
            
            # 只统计有抽中记录的奖品
            if drawn_count > 0:
                prize_stats.append({
                    "name": prize_name,
                    "count": drawn_count
                })
        
        return prize_stats
    except Exception as e:
        logger.error(f"获取奖品抽奖统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取奖品抽奖统计失败: {str(e)}")


@router.get("/stats/registration-timeline")
async def get_registration_timeline(current_user: dict = Depends(require_super_admin)):
    """
    获取普通用户人流量分布（按小时统计）
    仅统计2025年10月19日 8:00-18:00的数据
    """
    try:
        collection = await user_manager.get_collection()
        
        # 设置时间范围：2025年10月19日 08:00:00 到 18:00:00
        start_date = datetime(2025, 10, 19, 8, 0, 0)
        end_date = datetime(2025, 10, 19, 18, 0, 0)
        
        # 聚合查询：按小时统计注册数量
        pipeline = [
            {
                "$match": {
                    "role": "user",
                    "creatTime": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }
            },
            {
                "$project": {
                    "hour": {"$hour": "$creatTime"}
                }
            },
            {
                "$group": {
                    "_id": "$hour",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        
        result = await collection.aggregate(pipeline).to_list(None)
        
        # 构建8:00-18:00的数据（包括0人的时段）
        hourly_stats = []
        result_dict = {item["_id"]: item["count"] for item in result}
        
        for hour in range(8, 19):  # 8到18（包含18点）
            hourly_stats.append({
                "hour": hour,
                "count": result_dict.get(hour, 0)
            })
        
        return hourly_stats
    except Exception as e:
        logger.error(f"获取人流量分布失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取人流量分布失败: {str(e)}")


@router.get("/stats/overview")
async def get_dashboard_overview(current_user: dict = Depends(require_super_admin)):
    """
    获取看板总览数据
    """
    try:
        user_collection = await user_manager.get_collection()
        level_collection = await level_manager.get_collection()
        prize_collection = await prize_manager.get_collection()
        
        # 总用户数
        total_users = await user_collection.count_documents({"role": "user"})
        
        # 总关卡数（不含投票关卡）
        total_levels = await level_collection.count_documents({
            "name": {"$ne": "欢迎给我们投票!!!"}
        })
        
        # 总奖品种类数
        total_prize_types = await prize_collection.count_documents({})
        
        # 总抽奖次数
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "totalDrawn": {"$sum": "$drawn_count"}
                }
            }
        ]
        drawn_result = await prize_collection.aggregate(pipeline).to_list(1)
        total_drawn = drawn_result[0]["totalDrawn"] if drawn_result else 0
        
        return {
            "totalUsers": total_users,
            "totalLevels": total_levels,
            "totalPrizeTypes": total_prize_types,
            "totalDrawn": total_drawn
        }
    except Exception as e:
        logger.error(f"获取看板总览数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取看板总览数据失败: {str(e)}")
