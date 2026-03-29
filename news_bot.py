import os
import feedparser
import requests
from datetime import datetime, timedelta, timezone
import time

RSS_FEEDS = [
    ("中央社", "https://www.cna.com.tw/rss/aall.aspx"),
    ("自由時報", "https://news.ltn.com.tw/rss/all.xml"),
]


def fetch_news():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    all_articles = []
    for name, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                if count >= 5:
                    break
                all_articles.append({
                    "source": name,
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                })
                count += 1
        except Exception as e:
            print(f"FAIL {name}: {e}")
    return all_articles


def send_telegram(text, token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True}, timeout=15)
    print("TG:", r.status_code)


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    today = datetime.now().strftime("%Y年%m月%d日")
    articles = fetch_news()
    lines = [f"📰 台灣新聞 {today}\n"]
    for a in articles:
        lines.append(f"【{a['source']}】{a['title']}\n{a['link']}\n")
    send_telegram("\n".join(lines), token, chat_id)
    print("Done")


if __name__ == "__main__":
    main()
