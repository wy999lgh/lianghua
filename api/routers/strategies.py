"""策略配置相关路由

此模块包含策略配置的创建、查询、更新与删除相关的 API 端点。
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional

from api.schemas import StrategyConfig, StrategyUpdate
from core.data.database import Database, get_db
from core.strategy.strategy_manager import get_strategy_manager

router = APIRouter()


@router.post("/strategies/config", response_model=Dict[str, Any])
def create_strategy_config(config: StrategyConfig):
    """创建策略配置（写入 PostgreSQL）"""
    try:
        db = get_db()
        cfg = config.model_dump()
        if not cfg.get("symbol"):
            raise HTTPException(status_code=400, detail="symbol 不能为空")
        if cfg.get("strategy_type") is None:
            cfg["strategy_type"] = "grid"
        if cfg.get("max_position") is None:
            cfg["max_position"] = 100000000.0
        if cfg.get("min_position") is None:
            cfg["min_position"] = 0.0
        if cfg.get("initial_cash") is None:
            cfg["initial_cash"] = 1000000.0  # 默认100万初始资金
        if cfg.get("buy_quantity") is None:
            cfg["buy_quantity"] = 100  # 默认买入数量
        if cfg.get("sell_quantity") is None:
            cfg["sell_quantity"] = 100  # 默认卖出数量
        if cfg.get("upper_count") is None:
            cfg["upper_count"] = 100
        if cfg.get("lower_count") is None:
            cfg["lower_count"] = 100
        new_id = db.save_strategy_config(cfg)
        return {"status": "success", "config_id": int(new_id), "config": cfg}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建策略配置失败: {str(e)}")


@router.get("/strategies/configs", response_model=Dict[str, Any])
def list_strategy_configs():
    """获取策略配置列表（来源：PostgreSQL strategy_configs）"""
    try:
        db = get_db()
        items: List[Dict[str, Any]] = db.get_strategy_configs()
        return {"status": "success", "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略配置列表失败: {str(e)}")


@router.get("/strategies/config/{config_id}", response_model=Dict[str, Any])
def get_strategy_config(config_id: int):
    """根据ID获取单个策略配置"""
    try:
        db = get_db()
        config = db.get_strategy_config_by_id(config_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"策略配置 {config_id} 不存在")
        return {"status": "success", "config": config}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略配置失败: {str(e)}")


@router.put("/strategies/config/{config_id}", response_model=Dict[str, Any])
def update_strategy_config(config_id: int, config: StrategyUpdate):
    """更新策略配置"""
    try:
        db = get_db()
        # 先检查策略是否存在
        existing = db.get_strategy_config_by_id(config_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"策略配置 {config_id} 不存在")
        
        cfg = config.model_dump(exclude_unset=True)
        
        conn = db._pg_connect()
        try:
            cur = conn.cursor()
            update_fields = []
            update_values = []
            
            if "strategy_name" in cfg:
                update_fields.append("strategy_name = %s")
                update_values.append(cfg["strategy_name"])
            if "strategy_type" in cfg:
                update_fields.append("strategy_type = %s")
                update_values.append(cfg["strategy_type"])
            if "symbol" in cfg:
                update_fields.append("symbol = %s")
                update_values.append(cfg["symbol"])
            if "base_price" in cfg:
                update_fields.append("base_price = %s")
                update_values.append(cfg["base_price"])
            if "upper_step" in cfg:
                update_fields.append("upper_step = %s")
                update_values.append(cfg["upper_step"])
            if "lower_step" in cfg:
                update_fields.append("lower_step = %s")
                update_values.append(cfg["lower_step"])
            if "upper_count" in cfg:
                update_fields.append("upper_count = %s")
                update_values.append(cfg["upper_count"])
            if "lower_count" in cfg:
                update_fields.append("lower_count = %s")
                update_values.append(cfg["lower_count"])
            if "max_position" in cfg:
                update_fields.append("max_position = %s")
                update_values.append(cfg["max_position"])
            if "min_position" in cfg:
                update_fields.append("min_position = %s")
                update_values.append(cfg["min_position"])
            
            if not update_fields:
                raise HTTPException(status_code=400, detail="没有提供更新字段")
            
            update_values.append(config_id)
            sql = f"UPDATE strategy_configs SET {', '.join(update_fields)} WHERE id = %s"
            cur.execute(sql, tuple(update_values))
            conn.commit()
            
            # 返回更新后的配置
            updated_config = db.get_strategy_config_by_id(config_id)
            return {"status": "success", "config": updated_config}
        finally:
            db._pg_release(conn)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新策略配置失败: {str(e)}")


@router.delete("/strategies/config/{config_id}", response_model=Dict[str, Any])
def delete_strategy_config(config_id: int):
    """删除策略配置（级联删除关联的回测结果和交易记录）"""
    try:
        db = get_db()
        # 先检查策略是否存在
        existing = db.get_strategy_config_by_id(config_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"策略配置 {config_id} 不存在")
        
        success = db.delete_strategy_config(config_id)
        if not success:
            raise HTTPException(status_code=500, detail="删除策略配置失败")
        
        return {"status": "success", "message": f"策略配置 {config_id} 已成功删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除策略配置失败: {str(e)}")


@router.get("/strategies/list", response_model=Dict[str, Any])
def list_strategies():
    """获取后端策略层的策略脚本列表"""
    try:
        strategy_manager = get_strategy_manager()
        strategies = strategy_manager.list_strategies()
        
        strategy_info_list = []
        for strategy_name in strategies:
            info = strategy_manager.get_strategy_info(strategy_name)
            if info:
                strategy_info_list.append(info)
        
        return {"status": "success", "strategies": strategy_info_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略列表失败: {str(e)}")


@router.get("/strategies/info/{strategy_name}", response_model=Dict[str, Any])
def get_strategy_info(strategy_name: str):
    """获取指定策略的详细信息"""
    try:
        strategy_manager = get_strategy_manager()
        info = strategy_manager.get_strategy_info(strategy_name)
        
        if not info:
            raise HTTPException(status_code=404, detail=f"策略 {strategy_name} 不存在")
        
        return {"status": "success", "strategy": info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略信息失败: {str(e)}")


@router.put("/strategies/info/{strategy_name}", response_model=Dict[str, Any])
def update_strategy_config(strategy_name: str, config: Dict[str, Any]):
    """更新策略配置参数"""
    try:
        strategy_manager = get_strategy_manager()
        
        if strategy_name not in strategy_manager.list_strategies():
            raise HTTPException(status_code=404, detail=f"策略 {strategy_name} 不存在")
        
        # 获取策略类
        strategy_class = strategy_manager.strategies.get(strategy_name)
        if not strategy_class:
            raise HTTPException(status_code=404, detail=f"策略 {strategy_name} 不存在")
        
        # 更新策略类的默认配置
        if hasattr(strategy_class, 'DEFAULT_CONFIG'):
            strategy_class.DEFAULT_CONFIG.update(config.get('config', {}))
            print(f"[OK] 策略 {strategy_name} 配置已更新")
        
        return {
            "status": "success", 
            "message": f"策略 {strategy_name} 配置更新成功",
            "config": strategy_class.DEFAULT_CONFIG
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新策略配置失败: {str(e)}")
