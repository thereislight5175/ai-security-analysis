# 数据源 API 格式记录

## 新浪财经

**K线数据**:
```
GET https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData
  ?symbol=sh600519
  &scale=240        # 240=日K
  &ma=no
  &datalen=120
```
返回: `[{"day":"2024-01-02","open":"1680.00","high":"1700.00","low":"1675.00","close":"1690.00","volume":"12345"}]`

## 东方财富

**K线数据**:
```
GET https://push2his.eastmoney.com/api/qt/stock/kline/get
  ?secid=1.600519   # 1.=SH, 0.=SZ
  &fields1=f1,f2,f3
  &fields2=f51,f52,f53,f54,f55,f56,f57
  &klt=101          # 101=日K
  &fqt=1            # 前复权
  &end=20500101
  &lmt=120
```
返回: `{"data":{"klines":["2024-01-02,1680.00,1700.00,1675.00,1690.00,12345,6543210"]}}`
字段: date, open, close, high, low, volume, amount

## 腾讯证券

**K线数据**:
```
GET https://web.ifzq.gtimg.cn/appstock/app/fqkline/get
  ?param=sh600519,day,,,120
```
返回: `{"data":{"sh600519":{"day":[["2024-01-02","1680.00","1700.00","1675.00","1690.00","12345"]]}}}`
字段: date, open, close, high, low, volume
