from fastapi import Request
from typing import Optional


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    Handles proxies and load balancers.
    """
    # Check X-Forwarded-For header (from proxies/load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        ip = forwarded_for.split(",")[0].strip()
        return ip
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"
