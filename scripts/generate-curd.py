#!/usr/bin/env python3
"""
自动化生成CRUD API脚本
根据models.py中的SQLAlchemy模型生成API、Core和Schema文件
"""

import os
import sys
import importlib.util
import inspect
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_models():
    """加载models.py文件并返回所有SQLAlchemy模型类"""
    try:
        # 获取models.py文件路径
        models_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "models.py")
        
        # 导入SQLAlchemy相关模块
        from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
        from sqlalchemy.orm import relationship
        from sqlalchemy.ext.declarative import declarative_base
        
        # 创建临时的Base类
        Base = declarative_base()
        
        # 设置global_vars，确保app和app.rdbms等模块不会被真正导入
        global_vars = {
            '__file__': models_path,
            '__name__': 'app.models',
            '__package__': 'app',
            
            # 直接导入SQLAlchemy相关模块
            'Column': Column,
            'Integer': Integer,
            'String': String,
            'DateTime': DateTime,
            'ForeignKey': ForeignKey,
            'Text': Text,
            'relationship': relationship,
            'func': func,
            'Base': Base,
        }
        
        # 执行models.py文件，但不导入app模块，直接使用我们提供的Base
        with open(models_path, 'r', encoding='utf-8') as f:
            models_content = f.read()
            
            # 替换models.py中的导入语句，直接使用我们提供的Base
            modified_content = models_content.replace('from app.rdbms import Base', '')
            
            # 执行修改后的内容
            exec(modified_content, global_vars)
        
        # 获取所有SQLAlchemy模型类
        model_classes = []
        for name, obj in global_vars.items():
            if isinstance(obj, type) and issubclass(obj, Base) and obj != Base:
                model_classes.append(obj)
        
        return model_classes
    except Exception as e:
        print(f"加载模型失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_table_columns(model_class) -> List[Dict[str, Any]]:
    """获取模型的所有列信息"""
    from sqlalchemy import inspect as sa_inspect
    mapper = sa_inspect(model_class)
    columns = []
    
    for column in mapper.columns:
        # 获取列的Python类型
        python_type = column.type.python_type
        
        # 转换为Pydantic类型
        pydantic_type = "Any"
        if python_type == str:
            pydantic_type = "str"
        elif python_type == int:
            pydantic_type = "int"
        elif python_type == float:
            pydantic_type = "float"
        elif python_type == bool:
            pydantic_type = "bool"
        elif python_type == datetime:
            pydantic_type = "datetime.datetime"
        
        columns.append({
            "name": column.name,
            "type": pydantic_type,
            "python_type": python_type,
            "nullable": column.nullable,
            "primary_key": column.primary_key,
            "default": column.default,
            "autoincrement": column.autoincrement if hasattr(column, 'autoincrement') else False
        })
    
    return columns

def snake_case_to_camel_case(text: str) -> str:
    """将蛇形命名转换为驼峰命名"""
    return ''.join(word.title() for word in text.split('_'))

def snake_case_to_pascal_case(text: str) -> str:
    """将蛇形命名转换为帕斯卡命名"""
    return text.title().replace('_', '')

def generate_schema_file(model_class, columns: List[Dict[str, Any]], output_dir: str):
    """生成schema.py文件"""
    table_name = model_class.__tablename__
    model_name = model_class.__name__
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成导入语句
    imports = [
        "from pydantic import BaseModel, Field",
        "from typing import Optional, List",
        "from datetime import datetime"
    ]
    
    # 收集需要的导入类型
    used_types = set()
    for col in columns:
        if col["type"] not in used_types:
            used_types.add(col["type"])
    
    # 生成CreateSchema
    create_fields = []
    for col in columns:
        if not col["primary_key"] and not col["autoincrement"]:
            field_line = f"    {col['name']}: Optional[{col['type']}] = Field(None, description='{col['name']}')"
            if not col["nullable"]:
                field_line = field_line.replace("Optional[", "").replace("]", "").replace("= Field(None", "= Field(...")
            create_fields.append(field_line)
    
    # 生成UpdateSchema
    update_fields = []
    for col in columns:
        if not col["primary_key"]:
            update_fields.append(f"    {col['name']}: Optional[{col['type']}] = Field(None, description='{col['name']}')")
    
    # 生成ResponseSchema
    response_fields = []
    for col in columns:
        response_fields.append(f"    {col['name']}: Optional[{col['type']}] = Field(None, description='{col['name']}')")
    
    # 生成文件内容
    content = "\n".join(imports) + "\n\n"
    
    # Create Schema
    content += f"class {model_name}Create(BaseModel):\n"
    content += "    \"\"\"创建{}的请求模式\"\"\"\n".format(model_name)
    content += "\n".join(create_fields) + "\n\n"
    
    # Update Schema
    content += f"class {model_name}Update(BaseModel):\n"
    content += "    \"\"\"更新{}的请求模式\"\"\"\n".format(model_name)
    content += "\n".join(update_fields) + "\n\n"
    
    # Response Schema
    content += f"class {model_name}Response(BaseModel):\n"
    content += "    \"\"\"{}的响应模式\"\"\"\n".format(model_name)
    content += "\n".join(response_fields) + "\n\n"
    content += "    class Config:\n"
    content += "        orm_mode = True\n"
    
    # List Response Schema
    content += f"\nclass {model_name}ListResponse(BaseModel):\n"
    content += "    \"\"\"{}列表的响应模式\"\"\"\n".format(model_name)
    content += f"    items: List[{model_name}Response]\n"
    content += "    total: int\n"
    content += "    page: int\n"
    content += "    page_size: int\n"
    
    # 写入文件
    with open(os.path.join(output_dir, "schema.py"), "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✓ 生成Schema文件: {os.path.join(output_dir, 'schema.py')}")

def generate_core_file(model_class, columns: List[Dict[str, Any]], output_dir: str):
    """生成core.py文件"""
    table_name = model_class.__tablename__
    model_name = model_class.__name__
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取主键列
    primary_key_col = next(col for col in columns if col["primary_key"])
    
    # 生成文件内容
    content = """
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import models
"""
    
    content += f"from app.schemas.{table_name} import schema as {table_name}_schema\n\n"
    
    # Create function
    content += f"def create_{table_name}(db: Session, obj_in: {table_name}_schema.{model_name}Create) -> models.{model_name}:\n"
    content += f"    \"\"\"创建{model_name}记录\"\"\"\n"
    content += f"    obj_data = obj_in.dict(exclude_unset=True)\n"
    content += f"    db_obj = models.{model_name}(**obj_data)\n"
    content += f"    db.add(db_obj)\n"
    content += f"    db.commit()\n"
    content += f"    db.refresh(db_obj)\n"
    content += f"    return db_obj\n\n"
    
    # Get function
    content += f"def get_{table_name}(db: Session, {primary_key_col['name']}: {primary_key_col['type']}) -> Optional[models.{model_name}]:\n"
    content += f"    \"\"\"根据ID获取{model_name}记录\"\"\"\n"
    content += f"    return db.query(models.{model_name}).filter(models.{model_name}.{primary_key_col['name']} == {primary_key_col['name']}).first()\n\n"
    
    # Get all function
    content += f"def get_{table_name}_list(\n"
    content += f"    db: Session, skip: int = 0, limit: int = 100\n"
    content += f") -> List[models.{model_name}]:\n"
    content += f"    \"\"\"获取{model_name}记录列表\"\"\"\n"
    content += f"    return db.query(models.{model_name}).offset(skip).limit(limit).all()\n\n"
    
    # Update function
    content += f"def update_{table_name}(\n"
    content += f"    db: Session, db_obj: models.{model_name}, obj_in: {table_name}_schema.{model_name}Update\n"
    content += f") -> models.{model_name}:\n"
    content += f"    \"\"\"更新{model_name}记录\"\"\"\n"
    content += f"    obj_data = obj_in.dict(exclude_unset=True)\n"
    content += f"    for field, value in obj_data.items():\n"
    content += f"        setattr(db_obj, field, value)\n"
    content += f"    db.add(db_obj)\n"
    content += f"    db.commit()\n"
    content += f"    db.refresh(db_obj)\n"
    content += f"    return db_obj\n\n"
    
    # Delete function
    content += f"def delete_{table_name}(db: Session, {primary_key_col['name']}: {primary_key_col['type']}) -> bool:\n"
    content += f"    \"\"\"删除{model_name}记录\"\"\"\n"
    content += f"    db_obj = get_{table_name}(db, {primary_key_col['name']})\n"
    content += f"    if not db_obj:\n"
    content += f"        return False\n"
    content += f"    db.delete(db_obj)\n"
    content += f"    db.commit()\n"
    content += f"    return True\n\n"
    
    # Get total count function
    content += f"def get_{table_name}_total_count(db: Session) -> int:\n"
    content += f"    \"\"\"获取{model_name}记录总数\"\"\"\n"
    content += f"    return db.query(models.{model_name}).count()\n"
    
    # 写入文件
    with open(os.path.join(output_dir, "core.py"), "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✓ 生成Core文件: {os.path.join(output_dir, 'core.py')}")

def generate_api_file(model_class, columns: List[Dict[str, Any]], output_dir: str):
    """生成api.py文件"""
    table_name = model_class.__tablename__
    model_name = model_class.__name__
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取主键列
    primary_key_col = next(col for col in columns if col["primary_key"])
    
    # 生成文件内容
    content = """
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app import get_db
"""
    
    content += f"from app.schemas.{table_name} import schema as {table_name}_schema\n"
    content += f"from app.cores.{table_name} import core as {table_name}_core\n\n"
    
    content += f"router = APIRouter(prefix='/api/{table_name}', tags=['{model_name}'])\n\n"
    
    # Create API
    content += f"@router.post('/', response_model={table_name}_schema.{model_name}Response)\n"
    content += f"def create_{table_name}(\n"
    content += f"    obj_in: {table_name}_schema.{model_name}Create,\n"
    content += f"    db: Session = Depends(get_db)\n"
    content += f"):\n"
    content += f"    \"\"\"创建{model_name}记录\"\"\"\n"
    content += f"    return {table_name}_core.create_{table_name}(db=db, obj_in=obj_in)\n\n"
    
    # Get API
    content += f"@router.get('/{{{primary_key_col['name']}}}', response_model={table_name}_schema.{model_name}Response)\n"
    content += f"def get_{table_name}(\n"
    content += f"    {primary_key_col['name']}: {primary_key_col['type']},\n"
    content += f"    db: Session = Depends(get_db)\n"
    content += f"):\n"
    content += f"    \"\"\"获取{model_name}记录\"\"\"\n"
    content += f"    db_obj = {table_name}_core.get_{table_name}(db=db, {primary_key_col['name']}={primary_key_col['name']})\n"
    content += f"    if not db_obj:\n"
    content += f"        raise HTTPException(status_code=404, detail='{model_name} not found')\n"
    content += f"    return db_obj\n\n"
    
    # Get list API
    content += f"@router.get('/', response_model={table_name}_schema.{model_name}ListResponse)\n"
    content += f"def get_{table_name}_list(\n"
    content += f"    page: int = Query(1, ge=1, description='页码'),\n"
    content += f"    page_size: int = Query(10, ge=1, le=100, description='每页条数'),\n"
    content += f"    db: Session = Depends(get_db)\n"
    content += f"):\n"
    content += f"    \"\"\"获取{model_name}记录列表\"\"\"\n"
    content += f"    skip = (page - 1) * page_size\n"
    content += f"    items = {table_name}_core.get_{table_name}_list(db=db, skip=skip, limit=page_size)\n"
    content += f"    total = {table_name}_core.get_{table_name}_total_count(db=db)\n"
    content += f"    return {{\n"
    content += f"        'items': items,\n"
    content += f"        'total': total,\n"
    content += f"        'page': page,\n"
    content += f"        'page_size': page_size\n"
    content += f"    }}\n\n"
    
    # Update API
    content += f"@router.put('/{{{primary_key_col['name']}}}', response_model={table_name}_schema.{model_name}Response)\n"
    content += f"def update_{table_name}(\n"
    content += f"    {primary_key_col['name']}: {primary_key_col['type']},\n"
    content += f"    obj_in: {table_name}_schema.{model_name}Update,\n"
    content += f"    db: Session = Depends(get_db)\n"
    content += f"):\n"
    content += f"    \"\"\"更新{model_name}记录\"\"\"\n"
    content += f"    db_obj = {table_name}_core.get_{table_name}(db=db, {primary_key_col['name']}={primary_key_col['name']})\n"
    content += f"    if not db_obj:\n"
    content += f"        raise HTTPException(status_code=404, detail='{model_name} not found')\n"
    content += f"    return {table_name}_core.update_{table_name}(db=db, db_obj=db_obj, obj_in=obj_in)\n\n"
    
    # Delete API
    content += f"@router.delete('/{{{primary_key_col['name']}}}', response_model=dict)\n"
    content += f"def delete_{table_name}(\n"
    content += f"    {primary_key_col['name']}: {primary_key_col['type']},\n"
    content += f"    db: Session = Depends(get_db)\n"
    content += f"):\n"
    content += f"    \"\"\"删除{model_name}记录\"\"\"\n"
    content += f"    success = {table_name}_core.delete_{table_name}(db=db, {primary_key_col['name']}={primary_key_col['name']})\n"
    content += f"    if not success:\n"
    content += f"        raise HTTPException(status_code=404, detail='{model_name} not found')\n"
    content += f"    return {{'message': '{model_name} deleted successfully'}}\n"
    
    # 写入文件
    with open(os.path.join(output_dir, "api.py"), "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✓ 生成API文件: {os.path.join(output_dir, 'api.py')}")

def update_apis_init(model_class, base_dir: str):
    """更新apis/__init__.py文件，导入新生成的API"""
    table_name = model_class.__tablename__
    
    init_file_path = os.path.join(base_dir, "__init__.py")
    
    # 读取现有内容
    if os.path.exists(init_file_path):
        with open(init_file_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = ""
    
    # 检查是否已导入
    import_line = f"from .{table_name}.api import router as {table_name}_router"
    include_line = f"router.include_router({table_name}_router)"
    
    # 如果还没有导入语句，添加到文件开头
    if import_line not in content:
        # 添加导入
        if content.strip():
            content = import_line + "\n" + content
        else:
            content = import_line + "\n"
        
        # 添加FastAPI导入（如果需要）
        if "from fastapi import APIRouter" not in content:
            content = "from fastapi import APIRouter\n" + content
        
        # 添加主router定义（如果需要）
        if "router = APIRouter()" not in content:
            content = "router = APIRouter()\n" + content
    
    # 如果还没有包含router，添加到文件末尾
    if include_line not in content:
        content += "\n" + include_line
    
    # 写入更新后的内容
    with open(init_file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✓ 更新apis/__init__.py文件")

def main():
    """主函数"""
    print("=" * 50)
    print("        自动化CRUD API生成工具")
    print("=" * 50)
    
    # 加载模型
    models = load_models()
    
    if not models:
        print("未找到任何SQLAlchemy模型，请先在models.py中定义模型")
        return
    
    # 显示可用的模型
    print("\n可用的数据表模型：")
    for i, model in enumerate(models, 1):
        print(f"{i}. {model.__name__} ({model.__tablename__})")
    
    # 让用户选择模型
    while True:
        try:
            choice = input("\n请输入要生成CRUD的模型编号 (0退出): ")
            if choice == "0":
                print("\n操作已取消")
                return
            
            index = int(choice) - 1
            if 0 <= index < len(models):
                selected_model = models[index]
                break
            else:
                print("无效的选择，请重新输入")
        except ValueError:
            print("请输入有效的数字")
    
    print(f"\n开始生成 {selected_model.__name__} 的CRUD API...")
    
    # 获取模型列信息
    columns = get_table_columns(selected_model)
    
    # 项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 生成Schema文件
    schema_dir = os.path.join(project_root, "scripts", "generated", "schemas", selected_model.__tablename__)
    generate_schema_file(selected_model, columns, schema_dir)
    
    # 生成Core文件
    core_dir = os.path.join(project_root, "scripts", "generated", "cores", selected_model.__tablename__)
    generate_core_file(selected_model, columns, core_dir)
    
    # 生成API文件
    api_dir = os.path.join(project_root, "scripts", "generated", "apis", selected_model.__tablename__)
    generate_api_file(selected_model, columns, api_dir)
    
    print(f"\n{selected_model.__name__} 的CRUD API生成完成！")
    print("\n生成的文件：")
    print(f"- Schema: {os.path.join(schema_dir, 'schema.py')}")
    print(f"- Core: {os.path.join(core_dir, 'core.py')}")
    print(f"- API: {os.path.join(api_dir, 'api.py')}")
    print("\n使用说明：")
    print("1. 检查生成的文件内容")
    print("2. 按需将需要的文件移动到app目录下的对应位置")
    print("3. 如果移动API文件，需要在app/apis/__init__.py中注册路由")
    print("4. 启动服务后，可通过 /api/{table_name} 访问API")

if __name__ == "__main__":
    main()