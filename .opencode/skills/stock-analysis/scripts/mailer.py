import os
import sys
import json
import io
import contextlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from config import SKILL_DIR

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


def send_email(cfg, text_result):
    msg = MIMEMultipart()
    msg["From"] = cfg["from_addr"]
    msg["To"] = cfg["to_addr"]
    msg["Subject"] = "[股票分析周报] %s" % cfg.get("stocks", [])

    body = MIMEText(text_result, "plain", "utf-8")
    msg.attach(body)

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

    from stock_analysis import analyze_batch

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        analyze_batch([str(c) for c in cfg["stocks"]])

    content = "\n".join(
        line for line in buf.getvalue().splitlines()
        if not line.strip().startswith("[图表]")
    ).strip()

    send_email(cfg, content)


if __name__ == "__main__":
    run_and_mail()
