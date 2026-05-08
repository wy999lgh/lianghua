# -*- coding: utf-8 -*-
"""
因子管理模块
提供因子配置、计算和管理的API接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd
import numpy as np

router = APIRouter()


class FactorConfig(BaseModel):
    """因子配置模型"""
    factor_name: str = Field(..., description="因子名称")
    display_name: str = Field(..., description="因子显示名称")
    description: Optional[str] = Field(None, description="因子描述")
    category: str = Field(..., description="因子类别")
    missing_method: str = Field(default='ffill', description="缺失值处理方法: ffill/mean/median")
    outlier_method: str = Field(default='mad', description="去极值方法: mad/iqr/percentile")
    normalize_method: str = Field(default='zscore', description="标准化方法: zscore/minmax/rank")
    params: Dict[str, Any] = Field(default_factory=dict, description="因子参数")
    enabled: bool = Field(default=True, description="是否启用")


class FactorUpdateRequest(BaseModel):
    """因子更新请求"""
    display_name: Optional[str] = Field(None, description="因子显示名称")
    description: Optional[str] = Field(None, description="因子描述")
    missing_method: Optional[str] = Field(None, description="缺失值处理方法")
    outlier_method: Optional[str] = Field(None, description="去极值方法")
    normalize_method: Optional[str] = Field(None, description="标准化方法")
    params: Optional[Dict[str, Any]] = Field(None, description="因子参数")
    enabled: Optional[bool] = Field(None, description="是否启用")


class FactorComputeRequest(BaseModel):
    """因子计算请求"""
    symbol: str = Field(..., description="标的代码")
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD")
    factors: List[str] = Field(..., description="要计算的因子列表")
    params: Dict[str, Any] = Field(default_factory=dict, description="因子参数")


class FactorResponse(BaseModel):
    """因子响应"""
    factor_name: str
    values: List[float]
    dates: List[str]
    stats: Dict[str, float]


FACTOR_TEMPLATES = {
    "ma5": {"name": "5日移动平均", "description": "简单移动平均线", "params": {"period": 5}},
    "ma10": {"name": "10日移动平均", "description": "简单移动平均线", "params": {"period": 10}},
    "ma20": {"name": "20日移动平均", "description": "简单移动平均线", "params": {"period": 20}},
    "ma60": {"name": "60日移动平均", "description": "简单移动平均线", "params": {"period": 60}},
    "ema12": {"name": "12日指数移动平均", "description": "指数加权移动平均线", "params": {"period": 12}},
    "ema26": {"name": "26日指数移动平均", "description": "指数加权移动平均线", "params": {"period": 26}},
    "macd": {"name": "MACD指标", "description": "移动平均收敛发散指标", "params": {"fast": 12, "slow": 26, "signal": 9}},
    "bollinger": {"name": "布林带", "description": "基于EMA的布林带通道", "params": {"period": 20, "std_mult": 2.0}},
    "rsi": {"name": "RSI指标", "description": "相对强弱指标", "params": {"period": 14}},
    "atr": {"name": "ATR指标", "description": "平均真实波幅", "params": {"period": 14}},
    "cmo": {"name": "CMO动量", "description": "Chande动量振荡器", "params": {"period": 20}},
    "rolling_beta": {"name": "滚动Beta", "description": "相对基准的滚动Beta", "params": {"window": 60, "benchmark": "000300"}},
    "residual_momentum": {"name": "残差动量", "description": "去除市场影响的动量", "params": {"beta_window": 60}},
    "rolling_zscore": {"name": "滚动ZScore", "description": "滚动标准化分数", "params": {"window": 60}},
    "rolling_slope": {"name": "滚动斜率", "description": "滚动线性回归斜率", "params": {"window": 10}},
    "rolling_percentile": {"name": "滚动分位排名", "description": "滚动窗口内分位排名", "params": {"window": 60}}
}


def _get_db():
    from core.data.database import Database
    return Database()


@router.get("/templates", summary="获取因子模板列表")
async def get_factor_templates():
    return {"code": 200, "data": FACTOR_TEMPLATES}


@router.get("/methods", summary="获取处理方法选项")
async def get_processing_methods():
    return {
        "code": 200,
        "data": {
            "missing": {"ffill": "前向填充", "mean": "均值填充", "median": "中位数填充"},
            "outlier": {"mad": "MAD法(3倍中位数绝对偏差)", "iqr": "IQR法(1.5倍四分位距)", "percentile": "百分位数法(1%-99%)"},
            "normalize": {"zscore": "Z-score标准化", "minmax": "Min-Max缩放", "rank": "排名标准化"}
        }
    }


@router.post("/compute", summary="计算因子")
async def compute_factors(request: FactorComputeRequest):
    try:
        from core.analysis.factor_processor import FactorProcessor
        from core.analysis.factor_library import FactorLibrary

        db = _get_db()
        results = {}

        table_name = f"stock_daily_{request.symbol}" if request.symbol.isdigit() else f"index_daily_{request.symbol}"
        data = db.get_data(table_name, start_date=request.start_date, end_date=request.end_date, limit=10000)

        if data is None or len(data) == 0:
            raise HTTPException(status_code=404, detail=f"找不到标的 {request.symbol} 的数据")

        close = data['close']

        for factor_name in request.factors:
            if factor_name.startswith("ma"):
                period = int(factor_name[2:]) if len(factor_name) > 2 else 20
                values = FactorLibrary.ma(close, period=period)
            elif factor_name.startswith("ema"):
                period = int(factor_name[3:]) if len(factor_name) > 3 else 20
                values = FactorLibrary.ema(close, period=period)
            elif factor_name == "macd":
                ema12 = FactorLibrary.ema(close, period=12)
                ema26 = FactorLibrary.ema(close, period=26)
                macd = ema12 - ema26
                signal = FactorLibrary.ema(macd, period=9)
                values = macd - signal
            elif factor_name == "bollinger":
                bb = FactorLibrary.bollinger_bands_ema(close, period=20, std_mult=2.0)
                values = bb['bb_width']
            elif factor_name == "rsi":
                delta = close.diff()
                gain = delta.clip(lower=0)
                loss = (-delta).clip(lower=0)
                avg_gain = gain.ewm(com=13, adjust=False).mean()
                avg_loss = loss.ewm(com=13, adjust=False).mean()
                rs = avg_gain / avg_loss.replace(0, np.nan)
                values = 100 - (100 / (1 + rs))
            elif factor_name == "atr":
                high = data['high']
                low = data['low']
                tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
                values = tr.ewm(span=13, adjust=False).mean()
            elif factor_name == "cmo":
                values = FactorLibrary.cmo(close, period=20)
            else:
                values = FactorLibrary.ma(close, period=20)

            valid_mask = ~values.isna()
            valid_dates = data.loc[valid_mask, 'date'].astype(str).tolist() if 'date' in data.columns else [str(d) for d in data.loc[valid_mask, 'trade_date']]

            processor = FactorProcessor(
                missing_method=request.params.get('missing_method', 'ffill'),
                outlier_method=request.params.get('outlier_method', 'mad'),
                normalize_method=request.params.get('normalize_method', 'zscore')
            )

            df_temp = pd.DataFrame({'factor': values})
            processed = processor.process_pipeline(df_temp)

            results[factor_name] = {
                "values": processed['factor'].fillna(0).tolist(),
                "dates": valid_dates,
                "stats": {
                    "mean": float(processed['factor'].mean()),
                    "std": float(processed['factor'].std()),
                    "min": float(processed['factor'].min()),
                    "max": float(processed['factor'].max())
                }
            }

        return {
            "code": 200,
            "data": {"symbol": request.symbol, "start_date": request.start_date, "end_date": request.end_date, "factors": results}
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", summary="获取因子列表")
async def list_factors():
    try:
        db = _get_db()
        sql = "SELECT * FROM factor_configs ORDER BY category, created_at"
        result = db.execute_sql(sql, fetch=True)
        
        if result:
            factors = []
            for row in result:
                factors.append({
                    "id": row[0],
                    "factor_name": row[1],
                    "display_name": row[2],
                    "description": row[3],
                    "category": row[4],
                    "missing_method": row[5],
                    "outlier_method": row[6],
                    "normalize_method": row[7],
                    "params": row[8] if row[8] else {},
                    "enabled": row[9],
                    "created_at": row[10].isoformat() if row[10] else None,
                    "updated_at": row[11].isoformat() if row[11] else None
                })
            return {"code": 200, "data": {"factors": factors}}
        else:
            return {"code": 200, "data": {"factors": []}}
            
    except Exception as e:
        return {"code": 200, "data": {"factors": []}}


@router.get("/{factor_name}", summary="获取单个因子配置")
async def get_factor(factor_name: str):
    try:
        db = _get_db()
        sql = "SELECT * FROM factor_configs WHERE factor_name = %s"
        result = db.execute_sql(sql, (factor_name,), fetch=True)
        
        if result:
            row = result[0]
            return {
                "code": 200,
                "data": {
                    "id": row[0],
                    "factor_name": row[1],
                    "display_name": row[2],
                    "description": row[3],
                    "category": row[4],
                    "missing_method": row[5],
                    "outlier_method": row[6],
                    "normalize_method": row[7],
                    "params": row[8] if row[8] else {},
                    "enabled": row[9],
                    "created_at": row[10].isoformat() if row[10] else None,
                    "updated_at": row[11].isoformat() if row[11] else None
                }
            }
        else:
            raise HTTPException(status_code=404, detail=f"因子 {factor_name} 不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config", summary="保存因子配置")
async def save_factor_config(config: FactorConfig):
    try:
        db = _get_db()
        
        existing = db.execute_sql("SELECT id FROM factor_configs WHERE factor_name = %s", (config.factor_name,), fetch=True)
        
        if existing:
            raise HTTPException(status_code=409, detail=f"因子 {config.factor_name} 已存在")
        
        sql = '''
            INSERT INTO factor_configs 
            (factor_name, display_name, description, category, missing_method, outlier_method, normalize_method, params, enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        
        db.execute_sql(sql, (
            config.factor_name,
            config.display_name,
            config.description,
            config.category,
            config.missing_method,
            config.outlier_method,
            config.normalize_method,
            str(config.params).replace("'", '"') if config.params else '{}',
            config.enabled
        ))
        
        return {
            "code": 200,
            "message": "因子配置保存成功",
            "data": config.model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{factor_name}", summary="更新因子配置")
async def update_factor_config(factor_name: str, request: FactorUpdateRequest):
    try:
        db = _get_db()
        
        existing = db.execute_sql("SELECT id FROM factor_configs WHERE factor_name = %s", (factor_name,), fetch=True)
        if not existing:
            raise HTTPException(status_code=404, detail=f"因子 {factor_name} 不存在")
        
        update_fields = []
        update_values = []
        
        if request.display_name is not None:
            update_fields.append("display_name = %s")
            update_values.append(request.display_name)
        if request.description is not None:
            update_fields.append("description = %s")
            update_values.append(request.description)
        if request.missing_method is not None:
            update_fields.append("missing_method = %s")
            update_values.append(request.missing_method)
        if request.outlier_method is not None:
            update_fields.append("outlier_method = %s")
            update_values.append(request.outlier_method)
        if request.normalize_method is not None:
            update_fields.append("normalize_method = %s")
            update_values.append(request.normalize_method)
        if request.params is not None:
            update_fields.append("params = %s")
            update_values.append(str(request.params).replace("'", '"'))
        if request.enabled is not None:
            update_fields.append("enabled = %s")
            update_values.append(request.enabled)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="没有提供更新字段")
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_values.append(factor_name)
        
        sql = f"UPDATE factor_configs SET {', '.join(update_fields)} WHERE factor_name = %s"
        db.execute_sql(sql, tuple(update_values))
        
        return {
            "code": 200,
            "message": "因子配置更新成功",
            "data": {"factor_name": factor_name}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{factor_name}", summary="删除因子配置")
async def delete_factor_config(factor_name: str):
    try:
        db = _get_db()
        
        existing = db.execute_sql("SELECT id FROM factor_configs WHERE factor_name = %s", (factor_name,), fetch=True)
        if not existing:
            raise HTTPException(status_code=404, detail=f"因子 {factor_name} 不存在")
        
        sql = "DELETE FROM factor_configs WHERE factor_name = %s"
        db.execute_sql(sql, (factor_name,))
        
        return {
            "code": 200,
            "message": "因子配置删除成功",
            "data": {"factor_name": factor_name}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", summary="批量保存因子配置")
async def batch_save_factors(configs: List[FactorConfig]):
    try:
        db = _get_db()
        saved_count = 0
        skipped_count = 0
        
        for config in configs:
            try:
                existing = db.execute_sql("SELECT id FROM factor_configs WHERE factor_name = %s", (config.factor_name,), fetch=True)
                if existing:
                    skipped_count += 1
                    continue
                
                sql = '''
                    INSERT INTO factor_configs 
                    (factor_name, display_name, description, category, missing_method, outlier_method, normalize_method, params, enabled)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                '''
                
                db.execute_sql(sql, (
                    config.factor_name,
                    config.display_name,
                    config.description,
                    config.category,
                    config.missing_method,
                    config.outlier_method,
                    config.normalize_method,
                    str(config.params).replace("'", '"') if config.params else '{}',
                    config.enabled
                ))
                saved_count += 1
            except Exception:
                skipped_count += 1
        
        return {
            "code": 200,
            "message": f"批量保存完成",
            "data": {"saved": saved_count, "skipped": skipped_count}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview", summary="预览因子数据")
async def preview_factor(symbol: str, factor_name: str, days: int = 30):
    try:
        from core.analysis.factor_library import FactorLibrary

        db = _get_db()
        table_name = f"stock_daily_{symbol}" if symbol.isdigit() else f"index_daily_{symbol}"
        data = db.get_data(table_name, limit=days)
        
        if data is None or len(data) == 0:
            raise HTTPException(status_code=404, detail=f"找不到标的 {symbol} 的数据")

        close = data['close']

        if factor_name.startswith("ma"):
            period = int(factor_name[2:]) if len(factor_name) > 2 else 20
            values = FactorLibrary.ma(close, period=period)
        elif factor_name.startswith("ema"):
            period = int(factor_name[3:]) if len(factor_name) > 3 else 20
            values = FactorLibrary.ema(close, period=period)
        else:
            values = FactorLibrary.ma(close, period=20)

        date_col = 'date' if 'date' in data.columns else 'trade_date'
        result = pd.DataFrame({
            'date': data[date_col].astype(str),
            'close': close.values,
            factor_name: values.values
        }).tail(days).to_dict('records')

        return {"code": 200, "data": result}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
