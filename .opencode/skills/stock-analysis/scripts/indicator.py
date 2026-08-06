import numpy as np
from config import MA_PERIOD, BUY_THRESHOLD, SELL_THRESHOLD


def calc_ma120(records):
    closes = [r["close"] for r in records]
    if len(closes) < MA_PERIOD:
        ma = np.mean(closes)
        actual_days = len(closes)
    else:
        ma = np.mean(closes[-MA_PERIOD:])
        actual_days = MA_PERIOD
    return ma, actual_days


def determine_zone(current_price, ma120):
    buy_line = ma120 * BUY_THRESHOLD
    sell_line = ma120 * SELL_THRESHOLD

    if current_price < buy_line:
        zone = "buy"
    elif current_price > sell_line:
        zone = "sell"
    else:
        zone = "wait"

    return {
        "zone": zone,
        "current_price": current_price,
        "ma120": round(ma120, 2),
        "buy_line": round(buy_line, 2),
        "sell_line": round(sell_line, 2),
    }
