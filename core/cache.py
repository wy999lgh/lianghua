# -*- coding: utf-8 -*-
"""
Redis 缓存层 - 为重复计算提供缓存加速

设计要点:
- 连接失败时优雅降级（跳过缓存，直接执行原函数）
- 基于参数哈希的自动缓存键生成
- 可配置的 TTL（过期时间）
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Optional, Callable, Any

try:
    import redis as _redis_lib
except ImportError:
    _redis_lib = None

logger = logging.getLogger(__name__)

# 默认 TTL（秒）
DEFAULT_TTL = 300

# 全局 Redis 连接（惰性初始化）
_redis_client: Optional[Any] = None
_redis_available: bool = True


def _get_redis() -> Optional[Any]:
    """获取 Redis 连接，失败时返回 None"""
    global _redis_client, _redis_available

    if _redis_lib is None or not _redis_available:
        return None
    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except Exception:
            _redis_available = False
            logger.warning("Redis 连接断开，已降级为无缓存模式")
            return None

    try:
        _redis_client = _redis_lib.Redis(
            host="localhost",
            port=6379,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        _redis_client.ping()
        logger.info("Redis 缓存已连接")
        return _redis_client
    except Exception:
        _redis_available = False
        logger.warning("Redis 不可用，已降级为无缓存模式")
        return None


def _make_cache_key(prefix: str, *args, **kwargs) -> str:
    """根据函数参数生成缓存键"""
    raw = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    digest = hashlib.md5(raw.encode()).hexdigest()[:16]
    return f"quant:{prefix}:{digest}"


def get_cached(prefix: str, *args, **kwargs) -> Optional[dict]:
    """显式读取缓存，用于 FastAPI 端点内部"""
    client = _get_redis()
    if client is None:
        return None
    cache_key = _make_cache_key(prefix, *args, **kwargs)
    try:
        val = client.get(cache_key)
        if val is not None:
            logger.debug("缓存命中: %s", cache_key)
            return json.loads(val)
    except Exception:
        pass
    return None


def set_cache(prefix: str, value, ttl: int = DEFAULT_TTL, *args, **kwargs) -> None:
    """显式写入缓存，用于 FastAPI 端点内部"""
    client = _get_redis()
    if client is None:
        return
    cache_key = _make_cache_key(prefix, *args, **kwargs)
    try:
        client.setex(cache_key, ttl, json.dumps(value, default=str))
        logger.debug("缓存写入: %s (TTL=%ds)", cache_key, ttl)
    except Exception:
        pass


def invalidate_cache(prefix: str) -> int:
    """按前缀清除缓存，返回清除的键数量"""
    client = _get_redis()
    if client is None:
        return 0
    pattern = f"quant:{prefix}:*"
    keys = client.keys(pattern)
    if keys:
        return client.delete(*keys)
    return 0


def cached(prefix: str, ttl: int = DEFAULT_TTL):
    """装饰器：为函数结果添加 Redis 缓存

    Args:
        prefix: 缓存键前缀（建议用端点标识，如 'ema_data'）
        ttl: 缓存过期时间（秒），默认 300

    Usage:
        @cached("ema_data", ttl=120)
        def compute_ema(symbol, period, limit):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client = _get_redis()
            if client is None:
                return func(*args, **kwargs)

            cache_key = _make_cache_key(prefix, *args, **kwargs)
            try:
                cached_val = client.get(cache_key)
                if cached_val is not None:
                    logger.debug("缓存命中: %s", cache_key)
                    return json.loads(cached_val)
            except Exception:
                logger.debug("缓存读取失败: %s", cache_key)

            result = func(*args, **kwargs)

            try:
                client.setex(cache_key, ttl, json.dumps(result, default=str))
                logger.debug("缓存写入: %s (TTL=%ds)", cache_key, ttl)
            except Exception:
                logger.debug("缓存写入失败: %s", cache_key)

            return result

        return wrapper

    return decorator
