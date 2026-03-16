"""
    获取所有A股股票代码及名称测试示例
    
    本文件演示如何使用tqcenter获取A股股票列表
    包含多种获取方式:
    1. 获取所有A股
    2. 获取特定市场(上证主板、深证主板、创业板、科创板、北交所)
    3. 获取指数成分股
    4. 获取板块成分股
    5. 筛选特定股票
    6. 数据保存到文件
    
    使用前请确保:
    - 已启动通达信客户端并登录
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
# 示例1: 获取所有A股股票
# ============================================================================
print("=" * 80)
print("示例1: 获取所有A股股票")
print("=" * 80)

all_stocks = tq.get_stock_list('5')  # 5:所有A股
print(f"\n获取到 {len(all_stocks)} 只A股股票")
print(f"前20只股票:")
print(all_stocks[:20])

# ============================================================================
# 示例2: 获取不同市场的A股
# ============================================================================
print("\n" + "=" * 80)
print("示例2: 获取不同市场的A股")
print("=" * 80)

# 上证主板
sh_main = tq.get_stock_list('7')
print(f"\n上证主板: {len(sh_main)} 只")

# 深证主板
sz_main = tq.get_stock_list('8')
print(f"深证主板: {len(sz_main)} 只")

# 创业板
cyb = tq.get_stock_list('51')
print(f"创业板: {len(cyb)} 只")

# 科创板
kcb = tq.get_stock_list('52')
print(f"科创板: {len(kcb)} 只")

# 北交所
bjs = tq.get_stock_list('53')
print(f"北交所: {len(bjs)} 只")

# 沪深A股
hs_a = tq.get_stock_list('50')
print(f"沪深A股: {len(hs_a)} 只")

# ============================================================================
# 示例3: 获取主要指数成分股
# ============================================================================
print("\n" + "=" * 80)
print("示例3: 获取主要指数成分股")
print("=" * 80)

# 沪深300
hs300 = tq.get_stock_list('23')
print(f"\n沪深300成分股: {len(hs300)} 只")
print(f"前10只: {hs300[:10]}")

# 中证500
zz500 = tq.get_stock_list('24')
print(f"\n中证500成分股: {len(zz500)} 只")
print(f"前10只: {zz500[:10]}")

# 中证1000
zz1000 = tq.get_stock_list('25')
print(f"\n中证1000成分股: {len(zz1000)} 只")
print(f"前10只: {zz1000[:10]}")

# 国证2000
gz2000 = tq.get_stock_list('26')
print(f"\n国证2000成分股: {len(gz2000)} 只")

# 中证A500
zza500 = tq.get_stock_list('28')
print(f"\n中证A500成分股: {len(zza500)} 只")

# ============================================================================
# 示例4: 获取基金相关品种
# ============================================================================
print("\n" + "=" * 80)
print("示例4: 获取基金相关品种")
print("=" * 80)

# ETF基金
etf = tq.get_stock_list('31')
print(f"\nETF基金: {len(etf)} 只")
print(f"前10只: {etf[:10]}")

# 可转债
convertible_bonds = tq.get_stock_list('32')
print(f"\n可转债: {len(convertible_bonds)} 只")

# LOF基金
lof = tq.get_stock_list('33')
print(f"\nLOF基金: {len(lof)} 只")

# 所有可交易基金
all_funds = tq.get_stock_list('34')
print(f"\n所有可交易基金: {len(all_funds)} 只")

# ============================================================================
# 示例5: 获取股票详细信息(代码和名称)
# ============================================================================
print("\n" + "=" * 80)
print("示例5: 获取股票详细信息")
print("=" * 80)

# 获取沪深300成分股的详细信息
hs300_stocks = tq.get_stock_list('23')
print(f"\n正在获取沪深300成分股详细信息...")

# 批量获取股票详细信息
stock_details = []
batch_size = 50  # 每次获取50只

for i in range(0, min(100, len(hs300_stocks)), batch_size):  # 只获取前100只作为示例
    batch = hs300_stocks[i:i+batch_size]
    print(f"  正在获取第 {i+1}-{min(i+batch_size, len(hs300_stocks))} 只...")
    
    for stock_code in batch:
        try:
            # 获取股票基本信息
            info = tq.get_stock_info(stock_code=stock_code, field_list=[])
            if info and len(info) > 0:
                # 提取股票名称（字段名可能是'StockName'或'Name'）
                stock_name = '未知'
                if 'StockName' in info:
                    stock_name = info['StockName']
                elif 'Name' in info:
                    stock_name = info['Name']
                
                stock_details.append({
                    'StockCode': stock_code,
                    'StockName': stock_name
                })
        except Exception as e:
            print(f"  获取 {stock_code} 失败: {e}")

print(f"\n成功获取 {len(stock_details)} 只股票的详细信息:")
print(stock_details[:10])

# 转换为DataFrame
df_stocks = pd.DataFrame(stock_details)
print(f"\nDataFrame预览:")
print(df_stocks.head(10))

# ============================================================================
# 示例6: 筛选特定股票
# ============================================================================
print("\n" + "=" * 80)
print("示例6: 筛选特定股票")
print("=" * 80)

# 筛选沪市股票
sh_stocks = [s for s in all_stocks if s.endswith('.SH')]
print(f"\n沪市A股: {len(sh_stocks)} 只")
print(f"前10只: {sh_stocks[:10]}")

# 筛选深市股票
sz_stocks = [s for s in all_stocks if s.endswith('.SZ')]
print(f"\n深市A股: {len(sz_stocks)} 只")
print(f"前10只: {sz_stocks[:10]}")

# 筛选特定代码前缀
stocks_600xxx = [s for s in all_stocks if s.startswith('600')]
print(f"\n600开头的股票: {len(stocks_600xxx)} 只")

stocks_000xxx = [s for s in all_stocks if s.startswith('000')]
print(f"000开头的股票: {len(stocks_000xxx)} 只")

# ============================================================================
# 示例7: 获取板块列表
# ============================================================================
print("\n" + "=" * 80)
print("示例7: 获取板块列表")
print("=" * 80)

block_list = tq.get_sector_list()
print(f"\n共获取到 {len(block_list)} 个板块")
print(f"\n前20个板块:")
for i, block in enumerate(block_list[:20], 1):
    print(f"  {i:2d}. {block}")

# ============================================================================
# 示例8: 获取板块成分股
# ============================================================================
print("\n" + "=" * 80)
print("示例8: 获取板块成分股")
print("=" * 80)

# 通过板块代码获取
block_stocks1 = tq.get_stock_list_in_sector('880081.SH')  # 某个板块代码
print(f"\n板块880081.SH的成分股: {len(block_stocks1)} 只")
print(block_stocks1[:10])

# 通过板块名称获取
block_stocks2 = tq.get_stock_list_in_sector('钛金属')
print(f"\n钛金属板块的成分股: {len(block_stocks2)} 只")
print(block_stocks2[:10])

# ============================================================================
# 示例9: 保存股票列表到文件
# ============================================================================
print("\n" + "=" * 80)
print("示例9: 保存股票列表到文件")
print("=" * 80)

# 保存所有A股列表
output_path1 = str(Path(__file__).parent.parent.parent / 'data' / 'all_a_stocks.txt')
with open(output_path1, 'w', encoding='utf-8') as f:
    for stock in all_stocks:
        f.write(f"{stock}\n")
print(f"\n所有A股列表已保存到: {output_path1}")

# 保存为CSV格式
df_all_stocks = pd.DataFrame({'StockCode': all_stocks})
output_path2 = str(Path(__file__).parent.parent.parent / 'data' / 'all_a_stocks.csv')
df_all_stocks.to_csv(output_path2, index=False, encoding='utf-8-sig')
print(f"所有A股CSV已保存到: {output_path2}")

# 保存有名称的股票列表
if len(stock_details) > 0:
    output_path3 = str(Path(__file__).parent.parent.parent / 'data' / 'stocks_with_name.csv')
    df_stocks.to_csv(output_path3, index=False, encoding='utf-8-sig')
    print(f"股票名称列表已保存到: {output_path3}")

# ============================================================================
# 示例10: 统计分析
# ============================================================================
print("\n" + "=" * 80)
print("示例10: 统计分析")
print("=" * 80)

print(f"\n股票统计:")
print(f"- 所有A股总数: {len(all_stocks)}")
print(f"- 沪市A股: {len(sh_stocks)}")
print(f"- 深市A股: {len(sz_stocks)}")
print(f"- 上证主板: {len(sh_main)}")
print(f"- 深证主板: {len(sz_main)}")
print(f"- 创业板: {len(cyb)}")
print(f"- 科创板: {len(kcb)}")
print(f"- 北交所: {len(bjs)}")
print(f"- 沪深300: {len(hs300)}")
print(f"- 中证500: {len(zz500)}")
print(f"- 中证1000: {len(zz1000)}")
print(f"- ETF基金: {len(etf)}")
print(f"- 可转债: {len(convertible_bonds)}")
print(f"- 板块数量: {len(block_list)}")

# 按市场统计
sh_count = len([s for s in all_stocks if s.endswith('.SH')])
sz_count = len([s for s in all_stocks if s.endswith('.SZ')])
bj_count = len([s for s in all_stocks if s.endswith('.BJ')])
print(f"\n按市场统计:")
print(f"- 上海市场(SH): {sh_count}")
print(f"- 深圳市场(SZ): {sz_count}")
print(f"- 北京市场(BJ): {bj_count}")

# 按代码前缀统计
prefix_stats = {}
for stock in all_stocks:
    prefix = stock[:3]
    if prefix not in prefix_stats:
        prefix_stats[prefix] = 0
    prefix_stats[prefix] += 1

print(f"\n按代码前缀统计(前10个):")
for prefix, count in sorted(prefix_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"- {prefix}: {count} 只")

# ============================================================================
# 示例11: 获取自选股和持仓股
# ============================================================================
print("\n" + "=" * 80)
print("示例11: 获取自选股和持仓股")
print("=" * 80)

# 获取自选股
try:
    my_stocks = tq.get_stock_list('0')
    print(f"\n自选股: {len(my_stocks)} 只")
    if len(my_stocks) > 0:
        print(my_stocks[:10])
except Exception as e:
    print(f"\n获取自选股失败: {e}")

# 获取持仓股
try:
    hold_stocks = tq.get_stock_list('1')
    print(f"\n持仓股: {len(hold_stocks)} 只")
    if len(hold_stocks) > 0:
        print(hold_stocks[:10])
except Exception as e:
    print(f"\n获取持仓股失败: {e} (可能无持仓或权限不足)")

# ============================================================================
# get_stock_list 参数说明
# ============================================================================
print("\n" + "=" * 80)
print("get_stock_list 参数说明")
print("=" * 80)
print("""
参数说明:
  0: 自选股
  1: 持仓股
  5: 所有A股
  6: 上证指数成份股
  7: 上证主板
  8: 深证主板
  9: 重点指数
  10: 所有板块指数
  11: 缺省行业板块
  12: 概念板块
  13: 风格板块
  14: 地区板块
  15: 缺省行业分类+概念板块
  16: 研究行业一级
  17: 研究行业二级
  18: 研究行业三级
  21: 含H股
  22: 含可转债
  23: 沪深300
  24: 中证500
  25: 中证1000
  26: 国证2000
  27: 中证2000
  28: 中证A500
  30: REITs
  31: ETF基金
  32: 可转债
  33: LOF基金
  34: 所有可交易基金
  35: 所有沪深基金
  36: T+0基金
  49: 金融类企业
  50: 沪深A股
  51: 创业板
  52: 科创板
  53: 北交所
  101: 国内期货
  102: 港股
  103: 美股
""")

print("\n" + "=" * 80)
print("所有测试完成!")
print("=" * 80)

# 关闭连接
tq.close()
print("\n连接已关闭")
