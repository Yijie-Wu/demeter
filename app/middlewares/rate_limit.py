import time
from typing import Dict, Tuple
from fastapi import Request, Response
from fastapi.responses import JSONResponse

# 存储IP地址和请求时间戳的字典
# 格式: {ip_address: (count, last_reset_time)}
rate_limits: Dict[str, Tuple[int, float]] = {}

# 配置: 每分钟允许的最大请求数
MAX_REQUESTS_PER_MINUTE = 60

def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    # 检查X-Forwarded-For头（如果在代理后面）
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    # 直接从请求中获取IP
    return request.client.host

async def rate_limit_middleware(request: Request, call_next):
    """IP速率限制中间件"""
    client_ip = get_client_ip(request)
    current_time = time.time()
    
    # 检查IP是否在速率限制字典中
    if client_ip in rate_limits:
        request_count, last_reset = rate_limits[client_ip]
        
        # 如果已经过了一分钟，重置计数器
        if current_time - last_reset >= 60:
            rate_limits[client_ip] = (1, current_time)
        else:
            # 检查是否超过限制
            if request_count >= MAX_REQUESTS_PER_MINUTE:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Too Many Requests",
                        "detail": f"Rate limit exceeded. Try again after {int(60 - (current_time - last_reset))} seconds."
                    }
                )
            # 增加请求计数
            rate_limits[client_ip] = (request_count + 1, last_reset)
    else:
        # 新IP，初始化计数器
        rate_limits[client_ip] = (1, current_time)
    
    # 继续处理请求
    response = await call_next(request)
    return response