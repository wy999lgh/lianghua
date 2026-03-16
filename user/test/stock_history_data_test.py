"""
    股票历史数据获取详细测试示例
    
    本文件演示如何使用tqcenter获取股票的历史K线数据
    包含多种获取方式:
    1. 按时间段获取
    2. 按数量获取
    3. 按指定字段获取
    4. 不同周期获取(日K、周K、月K、分钟K)
    5. 不同复权方式(不复权、前复权、后复权)
    
    使用前请确保:
    - 已启动通达信客户端并登录
    - 已下载对应的盘后数据
    
    注意: get_market_data 返回的是字典格式，键为字段名，值为DataFrame
"""

import numpy as np
import pandas as pd
import sys
from pathlib import Path

# 添加父目录到路径以导入tqcenter
sys.path.insert(0, str(Path(__file__).parent.parent))
from tqcenter import tq

# 初始化连接
tq.initialize(__file__)

# ============================================================================
# 辅助函数：从字典中提取单只股票的DataFrame
# ============================================================================
def get_stock_df(data_dict, stock_code):
    """
    从get_market_data返回的字典中提取指定股票的DataFrame
    
    Args:
        data_dict: get_market_data返回的字典
        stock_code: 股票代码
    
    Returns:
        DataFrame: 包含股票数据的DataFrame
    """
    if not data_dict or len(data_dict) == 0:
        return pd.DataFrame()
    
    # 获取第一个字段的DataFrame作为基础
    first_key = list(data_dict.keys())[0]
    df = data_dict[first_key].copy()
    
    # 添加所有其他字段
    for key, value in data_dict.items():
        df[key] = value
    
    return df

# ============================================================================
# 示例1: 按时间段获取日K线数据(不复权)
# ============================================================================
print("=" * 80)
print("示例1: 按时间段获取日K线数据(不复权)")
print("=" * 80)

result1 = tq.get_market_data(
    field_list=[],  # 空列表表示返回所有字段
    stock_list=['600000.SH'],  # 浦发银行
    start_time='20250101',  # 开始日期
    end_time='20250801',     # 结束日期
    count=-1,                # -1表示不限制数量
    dividend_type='none',   #不复权
    period='1d',            # 日K线
    fill_data=True          # 填充缺失数据
)

print(f"\n返回的数据类型: {type(result1)}")
print(f"返回的字段: {list(result1.keys())}")

# 提取DataFrame
df1 = get_stock_df(result1, '600000.SH')
print(f"\n获取到 {len(df1)} 条记录")
print(df1.head(10))

# ============================================================================
# 示例2: 按时间段获取日K线数据(前复权)
# ============================================================================
print("\n" + "=" * 80)
print("示例2: 按时间段获取日K线数据(前复权)")
print("=" * 80)

result2 = tq.get_market_data(
    field_list=[],
    stock_list=['600000.SH'],
    start_time='20250101',
    end_time='20250801',
    count=-1,
    dividend_type='front',  # 前复权
    period='1d',
    fill_data=True
)

df2 = get_stock_df(result2, '600000.SH')
print(f"\n获取到 {len(df2)} 条记录")
print(df2.head(10))

# ============================================================================
# 示例3: 按时间段获取日K线数据(后复权)
# ============================================================================
print("\n" + "=" * 80)
print("示例3: 按时间段获取日K线数据(后复权)")
print("=" * 80)

result3 = tq.get_market_data(
    field_list=[],
    stock_list=['600000.SH'],
    start_time='20250101',
    end_time='20250801',
    count=-1,
    dividend_type='back',   # 后复权
    period='1d',
    fill_data=True
)

df3 = get_stock_df(result3, '600000.SH')
print(f"\n获取到 {len(df3)} 条记录")
print(df3.head(10))

# ============================================================================
# 示例4: 按指定数量获取最新的N条数据
# ============================================================================
print("\n" + "=" * 80)
print("示例4: 获取最新的30条日K线数据")
print("=" * 80)

result4 = tq.get_market_data(
    field_list=[],
    stock_list=['600000.SH'],
    start_time='',     # 空字符串表示从当前往前
    end_time='',
    count=30,          # 只获取最新30条
    dividend_type='none',
    period='1d',
    fill_data=True
)

df4 = get_stock_df(result4, '600000.SH')
print(f"\n获取到 {len(df4)} 条记录")
print(df4)

# ============================================================================
# 示例5: 只获取指定字段的数据(如开盘价、收盘价、成交量)
# ============================================================================
print("\n" + "=" * 80)
print("示例5: 只获取指定的字段(开盘价、收盘价、成交量)")
print("=" * 80)

result5 = tq.get_market_data(
    field_list=['Open', 'Close', 'Volume'],  # 只返回这三个字段
    stock_list=['600000.SH'],
    start_time='20250101',
    end_time='20250801',
    count=-1,
    dividend_type='none',
    period='1d',
    fill_data=True
)

print(f"\n返回的字段: {list(result5.keys())}")
df5 = get_stock_df(result5, '600000.SH')
print(f"\n获取到 {len(df5)} 条记录")
print(df5.head(15))

# ============================================================================
# 示例6: 获取周K线数据
# ============================================================================
print("\n" + "=" * 80)
print("示例6: 获取周K线数据")
print("=" * 80)

result6 = tq.get_market_data(
    field_list=[],
    stock_list=['600000.SH'],
    start_time='20250101',
    end_time='20250801',
    count=-1,
    dividend_type='none',
    period='1w',            # 周K线
    fill_data=True
)

df6 = get_stock_df(result6, '600000.SH')
print(f"\n获取到 {len(df6)} 条周K线记录")
print(df6.head(10))

# ============================================================================
# 示例7: 获取月K线数据
# ============================================================================
print("\n" + "=" * 80)
print("示例7: 获取月K线数据")
print("=" * 80)

result7 = tq.get_market_data(
    field_list=[],
    stock_list=['600000.SH'],
    start_time='20240101',
    end_time='20250801',
    count=-1,
    dividend_type='none',
    period='1mon',            # 月K线
    fill_data=True
)

df7 = get_stock_df(result7, '600000.SH')
print(f"\n获取到 {len(df7)} 条月K线记录")
print(df7)

# ============================================================================
# 示例8: 获取分钟K线数据(5分钟)
# ============================================================================
print("\n" + "=" * 80)
print("示例8: 获取5分钟K线数据")
print("=" * 80)

result8 = tq.get_market_data(
    field_list=[],
    stock_list=['600000.SH'],
    start_time='20251201',  # 分钟K建议取较短时间段
    end_time='20251210',
    count=-1,
    dividend_type='none',
    period='5m',            # 5分钟K线
    fill_data=True
)

df8 = get_stock_df(result8, '600000.SH')
print(f"\n获取到 {len(df8)} 条5分钟K线记录")
print(df8.head(20))

# ============================================================================
# 示例9: 获取多只股票的数据
# ============================================================================
print("\n" + "=" * 80)
print("示例9: 获取多只股票的数据")
print("=" * 80)

result9 = tq.get_market_data(
    field_list=[],
    stock_list=['600000.SH', '600004.SH', '000001.SZ'],  # 多只股票
    start_time='20250101',
    end_time='20250801',
    count=-1,
    dividend_type='none',
    period='1d',
    fill_data=True
)

print(f"\n返回的数据结构:")
print(f"- 字段数: {len(result9)}")
print(f"- 字段列表: {list(result9.keys())[:5]}...")  # 只显示前5个字段

# 查看某个字段的DataFrame（例如Close收盘价）
if 'Close' in result9:
    print(f"\n收盘价数据: {len(result9['Close'])} 行")
    print(result9['Close'].head(10))

# ============================================================================
# 示例10: 数据保存到文件
# ============================================================================
print("\n" + "=" * 80)
print("示例10: 将数据保存到CSV文件")
print("=" * 80)

result10 = tq.get_market_data(
    field_list=[],
    stock_list=['600000.SH'],
    start_time='20250101',
    end_time='20250801',
    count=-1,
    dividend_type='none',
    period='1d',
    fill_data=True
)

df10 = get_stock_df(result10, '600000.SH')
output_path = str(Path(__file__).parent.parent.parent / 'data' / 'stock_history.csv')
df10.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"\n数据已保存到: {output_path}")
print(f"保存了 {len(df10)} 条记录")

# ============================================================================
# 示例11: 数据分析和可视化准备
# ============================================================================
print("\n" + "=" * 80)
print("示例11: 基本数据分析")
print("=" * 80)

result11 = tq.get_market_data(
    field_list=[],
    stock_list=['600000.SH'],
    start_time='20250101',
    end_time='20250801',
    count=-1,
    dividend_type='none',
    period='1d',
    fill_data=True
)

df11 = get_stock_df(result11, '600000.SH')

if len(df11) > 0 and 'Close' in df11.columns:
    print(f"\n数据概况:")
    print(f"- 记录数: {len(df11)}")
    print(f"- 字段数: {len(df11.columns)}")
    print(f"- 日期范围: {df11.index.min()} 到 {df11.index.max()}")
    
    if 'High' in df11.columns:
        print(f"- 最高价: {df11['High'].max():.2f}")
    if 'Low' in df11.columns:
        print(f"- 最低价: {df11['Low'].min():.2f}")
    if 'Volume' in df11.columns:
        print(f"- 平均成交量: {df11['Volume'].mean():.0f} 手")
    if 'Amount' in df11.columns:
        print(f"- 总成交额: {df11['Amount'].sum():.2f} 万元")
    
    # 计算收益率
    df11['Returns'] = df11['Close'].pct_change()
    print(f"- 最大单日涨幅: {df11['Returns'].max()*100:.2f}%")
    print(f"- 最大单日跌幅: {df11['Returns'].min()*100:.2f}%")

# ============================================================================
# 示例12: 获取特定时间段的数据并进行筛选
# ============================================================================
print("\n" + "=" * 80)
print("示例12: 获取数据并进行条件筛选")
print("=" * 80)

result12 = tq.get_market_data(
    field_list=[],
    stock_list=['600000.SH'],
    start_time='20250101',
    end_time='20250801',
    count=-1,
    dividend_type='none',
    period='1d',
    fill_data=True
)

df12 = get_stock_df(result12, '600000.SH')

if len(df12) > 0 and 'Close' in df12.columns:
    # 筛选收盘价大于某值的记录
    df_filtered = df12[df12['Close'] > 8.0]
    print(f"\n收盘价大于8.00元的交易日: {len(df_filtered)} 天")
    print(df_filtered[['Open', 'Close', 'Volume']].head(10))
    
    # 筛选成交量最大的前5天
    if 'Volume' in df12.columns:
        df_top_volume = df12.nlargest(5, 'Volume')
        print(f"\n成交量最大的5天:")
        print(df_top_volume[['Close', 'Volume', 'Amount']])

# ============================================================================
# 示例13: 不填充缺失数据
# ============================================================================
print("\n" + "=" * 80)
print("示例13: 不填充缺失数据(fill_data=False)")
print("=" * 80)

result13 = tq.get_market_data(
    field_list=[],
    stock_list=['600000.SH'],
    start_time='20250101',
    end_time='20250801',
    count=-1,
    dividend_type='none',
    period='1d',
    fill_data=False  # 不填充数据
)

df13 = get_stock_df(result13, '600000.SH')
print(f"\n获取到 {len(df13)} 条记录(不填充)")

# ============================================================================
# 示例14: 获取所有常见字段
# ============================================================================
print("\n" + "=" * 80)
print("示例14: 获取所有可用字段")
print("=" * 80)

result14 = tq.get_market_data(
    field_list=[],  # 空列表返回所有字段
    stock_list=['600000.SH'],
    start_time='20250101',
    end_time='20250201',
    count=-1,
    dividend_type='none',
    period='1d',
    fill_data=True
)

if len(result14) > 0:
    print(f"\n可用字段列表:")
    for i, col in enumerate(list(result14.keys()), 1):
        print(f"  {i:2d}. {col}")

# ============================================================================
# 示例15: 直接使用返回的字典
# ============================================================================
print("\n" + "=" * 80)
print("示例15: 直接使用返回的字典进行数据分析")
print("=" * 80)

result15 = tq.get_market_data(
    field_list=['Open', 'High', 'Low', 'Close', 'Volume'],
    stock_list=['600000.SH'],
    start_time='20250101',
    end_time='20250201',
    count=-1,
    dividend_type='none',
    period='1d',
    fill_data=True
)

# 直接使用字典中的DataFrame
print(f"\n收盘价统计:")
if 'Close' in result15:
    close_df = result15['Close']
    print(f"- 数据点数: {len(close_df)}")
    print(f"- 最高价: {close_df.max().max():.2f}")
    print(f"- 最低价: {close_df.min().min():.2f}")
    print(f"\n收盘价前10天:")
    print(close_df.head(10))

# ============================================================================
# 数据格式说明
# ============================================================================
print("\n" + "=" * 80)
print("数据格式说明")
print("=" * 80)
print("""
get_market_data 返回格式:
{
    'Open': DataFrame,      # 开盘价
    'High': DataFrame,      # 最高价
    'Low': DataFrame,       # 最低价
    'Close': DataFrame,     # 收盘价
    'Volume': DataFrame,    # 成交量(手)
    'Amount': DataFrame,    # 成交额(万元)
    ...
}

每个DataFrame的行索引为日期，列为股票代码

使用辅助函数 get_stock_df() 可以将字典转换为单只股票的DataFrame，
方便进行分析和处理。
""")

print("\n" + "=" * 80)
print("所有测试完成!")
print("=" * 80)

# 关闭连接
tq.close()
print("\n连接已关闭")
