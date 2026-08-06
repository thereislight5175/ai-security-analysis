import os
import sys
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from fetcher import normalize_code, fetch_all
from consensus import check_consistency
from indicator import calc_ma120, determine_zone
from estimator import estimate_wait_days
from chart import generate_chart
from config import SKILL_DIR

SOURCE_NAMES = {
    "sina": "新浪财经",
    "eastmoney": "东方财富",
    "tencent": "腾讯证券",
}

ZONE_LABELS = {
    "buy": "[买入区间] — 建议买入",
    "sell": "[卖出区间] — 建议卖出",
    "wait": "[等待区间] — 建议持有观察",
}

ZONE_SHORT = {"buy": "买入", "sell": "卖出", "wait": "等待"}

KNOWN_STOCKS = {
    "600519": "贵州茅台",
    "600036": "招商银行",
    "600660": "福耀玻璃",
    "600690": "海尔智家",
    "600000": "浦发银行",
    "603508": "思维列控",
    "000858": "五粮液",
    "00700": "腾讯控股",
}

HISTORY_PATH = os.path.join(SKILL_DIR, "history.json")


def resolve_name(code, name=None):
    if name:
        return name
    market, raw = normalize_code(code)
    return KNOWN_STOCKS.get(raw, f"{market.upper()}{raw}")


def analyze_stock(code, name=None):
    market, raw_code = normalize_code(code)
    display_code = f"{market.upper()}{raw_code}"

    print(f"\n[获取数据] {name or display_code} ({display_code}) ...")

    sources_data = fetch_all(market, raw_code)
    if not sources_data:
        print("[错误] 所有数据源均获取失败，请检查网络或股票代码。")
        return None

    active = list(sources_data.keys())
    print(f"   数据来源: {', '.join(SOURCE_NAMES[s] for s in active)}")

    result = check_consistency(sources_data)
    if not result:
        print("[错误] 各数据源数据不一致，无法分析。详情：")
        for src, data in sources_data.items():
            days = [r["day"] for r in data]
            print(f"   {SOURCE_NAMES[src]}: {len(days)} 条, {days[0]} ~ {days[-1]}")
        return None

    if isinstance(result, dict):
        records = result["records"]
        primary = f"主数据源: {SOURCE_NAMES.get(result['primary_source'], result['primary_source'])}"
        print(f"   {primary}")
    else:
        records = result

    print(f"   获取 {len(records)} 个交易日数据 "
          f"({records[0]['day']} ~ {records[-1]['day']})")

    current_price = records[-1]["close"]
    ma120, actual_days = calc_ma120(records)
    zone_info = determine_zone(current_price, ma120)
    zone_info["current_price"] = current_price

    buy_days = estimate_wait_days(records, current_price, zone_info["buy_line"])
    sell_days = estimate_wait_days(records, current_price, zone_info["sell_line"])

    stock_label = name or display_code
    header = f"\n== {stock_label} ({display_code}) =="
    print(header)
    print("─" * len(header))
    print(f"当前价格:  {current_price:.2f}")
    print(f"MA120:     {ma120:.2f}  (基于 {actual_days} 日)")
    print(f"买入线:    {zone_info['buy_line']:.2f}  (MA120×0.88)")
    print(f"卖出线:    {zone_info['sell_line']:.2f}  (MA120×1.12)")
    print("─" * len(header))
    print(f"判定: {ZONE_LABELS[zone_info['zone']]}")

    if zone_info["zone"] == "wait":
        if buy_days:
            print(f"预计买入需等: ≈{buy_days} 个交易日")
        else:
            print(f"预计买入需等: 当前趋势远离买入线")

        if sell_days:
            print(f"预计卖出需等: ≈{sell_days} 个交易日")
        else:
            print(f"预计卖出需等: 当前趋势远离卖出线")

    print()
    chart_path = generate_chart(records, zone_info, stock_label)
    print(f"[图表] {chart_path}")
    return {
        "code": raw_code,
        "display_code": display_code,
        "label": stock_label,
        "zone": zone_info["zone"],
        "current_price": current_price,
        "ma120": zone_info["ma120"],
        "buy_line": zone_info["buy_line"],
        "sell_line": zone_info["sell_line"],
        "buy_days": buy_days,
        "sell_days": sell_days,
    }


def load_history():
    if not os.path.exists(HISTORY_PATH):
        return None
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_history(results):
    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "stocks": {
            r["code"]: {
                "close": r["current_price"],
                "sell_days": r["sell_days"],
            }
            for r in results
        },
    }
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def disp_width(s):
    return sum(2 if ord(ch) > 127 else 1 for ch in s)


def pad(s, width):
    return s + " " * max(0, width - disp_width(s))


def print_summary_table(results):
    print("\n========== 汇总表 ==========")
    headers = ["股票", "代码", "当前价", "MA120", "买入线", "卖出线", "判定", "卖出需等"]
    widths = [8, 10, 8, 8, 8, 8, 6, 12]
    print("  ".join(pad(h, w) for h, w in zip(headers, widths)))
    print("─" * 70)
    for r in results:
        sd = f"≈{r['sell_days']}交易日" if r["sell_days"] else "远离"
        row = [
            r["label"],
            r["display_code"],
            f"{r['current_price']:.2f}",
            f"{r['ma120']:.2f}",
            f"{r['buy_line']:.2f}",
            f"{r['sell_line']:.2f}",
            ZONE_SHORT[r["zone"]],
            sd,
        ]
        print("  ".join(pad(v, w) for v, w in zip(row, widths)))


def print_comparison(results):
    prev = load_history()
    if not prev or not prev.get("stocks"):
        return

    print(f"\n========== 对比上次 ({prev.get('date', '未知')}) ==========")
    prev_stocks = prev["stocks"]
    for r in results:
        p = prev_stocks.get(r["code"])
        if not p:
            continue
        pct = (r["current_price"] - p["close"]) / p["close"] * 100 if p["close"] else 0
        print(f"{r['label']:<8} 当前 {r['current_price']:.2f} vs 上次 {p['close']:.2f}"
              f"  ({pct:+.2f}%)")

        if r["sell_days"] and p.get("sell_days"):
            diff = r["sell_days"] - p["sell_days"]
            if diff > 0:
                print(f"         卖出等待延长 {diff} 天")
            elif diff < 0:
                print(f"         卖出等待缩短 {abs(diff)} 天")
            else:
                print("         卖出等待持平")

    weak = [r for r in results if r["current_price"] < r["ma120"]]
    if weak:
        weak_names = "、".join(f"{r['label']}({r['display_code']})" for r in weak)
        print(f"\n注意: {weak_names} 当前价低于 MA120，走势偏弱")

    below_buy = [r for r in results if r["zone"] == "buy"]
    above_sell = [r for r in results if r["zone"] == "sell"]
    wait = [r for r in results if r["zone"] == "wait"]
    parts = []
    if below_buy:
        parts.append(f"{len(below_buy)} 只处于买入区间")
    if above_sell:
        parts.append(f"{len(above_sell)} 只处于卖出区间")
    if wait:
        parts.append(f"{len(wait)} 只处于等待区间")
    if parts:
        print(f"区间分布: {', '.join(parts)}")


def analyze_batch(codes, names=None):
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(analyze_stock, c, (names or {}).get(c) or resolve_name(c)): c
            for c in codes
        }
        for future in as_completed(futures):
            try:
                r = future.result()
                if r:
                    results.append(r)
            except Exception as e:
                print(f"[错误] {futures[future]}: {e}")

    if len(results) > 1:
        print_summary_table(results)
        print_comparison(results)
    save_history(results)
    return results


def main():
    parser = argparse.ArgumentParser(description="Stock Analysis Skill")
    parser.add_argument("codes", nargs="+", help="Stock code(s), e.g. 600519")
    parser.add_argument("--name", "-n", help="Stock display name")
    args = parser.parse_args()

    if len(args.codes) == 1:
        analyze_stock(args.codes[0], name=args.name or resolve_name(args.codes[0]))
    else:
        names = {c: args.name} if args.name else {}
        analyze_batch(args.codes, names=names)


if __name__ == "__main__":
    main()
