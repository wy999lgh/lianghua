from tqcenter import tq

'''
    利用此示例需要先在客户端下载全A股盘后数据，不然结果不准确
    通过MACD指标公式选出最新交易日金叉的股票
'''

tq.initialize(__file__)

#先获取A股全部股票
all_stocks = tq.get_stock_list(market='5')

print("正在处理，请等待...")

macd_stocks = []
mul_zb_result = tq.formula_process_mul_zb(
    formula_name='MACD',
    formula_arg='12,26,9',
    xsflag=6,
    return_count=2,
    return_date=False,
    stock_list=all_stocks,
    # stock_list=['600722.SH'],
    stock_period='1d',
    count=100,
    dividend_type=1)
# print(mul_zb_result)

if mul_zb_result:
    for key in mul_zb_result:
        if key != "ErrorId":
            if len(mul_zb_result[key]['DIF']) >= 2 and len(mul_zb_result[key]['DEA']) >= 2:
                if float(mul_zb_result[key]['DIF'][-2]) < float(mul_zb_result[key]['DEA'][-2]) and float(mul_zb_result[key]['DIF'][-1]) >= float(mul_zb_result[key]['DEA'][-1]):
                    macd_stocks.append(key)  


print("今日MACD金叉股票列表：")
print(macd_stocks)
print("符合MACD金叉条件的股票数量：", len(macd_stocks))
