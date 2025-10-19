"""
应用配置模块
包含FastAPI应用创建、数据库连接、中间件配置等
"""
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from Core.User.User import User
from Core.User.Session import session_manager
from Core.User.Permission import Permission
from Core.Prize.Prize import Prize
from Core.Level.Level import Level
from Core.Common.SystemSettings import system_settings
from Core.MongoDB.MongoDB import mongodb_instance

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 实例化各个管理器
user_manager = User()
prize_manager = Prize()
level_manager = Level()

def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title="NISA Welcome System",
        description="NISA社团迎新系统API",
        version="1.0.0",
    )
    
    # 静态文件托管
    app.mount("/Pages", StaticFiles(directory="Pages"), name="pages")
    app.mount("/Assest", StaticFiles(directory="Assest"), name="assets")
    
    # 启动事件：初始化默认奖品
    @app.on_event("startup")
    async def startup_event():
        """应用启动时执行的初始化任务"""
        logger.info("正在初始化系统...")
        try:
            # 确保默认奖品存在
            await prize_manager.ensure_default_prize()
            logger.info("默认奖品初始化完成")
        except Exception as e:
            logger.error(f"初始化默认奖品失败: {e}")
    
    return app

def setup_routes(app: FastAPI):
    """设置应用路由"""
    from api import auth_router, members_router, levels_router, prizes_router
    from api.routes.prizes import lottery_router
    from api.routes.dashboard import router as dashboard_router
    
    # 注册API路由
    app.include_router(auth_router, tags=["认证"])
    app.include_router(members_router, tags=["成员管理"])
    app.include_router(levels_router, tags=["关卡管理"])
    app.include_router(prizes_router, tags=["奖品管理"])
    app.include_router(lottery_router, tags=["抽奖配置"])
    app.include_router(dashboard_router, tags=["汇总看板"])

def get_managers():
    """获取管理器实例"""
    return {
        "user_manager": user_manager,
        "prize_manager": prize_manager,
        "level_manager": level_manager,
        "session_manager": session_manager,
        "system_settings": system_settings,
        "mongo_manager": mongodb_instance
    }