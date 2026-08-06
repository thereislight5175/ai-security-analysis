from config import CONSENSUS_TOLERANCE, MIN_SOURCES_CONSISTENT


def build_date_index(sources_data):
    date_sources = {}
    for src_name, records in sources_data.items():
        for rec in records:
            d = rec["day"]
            if d not in date_sources:
                date_sources[d] = {}
            date_sources[d][src_name] = rec
    return date_sources


def pick_best_source(sources_data):
    """Pick the source with the most records as primary data."""
    best = max(sources_data.items(), key=lambda kv: len(kv[1]))
    return best[0], best[1]


def check_consistency(sources_data):
    if not sources_data:
        return None

    num_sources = len(sources_data)

    # Single source: use it directly
    if num_sources < MIN_SOURCES_CONSISTENT:
        src_name = list(sources_data.keys())[0]
        records = sources_data[src_name]
        return [
            {**r, "sources": [src_name]} for r in records
        ]

    # Multiple sources: build date index
    date_index = build_date_index(sources_data)
    dates = sorted(date_index.keys())

    # Use the most complete source as primary
    primary_name, primary_records = pick_best_source(sources_data)
    primary_by_date = {r["day"]: r for r in primary_records}

    consistent_dates = []
    total_dates = 0
    consistent_count = 0

    for d in dates:
        entries = date_index[d]
        close_prices = [v["close"] for v in entries.values()]
        total_dates += 1

        if len(close_prices) < MIN_SOURCES_CONSISTENT:
            continue

        ref = close_prices[0]
        max_diff = max(abs(p - ref) / ref for p in close_prices)
        if max_diff <= CONSENSUS_TOLERANCE:
            consistent_count += 1

        # Use primary source values, but annotate with all sources
        primary_entry = primary_by_date.get(d, list(entries.values())[0])
        consistent_dates.append({
            "day": d,
            "open": primary_entry["open"],
            "close": primary_entry["close"],
            "high": primary_entry["high"],
            "low": primary_entry["low"],
            "volume": primary_entry["volume"],
            "sources": list(entries.keys()),
        })

    if consistent_dates:
        pct = consistent_count / total_dates * 100 if total_dates > 0 else 0
        return {
            "records": consistent_dates,
            "primary_source": primary_name,
            "consistency_pct": round(pct, 1),
        }

    return None
