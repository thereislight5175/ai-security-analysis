import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from config import CHART_DIR, SKILL_DIR

CONFIG_PATH = os.path.join(SKILL_DIR, "mail_config.json")

def load_config():
    # 优先使用环境变量（兼容 GitHub Actions）
    env_cfg = {}
    for key in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "FROM_ADDR", "TO_ADDR"):
        val = os.environ.get(key)
        if val:
            env_cfg[key.lower().replace("smtp_", "smtp_")] = val
    stock_list = os.environ.get("STOCK_LIST")
    if stock_list:
        env_cfg["stocks"] = stock_list.split(",")

    if env_cfg.get("smtp_host") and env_cfg.get("stocks"):
        env_cfg["smtp_port"] = int(env_cfg.get("smtp_port", 465))
        return env_cfg

    # 回退到本地文件
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    print("[邮件] 请配置邮箱，创建文件: %s" % CONFIG_PATH)
    print("""格式:
{
    "smtp_host": "smtp.qq.com",
    "smtp_port": 465,
    "smtp_user": "your@qq.com",
    "smtp_pass": "授权码",
    "from_addr": "your@qq.com",
    "to_addr": "target@example.com",
    "stocks": ["600036", "600660", "600690"]
}
或设置环境变量 SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_ADDR, TO_ADDR, STOCK_LIST
""")
    return None


def send_email(cfg, text_result, chart_paths):
    msg = MIMEMultipart()
    msg["From"] = cfg["from_addr"]
    msg["To"] = cfg["to_addr"]
    msg["Subject"] = "[股票分析周报] %s" % cfg.get("stocks", [])

    body = MIMEText(text_result, "plain", "utf-8")
    msg.attach(body)

    for path in chart_paths:
        p = Path(path)
        if p.exists():
            with open(p, "rb") as f:
                img = MIMEImage(f.read())
                img.add_header("Content-Disposition", "attachment", filename=p.name)
                msg.attach(img)

    try:
        if cfg["smtp_port"] == 465:
            server = smtplib.SMTP_SSL(cfg["smtp_host"], cfg["smtp_port"])
        else:
            server = smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"])
            server.starttls()
        server.login(cfg["smtp_user"], cfg["smtp_pass"])
        server.sendmail(cfg["from_addr"], cfg["to_addr"], msg.as_string())
        server.quit()
        print("[邮件] 发送成功 -> %s" % cfg["to_addr"])
    except Exception as e:
        print("[邮件] 发送失败: %s" % e)


def run_and_mail():
    cfg = load_config()
    if not cfg:
        return

    from fetcher import normalize_code, fetch_all
    from consensus import check_consistency
    from indicator import calc_ma120, determine_zone
    from estimator import estimate_wait_days
    from chart import generate_chart

    all_text = ""
    chart_paths = []

    for code in cfg["stocks"]:
        market, raw_code = normalize_code(str(code))
        display = "%s%s" % (market.upper(), raw_code)

        sources = fetch_all(market, raw_code)
        if not sources:
            all_text += "\n%s: 获取失败\n" % display
            continue

        result = check_consistency(sources)
        if not result:
            all_text += "\n%s: 数据不一致\n" % display
            continue

        records = result["records"] if isinstance(result, dict) else result
        close = records[-1]["close"]
        ma120, _ = calc_ma120(records)
        zone = determine_zone(close, ma120)
        zone["current_price"] = close

        lines = [
            "\n== %s ==" % display,
            "  当前价: %.2f" % close,
            "  MA120:  %.2f" % ma120,
            "  买入线: %.2f (MA120x0.88)" % zone["buy_line"],
            "  卖出线: %.2f (MA120x1.12)" % zone["sell_line"],
        ]

        if zone["zone"] == "buy":
            lines.append("  判定: 买入区间 - 建议买入")
        elif zone["zone"] == "sell":
            lines.append("  判定: 卖出区间 - 建议卖出")
        else:
            lines.append("  判定: 等待区间 - 持有观察")
            bd = estimate_wait_days(records, close, zone["buy_line"])
            sd = estimate_wait_days(records, close, zone["sell_line"])
            if bd: lines.append("  预计买入需等: %d交易日" % bd)
            if sd: lines.append("  预计卖出需等: %d交易日" % sd)

        all_text += "\n".join(lines) + "\n"
        chart_path = generate_chart(records, zone, display)
        chart_paths.append(chart_path)

    send_email(cfg, all_text.strip(), chart_paths)


if __name__ == "__main__":
    run_and_mail()
