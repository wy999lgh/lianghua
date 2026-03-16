from tqcenter import tq
import time

'''
    利用此示例需要先在客户端下载全A股盘后数据，不然结果不准确

'''

tq.initialize(__file__)
#先获取A股全部股票
all_stocks = tq.get_stock_list(market='5')
print("正在处理，请等待...")

upn_stocks = []
mul_xg_result = tq.formula_process_mul_xg(
    formula_name='UPN',
    formula_arg='10',
    return_count=1,
    return_date=False,
    stock_list=all_stocks,
    stock_period='1d',
    count=5,
    dividend_type=1)
# print(mul_xg_result)

if mul_xg_result:
    for key in mul_xg_result:
        if key != "ErrorId":
            if mul_xg_result[key]['UP3'] and mul_xg_result[key]['UP3'][-1] == '1':
                upn_stocks.append(key)

print("符合UPN公式选股条件的股票列表：")
print(upn_stocks)
print("符合UPN公式选股条件的股票数量：", len(upn_stocks))


