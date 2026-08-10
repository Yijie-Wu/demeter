import asyncio
from typing import Optional, Callable
from fastapi import Request, Response
from starlette.responses import StreamingResponse, Response
from app.settings import settings

async def download_rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """下载速率限制中间件"""
    response = await call_next(request)
    
    # 检查是否是文件下载响应
    if (response.headers.get("content-disposition") and 
        "attachment" in response.headers["content-disposition"]):
        
        # 如果是StreamingResponse，直接包装流
        if isinstance(response, StreamingResponse):
            original_stream = response.body_iterator
            
            async def rate_limited_stream():
                async for chunk in original_stream:
                    yield chunk
                    # 计算延迟时间 (秒)
                    chunk_size = len(chunk)
                    if settings.DOWNLOAD_RATE_LIMIT > 0:
                        delay = chunk_size / settings.DOWNLOAD_RATE_LIMIT
                        await asyncio.sleep(delay)
            
            return StreamingResponse(
                content=rate_limited_stream(),
                status_code=response.status_code,
                headers=response.headers,
                media_type=response.media_type
            )
        
        # 如果是普通Response，转换为StreamingResponse
        else:
            content = response.body
            
            async def rate_limited_stream():
                chunk_size = settings.DOWNLOAD_CHUNK_SIZE
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i+chunk_size]
                    yield chunk
                    # 计算延迟时间 (秒)
                    if settings.DOWNLOAD_RATE_LIMIT > 0:
                        delay = len(chunk) / settings.DOWNLOAD_RATE_LIMIT
                        await asyncio.sleep(delay)
            
            return StreamingResponse(
                content=rate_limited_stream(),
                status_code=response.status_code,
                headers=response.headers,
                media_type=response.media_type
            )
    
    # 非下载响应，直接返回
    return response