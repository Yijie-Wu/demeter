from loguru import logger
from fastapi import FastAPI
from app.settings import settings
from sqlalchemy import text

from app.apis import router
from app.rdbms import get_db, engine
from app.middlewares import setup_cors, rate_limit_middleware, download_rate_limit_middleware


def create_app() -> FastAPI:
    # 创建FastAPI应用，禁用默认的Swagger UI
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        docs_url=None,  # 禁用默认的docs路径
        redoc_url=None,  # 禁用redoc路径
        openapi_url="/openapi.json"  # 保持openapi.json可用
    )

    # 初始化数据库
    init_db()
    register_routes(app)
    register_middlewares(app)
    register_logging()

    return app


def register_routes(app: FastAPI):
    app.include_router(router, prefix=settings.GLOBAL_PREFIX)


def register_middlewares(app: FastAPI):
    # 设置CORS中间件
    setup_cors(app)
    # 添加速率限制中间件
    app.middleware("http")(rate_limit_middleware)
    # 添加下载速率限制中间件
    app.middleware("http")(download_rate_limit_middleware)


def init_db():
    """
    初始化数据库, 判断数据库中的表和表结构，如果表已经存在，但是表结构有变化，
    则删除所有表，重新创建。否则，保持数据库中的表结构不变。如果数据库中没有表，
    则根据模型类创建表。
    """
    # 检查数据库是否存在表
    db = next(get_db())  # 获取数据库会话
    # 检查数据库是否存在表
    result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
    tables = result.fetchall()
    if tables:
        # 数据库存在表，检查表结构是否有变化
        result = db.execute(text("PRAGMA table_info('user');"))
        columns = result.fetchall()
        if columns:
            # 表结构有变化，删除所有表，重新创建
            db.execute(text("DROP TABLE IF EXISTS user;"))
            db.commit()
            # 根据模型类创建表
            from app.models import Settings
            Settings.__table__.create(bind=engine)
            db.commit()
    else:
        # 数据库不存在表，根据模型类创建表
        from app.models import Settings
        Settings.__table__.create(bind=engine)
        db.commit()


def register_logging():
    # 移除默认的日志输出
    logger.remove()
    # 添加日志文件输出，设置日志级别为INFO，文件大小为50MB，保留3个备份文件
    logger.add(
        settings.LOG_FILE_PATH, 
        rotation=settings.LOG_ROTATION, 
        level=settings.LOG_LEVEL, 
        retention=settings.LOG_RETENTION, 
        encoding=settings.LOG_ENCODING, 
        format=settings.LOG_FORMAT)