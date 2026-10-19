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

DEFAULT_STOCKS = {
    "600900": "长江电力",
    "600941": "中国移动",
    "601088": "中国神华",
    "600938": "中国海油",
    "000858": "五粮液",
    "600036": "招商银行",
    "000333": "美的集团",
    "601318": "中国平安",
    "600887": "伊利股份",
    "002142": "宁波银行",
    "601398": "工商银行",
    "000568": "泸州老窖",
    "600377": "宁沪高速",
    "603288": "海天味业",
    "000423": "东阿阿胶",
    "605499": "东鹏饮料",
    "600809": "山西汾酒",
    "601000": "唐山港",
    "601857": "中国石油",
    "600600": "青岛啤酒",
    "000895": "双汇发展",
    "000538": "云南白药",
    "601728": "中国电信",
    "000429": "粤高速A",
    "600222": "华润江中",
    "000651": "格力电器",
    "600132": "重庆啤酒",
}

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
