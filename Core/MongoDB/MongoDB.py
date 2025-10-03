import asyncio
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from Core.Common.Config import Config

class MongoDB:
    _instance: Optional['MongoDB'] = None
    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.clientString = None
            self.dbName = None
            self._initialized = False
            self.load_init()
    
    def load_init(self):
        """从配置文件加载MongoDB连接参数"""
        try:
            config = Config()
            self.clientString = config.get_value('MongoDB', 'ConnectionString')
            self.dbName = config.get_value('MongoDB', 'DatabaseName')
            logging.info(f"MongoDB配置加载成功: 数据库名 = {self.dbName}")
        except Exception as e:
            logging.error(f"加载MongoDB配置失败: {e}")
            raise
    
    async def connect(self) -> bool:
        """异步连接到MongoDB"""
        async with self._lock:
            if self._client is not None and self._initialized:
                return True
                
            try:
                # 创建异步客户端
                self._client = AsyncIOMotorClient(
                    self.clientString,
                    serverSelectionTimeoutMS=5000,  # 5秒超时
                    connectTimeoutMS=10000,         # 10秒连接超时
                    socketTimeoutMS=0,              # 无限制socket超时
                    maxPoolSize=10,                 # 最大连接池大小
                    minPoolSize=5,                 # 最小连接池大小
                    maxIdleTimeMS=30000            # 连接最大空闲时间
                )
                
                # 测试连接
                await self._client.admin.command('ping')
                
                # 获取数据库实例
                self._database = self._client[self.dbName]
                
                self._initialized = True
                logging.info("MongoDB连接成功")
                return True
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logging.error(f"MongoDB连接失败: {e}")
                await self.disconnect()
                return False
            except Exception as e:
                logging.error(f"MongoDB连接时发生未知错误: {e}")
                await self.disconnect()
                return False
    
    async def disconnect(self):
        """断开MongoDB连接"""
        async with self._lock:
            if self._client:
                self._client.close()
                self._client = None
                self._database = None
                self._initialized = False
                logging.info("MongoDB连接已断开")

# 全局MongoDB实例
mongodb_instance = MongoDB()

async def get_mongodb_database() -> AsyncIOMotorDatabase:
    """获取MongoDB数据库实例"""
    db = mongodb_instance
    if not await db.connect():
        raise ConnectionError("MongoDB连接失败")
    return db._database
