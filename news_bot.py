import os
import feedparser
import requests
from datetime import datetime, timedelta, timezone
import time

RSS_FEEDS = [
    ("中央社", "https://www.cna.com.tw/rss/aall.aspx"),
    ("聯合新聞網", "https://udn.com/rssfeed/news/2/6638?ch=news"),
    ("自由時報", "https://news.ltn.com.tw/rss/all.xml"),
    ("TVBS", "https://news.tvbs.com.tw/rss/news"),
]

MAX_ARTICLES = 5
HOURS = 24


def fetch_news():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS)
    all_articles = []
    for name, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                if count >= MAX_ARTICLES:
                    break
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime.fromtimestamp(
                        time.mktime(entry.published_parsed), tz=timezone.utc
                    )
                if published is None or published >= cutoff:
                    all_articles.append({
                        "source": name,
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", "")[:300],
                        "link": entry.get("link", ""),
                    })
                    count += 1
            print(f"OK {name}: {count}")
        except Exception as e:
            print(f"FAIL {name}: {e}")
    return all_articles


def summarize_with_gemini(articles):
    api_key = os.environ["GEMINI_API_KEY"]
    articles_text = "\n\n".join([
        f"[{a['source']}] {a['title']}\n{a['summary']}\n{a['link']}"
        for a in articles
    ])
    prompt = f"以下是今日台灣新聞，請用繁體中文整理最重要的5~8則，每則2句說明重點並附連結：\n\n{articles_text}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def send_telegram(text, token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        requests.post(url, json={"chat_id": chat_id, "text": chunk, "disable_web_page_preview": True}, timeout=15)


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    today = datetime.now().strftime("%Y年%m月%d日")
    send_telegram(f"📰 台灣每日新聞摘要\n{today}\n\n整理中...", token, chat_id)
    articles = fetch_news()
    summary = summarize_with_gemini(articles)
    send_telegram(summary, token, chat_id)
    send_telegram("✅ 完成！", token, chat_id)


if __name__ == "__main__":
    main()
