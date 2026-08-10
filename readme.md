# FastAPI Starter Template

![logo](docs/assets/logo.png)



一个功能完善的FastAPI项目模板，提供了完整的项目结构、中间件支持、自动化CRUD生成工具和Docker部署方案。

## 功能特性

- ✅ **完整的项目结构**：遵循最佳实践的代码组织方式
- ✅ **多种中间件支持**：CORS、IP速率限制、下载速率限制
- ✅ **数据库支持**：SQLite默认配置，支持PostgreSQL等其他数据库
- ✅ **自动化CRUD生成**：根据SQLAlchemy模型自动生成API、核心逻辑和数据验证代码
- ✅ **本地Swagger UI**：解决网络问题，使用本地资源提供API文档
- ✅ **Docker支持**：一键构建和部署
- ✅ **开发工具集成**：代码质量检查、测试、文档生成工具

## 技术栈

- **FastAPI**：现代化的Python Web框架
- **Pydantic**：数据验证和设置管理
- **SQLAlchemy**：ORM数据库操作
- **Loguru**：日志管理
- **Docker**：容器化部署
- **Pytest**：测试框架
- **Flake8/Black/Isort**：代码质量工具

## 快速开始

### 1. 安装依赖

```bash
# 安装运行依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 2. 运行项目

```bash
python main.py
```

项目将在 `http://0.0.0.0:8000` 启动。

### 3. 访问API文档

```bash
# 访问Swagger UI
http://localhost:8000/docs
```

## 项目结构

```
fastapi-starter/
├── app/                  # 应用主目录
│   ├── apis/            # API路由
│   ├── cores/           # 核心业务逻辑
│   ├── middlewares/     # 中间件
│   ├── schemas/         # 数据验证模型
│   ├── utils/           # 工具函数
│   ├── __init__.py      # 应用初始化
│   ├── decorators.py    # 装饰器
│   ├── models.py        # 数据库模型
│   ├── nosql.py         # NoSQL数据库配置
│   ├── rdbms.py         # 关系型数据库配置
│   └── settings.py      # 项目设置
├── data/                # 数据目录
├── logs/                # 日志目录
├── scripts/             # 脚本目录
│   ├── generated/       # 自动生成的代码
│   ├── generate-curd.py # CRUD代码生成器
│   └── data-migration.py # 数据迁移脚本
├── static/              # 静态文件
│   └── swagger/         # 本地Swagger资源
├── tests/               # 测试目录
├── .env                 # 环境变量配置
├── Dockerfile           # Docker构建文件
├── main.py              # 项目入口
├── requirements.txt     # 运行依赖
└── requirements-dev.txt # 开发依赖
```

## 配置说明

### 环境变量

在 `.env` 文件中可以配置以下环境变量：

```bash
# 应用配置
APP_NAME=FastAPI Starter
APP_VERSION=1.0.0

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///data/dev.db

# CORS配置
CORS_ORIGINS=*

# 下载速率限制
DOWNLOAD_RATE_LIMIT=1048576  # 1MB/s
```

### 多平台数据库配置

项目会根据操作系统自动调整SQLite数据库路径：
- **Windows**：自动规范化路径分隔符
- **非Windows**：使用标准路径格式

## 中间件

### CORS中间件

处理跨域资源共享请求，允许前端应用访问API：

```python
# app/middlewares/cors.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### IP速率限制中间件

限制单个IP每分钟的请求次数：

```python
# app/middlewares/rate_limit.py
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # 实现IP速率限制逻辑
```

### 下载速率限制中间件

限制文件下载的最大速率：

```python
# app/middlewares/download_rate_limit.py
@app.middleware("http")
async def download_rate_limit_middleware(request: Request, call_next):
    # 实现下载速率限制逻辑
```

## CRUD自动化生成

### 生成CRUD代码

```bash
python scripts/generate-curd.py
```

根据提示选择要生成的表，脚本将自动生成：
- API路由（`scripts/generated/apis/[表名]/api.py`）
- 核心业务逻辑（`scripts/generated/cores/[表名]/core.py`）
- 数据验证模型（`scripts/generated/schemas/[表名]/schema.py`）

### 使用生成的代码

将生成的代码复制到对应的项目目录中：

```bash
cp -r scripts/generated/apis/* app/apis/
cp -r scripts/generated/cores/* app/cores/
cp -r scripts/generated/schemas/* app/schemas/
```

## Docker部署

### 构建镜像

```bash
docker build -t fastapi-starter .
```

### 运行容器

```bash
docker run -d -p 8000:8000 --name fastapi-starter fastapi-starter
```

### 使用Docker Compose（可选）

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  fastapi-starter:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - APP_NAME=FastAPI Starter
      - DATABASE_URL=sqlite:///data/dev.db
    restart: unless-stopped
```

运行：

```bash
docker-compose up -d
```

## 开发指南

### 代码质量检查

```bash
# 运行flake8检查
flake8 app/

# 使用black格式化代码
black app/

# 使用isort排序导入
isort app/

# 运行类型检查
mypy app/
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app tests/
```

## 文档生成

使用MkDocs生成项目文档：

```bash
# 安装依赖
pip install mkdocs mkdocs-material

# 启动文档服务器
mkdocs serve

# 构建文档
mkdocs build
```

## 贡献

欢迎提交Issue和Pull Request！

### 开发流程

1. Fork项目
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'Add some feature'`
4. 推送到分支：`git push origin feature/your-feature`
5. 提交Pull Request

## 许可证

MIT License

## 联系方式

如有问题，请提交Issue或联系项目维护者。