"""
关系型数据库配置与初始化
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.settings import get_settings

settings = get_settings()

# 创建SQLAlchemy引擎
engine = create_engine(
    settings.build_database_url,  # 默认使用SQLite
    connect_args={"check_same_thread": False} if settings.DATABASE_URL is None else {}
)

# 创建SessionLocal类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()


# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_sync() -> SessionLocal:
    return SessionLocal()

