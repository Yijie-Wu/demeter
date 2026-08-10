
"""
health API测试用例
"""

import pytest


def test_health_get(client_with_db, load_test_data, request):
    """测试GET /api/health/接口"""
    # 加载测试数据
    test_data = load_test_data(request)
    
    # 发送GET请求到/api/health/接口
    response = client_with_db.get("/api/health/")
    
    # 验证响应状态码
    assert response.status_code == 200
    
    # 验证响应内容
    if test_data:
        expected = test_data.get("expected")
        if expected:
            assert response.json() == expected
