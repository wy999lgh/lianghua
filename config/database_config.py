# -*- coding: utf-8 -*-
"""
网格交易系统 - 数据库配置模块

密码读取优先级：环境变量 PGPASSWORD > POSTGRES_PASSWORD > .env > config.yaml 回退值
"""

import os
import re
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
import yaml

try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass


def _get_project_root() -> Path:
    return Path(__file__).parent.parent.resolve()


def _resolve_env_vars(value: str) -> str:
    """解析字符串中的 ${VAR:-default} 环境变量占位符"""
    if not isinstance(value, str):
        return value

    def _replace(match):
        expr = match.group(1)
        if ":-" in expr:
            var, default = expr.split(":-", 1)
            return os.environ.get(var.strip(), default.strip())
        return os.environ.get(expr, "")

    return re.sub(r"\$\{([^}]+)\}", _replace, value)


def _load_yaml_config() -> dict:
    config_path = _get_project_root() / "config" / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            raw = yaml.safe_load(f) or {}
        return _walk_and_resolve(raw)
    return {}


def _walk_and_resolve(obj):
    """递归遍历配置并解析环境变量占位符"""
    if isinstance(obj, dict):
        return {k: _walk_and_resolve(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_and_resolve(v) for v in obj]
    if isinstance(obj, str):
        return _resolve_env_vars(obj)
    return obj


@dataclass
class DatabaseConfig:
    """数据库配置类 (仅支持 PostgreSQL)"""
    backend: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_database: str = "postgres"
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_password_env: str = "PGPASSWORD"
    project_root: Path = field(default_factory=_get_project_root)
    
    @classmethod
    def from_yaml(cls, config_path: Optional[str] = None) -> "DatabaseConfig":
        if config_path:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = _load_yaml_config()
        
        db_config = config.get('database', {})
        pg_config: Dict[str, Any] = db_config.get("postgres", {}) or {}
        return cls(
            backend="postgres",  # 强制使用 postgres
            postgres_host=pg_config.get("host", "localhost"),
            postgres_port=int(pg_config.get("port", 5432)),
            postgres_database=pg_config.get("database", "postgres"),
            postgres_user=pg_config.get("user", "postgres"),
            postgres_password=pg_config.get("password", ""),
            postgres_password_env=pg_config.get("password_env", "PGPASSWORD"),
        )
    
    def get_backend(self) -> str:
        return "postgres"

    def get_postgres_password(self) -> str:
        """获取 PostgreSQL 密码，优先读取环境变量，其次配置文件（仅作为回退）。"""
        env_key = str(self.postgres_password_env or "PGPASSWORD").strip()
        if env_key:
            env_password = os.environ.get(env_key, "").strip()
            if env_password:
                return env_password

        for fallback_key in ("PGPASSWORD", "POSTGRES_PASSWORD"):
            env_password = os.environ.get(fallback_key, "").strip()
            if env_password:
                return env_password

        config_password = str(self.postgres_password or "").strip()
        if config_password:
            return config_password

        return ""

    def get_postgres_password_source(self) -> str:
        """返回当前密码来源，便于排查配置问题。"""
        env_key = str(self.postgres_password_env or "PGPASSWORD").strip()
        if env_key and os.environ.get(env_key, "").strip():
            return f"env:{env_key}"

        for fallback_key in ("PGPASSWORD", "POSTGRES_PASSWORD"):
            if os.environ.get(fallback_key, "").strip():
                return f"env:{fallback_key}"

        config_password = str(self.postgres_password or "").strip()
        if config_password:
            return "config"

        return "missing"

    def get_postgres_connect_kwargs(self) -> Dict[str, Any]:
        password = self.get_postgres_password()
        if not password:
            raise RuntimeError(
                "PostgreSQL 密码未配置：请设置环境变量 PGPASSWORD 或 POSTGRES_PASSWORD，"
                "或在项目根目录创建 .env 文件（参考 .env.example）。"
            )
        kwargs: Dict[str, Any] = {
            "host": self.postgres_host,
            "port": int(self.postgres_port),
            "dbname": self.postgres_database,
            "user": self.postgres_user,
        }
        if password:
            kwargs["password"] = password
        return kwargs

_database_config: Optional[DatabaseConfig] = None


def get_database_config(reload: bool = False) -> DatabaseConfig:
    global _database_config
    if _database_config is None or reload:
        _database_config = DatabaseConfig.from_yaml()
    return _database_config


def get_project_root() -> str:
    return str(_get_project_root())


PROJECT_ROOT = str(_get_project_root())


if __name__ == "__main__":
    config = get_database_config()
    print(f"Project root: {config.project_root}")
    print(f"Backend: {config.get_backend()}")
    print(f"Password source: {config.get_postgres_password_source()}")
    print(f"Postgres Config: {config.get_postgres_connect_kwargs()}")
