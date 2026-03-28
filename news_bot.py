import os
import feedparser
import requests
from datetime import datetime, timedelta, timezone
import time

RSS_FEEDS = [
    ("中央社", "https://www.cna.com.tw/rss/aall.aspx"),
    ("自由時報", "https://news.ltn.com.tw/rss/all.xml"),
    ("TVBS", "https://news.tvbs.com.tw/rss/news"),
]

def fetch_news():
    cutoff = datetime.now(timezone.utc) - timedelta(hou
