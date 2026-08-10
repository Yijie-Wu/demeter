"""
FastAPI Starter Application
"""

from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from app import create_app
from app.settings import get_settings, STATIC_DIR

settings = get_settings()

app = create_app()

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 自定义/docs路由，使用本地Swagger UI
@app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
def custom_swagger_ui(request: Request):
    swagger_html_path = os.path.join(STATIC_DIR, "swagger", "index.html")
    with open(swagger_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
