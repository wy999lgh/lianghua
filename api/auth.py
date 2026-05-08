# -*- coding: utf-8 -*-
"""JWT 认证与授权模块

提供 API 端点的身份验证和访问控制：
- 登录接口返回 JWT token
- 使用 Bearer Token 方式认证
- 支持可选的路由保护装饰器

使用方式：
    from api.auth import get_current_user, create_access_token
    from fastapi import Depends

    @router.get("/protected")
    def protected_route(user=Depends(get_current_user)):
        return {"user": user}
"""

import os
import time
import hashlib
import hmac
import base64
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# 密钥：优先从环境变量读取，否则使用项目名哈希作为默认值
_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "ai-quant-999-default-secret-change-me")
_TOKEN_EXPIRE_SECONDS = int(os.environ.get("JWT_TOKEN_EXPIRE", "86400"))  # 默认24小时

security = HTTPBearer(auto_error=False)


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(s: str) -> bytes:
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def create_access_token(username: str, expire_seconds: Optional[int] = None) -> str:
    """创建 JWT 访问令牌（HS256 签名）

    Args:
        username: 用户名
        expire_seconds: 过期秒数，默认使用 _TOKEN_EXPIRE_SECONDS

    Returns:
        str: JWT token 字符串
    """
    if expire_seconds is None:
        expire_seconds = _TOKEN_EXPIRE_SECONDS

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + expire_seconds,
    }

    header_b64 = _base64url_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _base64url_encode(json.dumps(payload).encode("utf-8"))

    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        _SECRET_KEY.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    signature_b64 = _base64url_encode(signature)

    return f"{signing_input}.{signature_b64}"


def verify_access_token(token: str) -> Dict[str, Any]:
    """验证 JWT 访问令牌并返回 payload

    Args:
        token: JWT token 字符串

    Returns:
        dict: payload 字典（含 sub, iat, exp）

    Raises:
        HTTPException: token 过期或无效
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="无效的认证令牌格式")

        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}"

        expected_sig = hmac.new(
            _SECRET_KEY.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        expected_sig_b64 = _base64url_encode(expected_sig)

        if not hmac.compare_digest(signature_b64, expected_sig_b64):
            raise HTTPException(status_code=401, detail="认证令牌签名无效")

        payload_raw = _base64url_decode(payload_b64)
        payload = json.loads(payload_raw)

        if payload.get("exp", 0) < time.time():
            raise HTTPException(status_code=401, detail="认证令牌已过期")

        return payload

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="认证令牌解析失败")


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """从请求头提取并验证当前用户（FastAPI 依赖注入）

    Args:
        credentials: HTTP Bearer 认证凭证（自动注入）

    Returns:
        str: 用户名

    Raises:
        HTTPException: 未提供 token 或 token 无效
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="请提供认证令牌（Bearer Token）")

    payload = verify_access_token(credentials.credentials)
    return payload.get("sub", "unknown")


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """可选认证：有 token 则返回用户名，无 token 返回 None（不报错）"""
    if credentials is None:
        return None
    try:
        payload = verify_access_token(credentials.credentials)
        return payload.get("sub", None)
    except HTTPException:
        return None
