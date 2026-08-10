#!/usr/bin/env python3
"""
API测试用例生成工具

该工具可以：
1. 自动发现项目中的所有API端点
2. 让用户选择要生成测试的API
3. 生成对应的测试用例文件和测试数据文件
4. 处理已存在文件的覆盖/跳过逻辑
"""

import os
import sys
import importlib
import argparse
from typing import Dict, List, Tuple, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from fastapi import FastAPI
from fastapi.routing import APIRoute


def get_all_routes(app: FastAPI) -> List[Tuple[str, str, APIRoute]]:
    """
    获取应用中的所有路由
    
    Args:
        app: FastAPI应用实例
        
    Returns:
        路由列表，每个元素为(method, path, route)的元组
    """
    routes = []
    
    def get_routes(router, prefix=""):
        for route in router.routes:
            if hasattr(route, "include_router"):
                # 处理嵌套路由
                get_routes(route, prefix + route.prefix)
            elif isinstance(route, APIRoute):
                # 处理单个路由
                for method in route.methods:
                    routes.append((method, prefix + route.path, route))
    
    # 从主应用开始获取路由
    for route in app.router.routes:
        if hasattr(route, "include_router"):
            get_routes(route, route.prefix)
        elif isinstance(route, APIRoute):
            for method in route.methods:
                routes.append((method, route.path, route))
    
    return routes


def generate_test_case(api_name: str, method: str, path: str) -> str:
    """
    生成测试用例代码
    
    Args:
        api_name: API名称
        method: HTTP方法
        path: API路径
        
    Returns:
        测试用例代码字符串
    """
    test_function_name = f"test_{api_name}_{method.lower()}"
    
    test_code = f'''
def {test_function_name}(client_with_db, load_test_data, request):
    """测试{method} {path}接口"""
    # 加载测试数据
    test_data = load_test_data(request)
    
    # 发送{method}请求到{path}接口
    response = client_with_db.{method.lower()}("{path}")
    
    # 验证响应状态码
    assert response.status_code == 200
    
    # 验证响应内容
    if test_data:
        expected = test_data.get("expected")
        if expected:
            assert response.json() == expected
'''
    
    return test_code


def generate_test_data(api_name: str, method: str, path: str) -> Dict[str, Any]:
    """
    生成测试数据
    
    Args:
        api_name: API名称
        method: HTTP方法
        path: API路径
        
    Returns:
        测试数据字典
    """
    # 根据API名称生成合适的默认响应数据
    default_response = {}
    if api_name == "health":
        default_response = {"status": "healthy"}
    
    return {
        "description": f"{api_name} API {method}请求测试数据",
        "request": {
            "method": method,
            "path": path
        },
        "expected": default_response
    }


def write_test_case(file_path: str, content: str, force: bool = False) -> bool:
    """
    写入测试用例文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
        force: 是否强制覆盖
        
    Returns:
        是否成功写入
    """
    if os.path.exists(file_path):
        if not force:
            choice = input(f"测试用例文件 {file_path} 已存在，是否覆盖？(y/n): ")
            if choice.lower() != 'y':
                print(f"跳过 {file_path}")
                return False
        print(f"覆盖 {file_path}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"创建测试用例文件: {file_path}")
    return True


def write_test_data(file_path: str, data: Dict[str, Any], force: bool = False) -> bool:
    """
    写入测试数据文件
    
    Args:
        file_path: 文件路径
        data: 测试数据
        force: 是否强制覆盖
        
    Returns:
        是否成功写入
    """
    import json
    
    if os.path.exists(file_path):
        if not force:
            choice = input(f"测试数据文件 {file_path} 已存在，是否覆盖？(y/n): ")
            if choice.lower() != 'y':
                print(f"跳过 {file_path}")
                return False
        print(f"覆盖 {file_path}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"创建测试数据文件: {file_path}")
    return True


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="API测试用例生成工具")
    parser.add_argument("-f", "--force", action="store_true", help="强制覆盖已存在的文件")
    args = parser.parse_args()
    
    # 创建FastAPI应用实例
    print("正在加载FastAPI应用...")
    app = create_app()
    
    # 获取所有路由
    print("正在获取所有API路由...")
    routes = get_all_routes(app)
    
    if not routes:
        print("未找到任何API路由")
        return
    
    # 按API分组路由
    api_groups: Dict[str, List[Tuple[str, str, APIRoute]]] = {}
    for method, path, route in routes:
        # 从路径中提取API名称（例如：/api/health -> health）
        api_path_parts = [p for p in path.split("/") if p and not p.startswith(":")]
        api_name = api_path_parts[-1] if api_path_parts else "root"
        
        if api_name not in api_groups:
            api_groups[api_name] = []
        api_groups[api_name].append((method, path, route))
    
    # 显示API列表供用户选择
    print("\n可用的API列表：")
    print("=" * 50)
    for i, (api_name, api_routes) in enumerate(api_groups.items(), 1):
        methods = {method for method, _, _ in api_routes}
        print(f"{i}. {api_name} ({', '.join(methods)})")
    print("=" * 50)
    
    # 用户选择API
    while True:
        try:
            choice = input("\n请选择要生成测试的API编号（多个编号用逗号分隔，输入'all'生成所有API测试）: ")
            
            if choice.lower() == 'all':
                selected_api_names = list(api_groups.keys())
                break
            
            selected_indices = [int(idx.strip()) - 1 for idx in choice.split(",")]
            selected_api_names = [list(api_groups.keys())[i] for i in selected_indices if 0 <= i < len(api_groups)]
            
            if selected_api_names:
                break
            else:
                print("无效的选择，请重新输入")
        except (ValueError, IndexError):
            print("无效的输入，请输入有效的数字或'all'")
    
    # 生成测试用例和测试数据
    print("\n正在生成测试用例和测试数据...")
    
    # 确保测试目录存在
    testcases_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "testcases")
    testdatas_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "testdatas")
    
    os.makedirs(testcases_dir, exist_ok=True)
    os.makedirs(testdatas_dir, exist_ok=True)
    
    for api_name in selected_api_names:
        api_routes = api_groups[api_name]
        
        # 生成测试用例文件
        test_file_name = f"test_{api_name}.py"
        test_file_path = os.path.join(testcases_dir, test_file_name)
        
        # 收集所有路由的测试函数
        test_functions = []
        for method, path, route in api_routes:
            test_function = generate_test_case(api_name, method, path)
            test_functions.append(test_function)
        
        # 合并所有测试函数
        test_content = f'''
"""
{api_name} API测试用例
"""

import pytest

'''
        test_content += "\n".join(test_functions)
        
        # 写入测试用例文件
        if write_test_case(test_file_path, test_content, args.force):
            # 为每个测试函数生成对应的测试数据文件
            for method, path, route in api_routes:
                test_function_name = f"test_{api_name}_{method.lower()}"
                test_data_file_name = f"{test_file_name[:-3]}_{test_function_name}.json"
                test_data_file_path = os.path.join(testdatas_dir, test_data_file_name)
                
                test_data = generate_test_data(api_name, method, path)
                write_test_data(test_data_file_path, test_data, args.force)
    
    print("\n测试用例和测试数据生成完成！")
    print(f"测试用例文件位于: {testcases_dir}")
    print(f"测试数据文件位于: {testdatas_dir}")


if __name__ == "__main__":
    main()
