"""
测试夹具配置文件
提供FastAPI测试所需的各种夹具
"""

import os
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import create_app
from app.rdbms import Base, get_db
from app.settings import get_settings


@pytest.fixture(scope="session")
def test_settings():
    """获取测试配置"""
    return get_settings()


@pytest.fixture(scope="session")
def test_app():
    """创建测试应用实例"""
    app = create_app()
    yield app


@pytest.fixture(scope="session")
def test_client(test_app):
    """创建FastAPI测试客户端"""
    with TestClient(test_app) as client:
        yield client


@pytest.fixture(scope="session")
def test_db_engine(test_settings):
    """创建测试数据库引擎"""
    # 使用内存数据库进行测试
    engine = create_engine("sqlite:///:memory:")
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    yield engine
    # 测试结束后清理
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_db_engine):
    """创建测试数据库会话"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def override_get_db(test_db, test_app):
    """覆盖默认的数据库依赖，使用测试数据库"""
    def _override_get_db():
        try:
            yield test_db
        finally:
            pass

    test_app.dependency_overrides[get_db] = _override_get_db
    yield
    # 移除覆盖
    test_app.dependency_overrides.pop(get_db)


@pytest.fixture(scope="function")
def client_with_db(test_client, override_get_db):
    """带测试数据库的客户端"""
    yield test_client


@pytest.fixture(scope="function")
def load_test_data():
    """
    加载测试数据的夹具
    根据测试用例名称自动加载对应的测试数据文件
    """
    def _load_test_data(request):
        # 获取测试用例的模块名和函数名
        module_name = request.module.__name__.split(".")[-1]
        function_name = request.function.__name__
        
        # 构建测试数据文件路径
        data_file_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "tests",
            "testdatas",
            f"{module_name}_{function_name}.json"
        )
        
        # 如果测试数据文件存在，则加载数据
        if os.path.exists(data_file_path):
            with open(data_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    return _load_test_data
