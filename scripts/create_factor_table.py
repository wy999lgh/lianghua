# -*- coding: utf-8 -*-
"""
创建因子配置表脚本
"""

from core.database import Database

def create_factor_config_table():
    db = Database()
    
    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS factor_configs (
        id SERIAL PRIMARY KEY,
        factor_name VARCHAR(100) NOT NULL UNIQUE,
        display_name VARCHAR(200) NOT NULL,
        description TEXT,
        category VARCHAR(50) NOT NULL,
        missing_method VARCHAR(20) DEFAULT 'ffill',
        outlier_method VARCHAR(20) DEFAULT 'mad',
        normalize_method VARCHAR(20) DEFAULT 'zscore',
        params JSONB DEFAULT '{}'::jsonb,
        enabled BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    '''
    
    db.execute_sql(create_table_sql)
    print('因子配置表创建成功')
    
    # 添加索引
    index_sql = '''
    CREATE INDEX IF NOT EXISTS idx_factor_configs_name ON factor_configs(factor_name);
    CREATE INDEX IF NOT EXISTS idx_factor_configs_category ON factor_configs(category);
    CREATE INDEX IF NOT EXISTS idx_factor_configs_enabled ON factor_configs(enabled);
    '''
    db.execute_sql(index_sql)
    print('索引创建成功')

if __name__ == '__main__':
    create_factor_config_table()
