"""
数据库模型定义, 基于SQLAlchemy
"""

import json

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.rdbms import Base


class Settings(Base):
    """应用配置模型"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String(50), unique=True, index=True, nullable=False)
    type = Column(String(50), nullable=False, default="string")
    value = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)  

    def __repr__(self):
        return f"<Settings {self.key}={self.value} type={self.type}>"

    def __str__(self):
        return self.value

    def get_value(self):
        if self.type == "string":
            return self.value
        elif self.type == "int":
            return int(self.value)
        elif self.type == "float":
            return float(self.value)
        elif self.type == "bool":
            return self.value.lower() == "true"
        elif self.type == "json":
            return json.loads(self.value)
        elif self.type == "list":
            return self.value.split(",")
        elif self.type == "dict":
            return json.loads(self.value)
        else:
            return self.value

