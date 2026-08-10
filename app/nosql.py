# redis
from redis import Redis
from pymongo import MongoClient
from app.settings import get_settings

settings = get_settings()


# 依赖项：获取Redis连接
def get_redis() -> Redis:
    redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
    )
    yield redis
    redis.close()


# 依赖项：获取MongoDB连接
def get_mongo() -> MongoClient:
    mongo = MongoClient(
        host=settings.MONGO_HOST,
        port=settings.MONGO_PORT,
    )
    yield mongo
    mongo.close()



def get_redis_sync() -> Redis:
    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
    )

def get_mongo_sync() -> MongoClient:
    return MongoClient(
        host=settings.MONGO_HOST,
        port=settings.MONGO_PORT,
    )

