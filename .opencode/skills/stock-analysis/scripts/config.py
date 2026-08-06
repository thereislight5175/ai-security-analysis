import os

BUY_THRESHOLD = 0.88
SELL_THRESHOLD = 1.12
CONSENSUS_TOLERANCE = 0.005
MIN_SOURCES_CONSISTENT = 2
MA_PERIOD = 120
CHART_DAYS = 30
ESTIMATE_PERIOD = 20
DEFAULT_DATA_LEN = 120

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHART_DIR = os.path.join(SKILL_DIR, "charts")

SOURCES = {
    "sina": {
        "name": "新浪财经",
        "kline_url": "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData",
        "real_url": "https://hq.sinajs.cn/list",
        "fields": ["day", "open", "high", "low", "close", "volume"],
    },
    "eastmoney": {
        "name": "东方财富",
        "kline_url": "https://push2his.eastmoney.com/api/qt/stock/kline/get",
        "secid_map": {"sh": "1.", "sz": "0.", "hk": "116."},
        "fields_map": {"f51": "day", "f52": "open", "f53": "close", "f54": "high", "f55": "low", "f56": "volume"},
    },
    "tencent": {
        "name": "腾讯证券",
        "kline_url": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
    },
}
