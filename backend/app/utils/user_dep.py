from fastapi import Header, HTTPException
from typing import Optional

async def get_user_id(x_user_id: Optional[str] = Header(None)):
    if not x_user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-Id header")
    return x_user_id


def get_user_id_from_websocket(websocket) -> str:
    """
    从WebSocket连接中获取用户ID
    这里简化处理，实际应该从JWT token或session中获取
    """
    # 从查询参数获取用户ID
    user_id = websocket.query_params.get("user_id")
    if not user_id:
        # 从headers获取
        user_id = websocket.headers.get("X-User-ID")
    
    if not user_id:
        raise ValueError("用户ID未提供")
    
    return user_id 