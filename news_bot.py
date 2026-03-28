import os
import feedparser
import requests
from datetime import datetime, timedelta, timezone
import time

# ======== 台灣新聞來源 ========
RSS_FEEDS = [
    ("中央社", "https://www.cna.com.tw/rss/aall.aspx"),
    ("聯合新聞網", "https://udn.com/rssfeed/news/2/6638?ch=news"),
    ("自由時報", "https://news.ltn.com.tw/rss/all.xml"),
    ("TVBS", "https://news.tvbs.com.tw/rss/news"),
]

MAX_ARTICLES = 5
HOURS = 24
# ==============================


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
            print(f"✅ {name}：抓到 {count} 則")
        except Exception as e:
            print(f"⚠️ {name} 失敗：{e}")

    return all_articles


def summarize_with_gemini(articles):
    api_key = os.environ["GEMINI_API_KEY"]

    articles_text = "\n\n".join([
        f"【{a['source']}】{a['title']}\n{a['summary']}\n連結：{a['link']}"
        for a in articles
    ])

    prompt = f"""以下是今日台灣新聞，請幫我整理成重點摘要。

要求：
- 選出最重要的 5~8 則
- 每則用 1~2 句話說明重點，用繁體中文
- 格式如下：

📌 標題
說明重點
🔗 連結

新聞內容：
{articles_text}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def send_telegram(text, token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    max_len = 4000
    chunks = [text[i:i+max_len] for i in range(0, len(text), max_len)]
    for chunk in chunks:
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": chunk,
            "disable_web_page_preview": True,
        }, timeout=15)
        if r.ok:
            print(f"✅ 發送成功（{len(chunk)} 字）")
        else:
            print(f"⚠️ 發送失敗：{r.text}")


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    today = datetime.now().strftime("%Y年%m月%d日")
    print(f"🚀 開始執行 {today}")

    send_telegram(f"📰 台灣每日新聞摘要\n{today}\n\n整理中，請稍候...", token, chat_id)

    articles = fetch_news()
    print(f"\n共抓到 {len(articles)} 則，交給 Gemini 整理...")

    summary = summarize_with_gemini(articles)
    send_telegram(summary, token, chat_id)
    send_telegram("✅ 今日摘要完成！", token, chat_id)
    print("🎉 完成！")


if __name__ == "__main__":
    main()
