"""系统相关路由

此模块包含系统级API端点：根路径、健康检查和用户认证。
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.auth import create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    token_type: str = "bearer"
    username: str


@router.get("/")
def read_root():
    """根路径，返回API信息"""
    return {
        "message": "网格交易量化策略系统API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@router.get("/health")
def health_check():
    """健康检查端点（含数据库连接验证）"""
    db_status = "unknown"
    try:
        from core.data.database import get_db
        db = get_db()
        tables = db.list_tables()
        db_status = "connected" if tables is not None else "error"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
    }


@router.post("/fix-strategy-table")
def fix_strategy_table():
    """修复策略配置表结构，添加缺失的字段"""
    try:
        from core.data.database import get_db
        db = get_db()
        conn = db._pg_connect()
        try:
            cur = conn.cursor()
            
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='strategy_configs'")
            existing_columns = [row[0] for row in cur.fetchall()]
            
            if 'initial_cash' not in existing_columns:
                cur.execute("ALTER TABLE strategy_configs ADD COLUMN initial_cash NUMERIC(18,2) DEFAULT 1000000.0")
            
            if 'buy_quantity' not in existing_columns:
                cur.execute("ALTER TABLE strategy_configs ADD COLUMN buy_quantity INTEGER DEFAULT 100")
            
            if 'sell_quantity' not in existing_columns:
                cur.execute("ALTER TABLE strategy_configs ADD COLUMN sell_quantity INTEGER DEFAULT 100")
            
            cur.execute("""
                UPDATE strategy_configs 
                SET 
                    initial_cash = COALESCE(initial_cash, 1000000.0),
                    buy_quantity = COALESCE(buy_quantity, 100),
                    sell_quantity = COALESCE(sell_quantity, 100)
                WHERE 
                    initial_cash IS NULL OR buy_quantity IS NULL OR sell_quantity IS NULL
            """)
            updated_count = cur.rowcount
            
            conn.commit()
            return {"status": "success", "updated_count": updated_count, "message": "策略配置表结构修复完成"}
        finally:
            db._pg_release(conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修复失败: {str(e)}")


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """用户登录，返回JWT访问令牌

    默认管理员账号：admin / admin123
    可通过环境变量 ADMIN_USERNAME / ADMIN_PASSWORD 自定义
    """
    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")

    if request.username != admin_username or request.password != admin_password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(request.username)
    return LoginResponse(
        access_token=token,
        username=request.username,
    )
