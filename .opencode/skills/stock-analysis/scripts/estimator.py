import numpy as np
from config import ESTIMATE_PERIOD


def estimate_wait_days(records, current_price, target_price):
    closes = [r["close"] for r in records]
    recent = closes[-ESTIMATE_PERIOD:]
    if len(recent) < 5:
        return None

    x = np.arange(len(recent))
    y = np.array(recent)
    slope, intercept = np.polyfit(x, y, 1)

    daily_change_rate = slope / intercept if intercept != 0 else 0
    if abs(daily_change_rate) < 1e-8:
        return None

    distance = target_price - current_price
    days = distance / (daily_change_rate * current_price)
    rounded = int(round(days))

    if rounded <= 0:
        return None
    return rounded
