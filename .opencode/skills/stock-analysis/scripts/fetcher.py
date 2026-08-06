import re
import json
import requests
from config import SOURCES, DEFAULT_DATA_LEN

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://finance.sina.com.cn",
}


def normalize_code(raw: str):
    raw = raw.strip().upper().replace(".", "")
    if raw.startswith("SH") or raw.startswith("SZ"):
        market = raw[:2].lower()
        code = raw[2:]
    elif raw.startswith("6") or raw.startswith("9"):
        market = "sh"
        code = raw
    elif raw.startswith("0") or raw.startswith("3") or raw.startswith("2"):
        market = "sz"
        code = raw
    elif raw.startswith("07") or raw.startswith("09"):
        market = "hk"
        code = raw
    else:
        market = "sh"
        code = raw
    return market, code


def fetch_sina(market, code):
    symbol = f"{market}{code}"
    params = {
        "symbol": symbol,
        "scale": 240,
        "ma": "no",
        "datalen": DEFAULT_DATA_LEN,
    }
    try:
        resp = requests.get(
            SOURCES["sina"]["kline_url"],
            params=params,
            headers=HEADERS,
            timeout=15,
        )
        data = resp.json()
        if not data or "day" not in data[0]:
            return None
        result = []
        for item in data:
            result.append({
                "day": item["day"],
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
                "volume": float(item.get("volume", 0)),
            })
        return result
    except Exception:
        return None


def fetch_eastmoney(market, code):
    secid_map = SOURCES["eastmoney"]["secid_map"]
    prefix = secid_map.get(market, "1.")
    secid = f"{prefix}{code}"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3",
        "fields2": "f51,f52,f53,f54,f55,f56,f57",
        "klt": "101",
        "fqt": "1",
        "end": "20500101",
        "lmt": DEFAULT_DATA_LEN,
    }
    try:
        resp = requests.get(
            SOURCES["eastmoney"]["kline_url"],
            params=params,
            headers=HEADERS,
            timeout=15,
        )
        raw = resp.json()
        klines = raw.get("data", {}).get("klines", [])
        if not klines:
            return None
        result = []
        fields_map = SOURCES["eastmoney"]["fields_map"]
        for line in klines:
            parts = line.split(",")
            result.append({
                "day": parts[0],
                "open": float(parts[1]),
                "close": float(parts[2]),
                "high": float(parts[3]),
                "low": float(parts[4]),
                "volume": float(parts[5]),
            })
        return result
    except Exception:
        return None


def fetch_tencent(market, code):
    symbol = f"{market}{code}"
    url = SOURCES["tencent"]["kline_url"]
    param_str = f"{symbol},day,,,{DEFAULT_DATA_LEN},qfq"
    try:
        resp = requests.get(
            url,
            params={"param": param_str},
            headers=HEADERS,
            timeout=15,
        )
        raw = resp.json()
        day_data = raw.get("data", {}).get(symbol, {}).get("qfqday", [])
        if not day_data:
            return None
        result = []
        for item in day_data:
            result.append({
                "day": item[0],
                "open": float(item[1]),
                "close": float(item[2]),
                "high": float(item[3]),
                "low": float(item[4]),
                "volume": float(item[5]) if len(item) > 5 else 0,
            })
        return result
    except Exception:
        return None


FETCHERS = {
    "sina": fetch_sina,
    "eastmoney": fetch_eastmoney,
    "tencent": fetch_tencent,
}


def fetch_all(market, code):
    results = {}
    for name, fetcher in FETCHERS.items():
        try:
            data = fetcher(market, code)
            if data:
                results[name] = data
        except Exception:
            continue
    return results
