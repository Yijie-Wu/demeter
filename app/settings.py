import os
from functools import lru_cache
from typing import Optional, ClassVar

from pydantic_settings import BaseSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 文件夹配置
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")
STATIC_DIR = os.path.join(BASE_DIR, "static")
SWAGGER_STATIC_DIR = os.path.join(STATIC_DIR, "swagger")
# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 根据操作系统配置不同的SQLite路径
if os.name == 'nt':  # Windows系统
    DB_FILE_PATH = os.path.join(DATA_DIR, "dev.db")
    # Windows路径需要将反斜杠转换为正斜杠，使用3个斜杠格式
    db_path_normalized = DB_FILE_PATH.replace('\\', '/')
    DATABASE_URL = f"sqlite:///{db_path_normalized}"
else:  # 非Windows系统
    DB_FILE_PATH = os.path.join(DATA_DIR, "dev.db")
    DATABASE_URL = f"sqlite:///{DB_FILE_PATH}"  # Unix/Linux使用3个斜杠格式


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "FastAPI Starter"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "A basic FastAPI application template"

    DEBUG: bool = True
    GLOBAL_PREFIX: str = "/demeter"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8500
    
    # 数据库配置
    DATABASE_ENGINE: str = "postgresql+asyncpg"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "postgres"
    DATABASE_NAME: str = "fastapi_starter"

    # 数据库文件路径（类变量，不会被Pydantic验证）
    DB_FILE_PATH: ClassVar[str] = DB_FILE_PATH
    DATABASE_URL: Optional[str] = DATABASE_URL

    # 构建数据库URL
    @property
    def build_database_url(self) -> str:
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"{self.DATABASE_ENGINE}://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        return self.DATABASE_URL


    # 日志配置
    LOG_FILE_PATH: str = os.path.join(LOG_DIR, "app.log")
    LOG_LEVEL: str = "INFO"
    LOG_ROTATION: str = "50 MB"
    LOG_RETENTION: str = "3 days"
    LOG_ENCODING: str = "utf-8"
    LOG_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"


    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # MongoDB配置
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    
    # CORS配置
    CORS_ORIGINS: list[str] = ["*"]
    
    # 下载速率限制配置
    DOWNLOAD_RATE_LIMIT: int = 1024 * 1024  # 默认1MB/s
    DOWNLOAD_CHUNK_SIZE: int = 8192  # 8KB chunks
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# 创建一个全局的settings实例
settings = get_settings()