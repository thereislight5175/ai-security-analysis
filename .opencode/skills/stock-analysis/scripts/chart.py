import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from config import CHART_DIR, BUY_THRESHOLD, SELL_THRESHOLD


def _setup_chinese_font():
    for name in [
        "SimHei", "Microsoft YaHei", "WenQuanYi Zen Hei",
        "WenQuanYi Micro Hei", "Noto Sans CJK SC", "Noto Sans CJK JP",
        "DejaVu Sans",
    ]:
        try:
            plt.rcParams["font.sans-serif"] = [name]
            plt.rcParams["axes.unicode_minus"] = False
            fig, ax = plt.subplots()
            ax.set_title("测试")
            plt.close(fig)
            return name
        except Exception:
            continue
    return None


def generate_chart(records, zone_info, stock_label):
    os.makedirs(CHART_DIR, exist_ok=True)
    _setup_chinese_font()

    chart_records = records[-30:] if len(records) >= 30 else records
    dates = [datetime.strptime(r["day"], "%Y-%m-%d") for r in chart_records]
    closes = [r["close"] for r in chart_records]

    buy_line = zone_info["buy_line"]
    sell_line = zone_info["sell_line"]
    current_price = zone_info["current_price"]
    ma120 = zone_info["ma120"]

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(dates, closes, "b-o", linewidth=2, markersize=4, label="收盘价")

    ax.axhline(y=buy_line, color="green", linestyle="--", linewidth=1.5,
               label=f"买入线 (MA120×{BUY_THRESHOLD}) = {buy_line:.2f}")
    ax.axhline(y=sell_line, color="red", linestyle="--", linewidth=1.5,
               label=f"卖出线 (MA120×{SELL_THRESHOLD}) = {sell_line:.2f}")

    ax.axhspan(0, buy_line, alpha=0.08, color="green", label="买入区间")
    ax.axhspan(buy_line, sell_line, alpha=0.08, color="gray", label="等待区间")
    ymax = max(closes + [sell_line]) * 1.05
    ax.axhspan(sell_line, ymax, alpha=0.08, color="red", label="卖出区间")

    ax.axhline(y=current_price, color="orange", linestyle=":", linewidth=1,
               alpha=0.7, label=f"当前价 = {current_price:.2f}")
    ax.plot(dates[-1], closes[-1], "o", color="orange", markersize=8)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    fig.autofmt_xdate()

    zone_text = {"buy": "买入区间", "sell": "卖出区间", "wait": "等待区间"}
    zone_color = {"buy": "green", "sell": "red", "wait": "gray"}
    current_zone = zone_text[zone_info["zone"]]

    ax.set_title(f"{stock_label}  最近{len(chart_records)}日走势  |  "
                 f"MA120={ma120:.2f}  |  当前区间: {current_zone}",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("日期")
    ax.set_ylabel("价格")
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, alpha=0.3)

    safe_name = stock_label.replace("/", "_").replace(":", "_")
    chart_path = os.path.join(CHART_DIR, f"{safe_name}.png")
    plt.tight_layout()
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)
    return chart_path
