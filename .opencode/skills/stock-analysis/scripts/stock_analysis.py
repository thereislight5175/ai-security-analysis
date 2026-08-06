import sys
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from fetcher import normalize_code, fetch_all
from consensus import check_consistency
from indicator import calc_ma120, determine_zone
from estimator import estimate_wait_days
from chart import generate_chart

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


def analyze_stock(code, name=None):
    market, raw_code = normalize_code(code)
    display_code = f"{market.upper()}{raw_code}"

    print(f"\n[获取数据] {name or display_code} ({display_code}) ...")

    sources_data = fetch_all(market, raw_code)
    if not sources_data:
        print("[错误] 所有数据源均获取失败，请检查网络或股票代码。")
        return

    active = list(sources_data.keys())
    print(f"   数据来源: {', '.join(SOURCE_NAMES[s] for s in active)}")

    result = check_consistency(sources_data)
    if not result:
        print("[错误] 各数据源数据不一致，无法分析。详情：")
        for src, data in sources_data.items():
            days = [r["day"] for r in data]
            print(f"   {SOURCE_NAMES[src]}: {len(days)} 条, {days[0]} ~ {days[-1]}")
        return

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
        buy_days = estimate_wait_days(records, current_price, zone_info["buy_line"])
        sell_days = estimate_wait_days(records, current_price, zone_info["sell_line"])

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
    return zone_info


def main():
    parser = argparse.ArgumentParser(description="Stock Analysis Skill")
    parser.add_argument("codes", nargs="+", help="Stock code(s), e.g. 600519")
    parser.add_argument("--name", "-n", help="Stock display name")
    args = parser.parse_args()

    if len(args.codes) == 1:
        analyze_stock(args.codes[0], name=args.name)
    else:
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(analyze_stock, c): c for c in args.codes}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"[错误] {futures[future]}: {e}")


if __name__ == "__main__":
    main()
