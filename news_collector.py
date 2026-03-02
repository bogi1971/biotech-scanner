import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import time
import re

# Import der KI-Engine und Alerts
try:
    from ai_engines import analyze_score
    from alerts import send_to_telegram
except ImportError:
    def analyze_score(text): return None
    def send_to_telegram(msg): print(f"TELEGRAM: {msg}")

class NewsCollector:
    def __init__(self):
        print("🚀 BIOTECH SCANNER V5 - DAYTRADING MODE")
        self.sources = {
            'endpoints': 'https://endpts.com/feed/',
            'fierce_biotech': 'https://www.fiercebiotech.com/rss.xml',
            'stat_news': 'https://www.statnews.com/feed/',
            'fda_news': 'https://www.fda.gov/news-events/newsroom/rss.xml',
            'ema_news': 'https://www.ema.europa.eu/en/news/rss.xml',
            'biospace': 'https://www.biospace.com/rss/news'
        }
        self.seen_urls = set()

    def fetch_all(self) -> List[Dict]:
        all_news = []
        for name, url in self.sources.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:10]:
                    if entry.link not in self.seen_urls:
                        all_news.append({
                            'title': entry.get('title', ''),
                            'summary': entry.get('summary', ''),
                            'link': entry.link,
                            'source': name
                        })
                        self.seen_urls.add(entry.link)
            except: continue
        return all_news

if __name__ == "__main__":
    collector = NewsCollector()
    # Erkennt auch europäische Begriffe [cite: 2026-01-16]
    keywords = ["approval", "phase", "merger", "acquisition", "Zulassung", "Übernahme", "Studie"]

    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scan läuft...")
        news = collector.fetch_all()
        
        for item in news:
            text = f"{item['title']} {item['summary']}"
            # Filtern nach Keywords
            if any(kw.lower() in text.lower() for kw in keywords):
                # KI-Analyse ohne feste Watchliste
                result = analyze_score(text)
                
                if result and result.get('score', 0) >= 7:
                    msg = (f"🚨 {result['direction']} | ${result['ticker']} (Score: {result['score']})\n"
                           f"📰 {result['summary']}\n🔗 {item['link']}")
                    send_to_telegram(msg)
                    print(f"✅ Alert gesendet: ${result['ticker']}")

        print("⏳ Warte 15 Minuten...")
        time.sleep(900) # Daytrading Takt: 15 Min [cite: 2026-01-21]

