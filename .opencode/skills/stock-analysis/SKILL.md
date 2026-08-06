---
name: stock-analysis
description: >
  Use when the user asks to analyze a stock, check stock price, query stock,
  evaluate buy/sell signal, or any Chinese stock market analysis request.
  Triggers on keywords like "股票", "股价", "分析", "stock", "买入", "卖出",
  "均线", "MA", or a stock code pattern like 600519 or SH600519.
---

# Stock Analysis Skill

Analyze Chinese A-share / HK / US stock prices using 120-day moving average (MA120) with 0.88 and 1.12 thresholds. Fetches data from multiple sources (Sina, East Money, Tencent), validates consistency, generates a chart, and outputs a buy/sell/wait recommendation.

## Usage

Run the analysis script with one or more stock codes:

```powershell
python .opencode\skills\stock-analysis\scripts\stock_analysis.py 600519
python .opencode\skills\stock-analysis\scripts\stock_analysis.py 600519 000858 00700
python .opencode\skills\stock-analysis\scripts\stock_analysis.py SH600519
python .opencode\skills\stock-analysis\scripts\stock_analysis.py 600519 --name "贵州茅台"
```

Supported code formats: `600519`, `SH600519`, `sh600519`, `600519.SH`.

## Workflow

1. Parse stock code(s) from user input
2. Fetch historical K-line data from Sina, East Money, and Tencent in parallel
3. Validate data consistency across sources (close price tolerance <= 0.5%)
4. Calculate MA120, buy line (MA120×0.88), sell line (MA120×1.12)
5. Determine zone: buy / sell / wait
6. If wait, estimate days using 20-day linear regression trend
7. Generate 30-day closing price chart with zone lines
8. Print analysis result and display chart

## Output Format

```
== 贵州茅台 (600519) ==
─────────────────────
当前价格:  1680.50
MA120:     1620.00
买入线:    1425.60 (MA120×0.88)
卖出线:    1814.40 (MA120×1.12)
─────────────────────
判定: [等待区间] — 建议持有观察
预计买入需等: ≈15 个交易日
预计卖出需等: ≈8 个交易日
─────────────────────
[图表] /path/to/chart.png
```
