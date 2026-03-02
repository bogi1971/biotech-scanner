import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
import asyncio
import sys
import os

# DER TRICK: Wir zwingen Python, im aktuellen Ordner zu suchen
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Jetzt die Integration deiner Module
try:
    from ai_engines import HybridAI
    from alerts import TelegramAlerter
    print("✅ Erfolg: ai_engines und alerts erfolgreich geladen!")
except ImportError as e:
    print(f"⚠️ Import-Fehler: {e}")
    # Minimal-Fallback
    class HybridAI:
        def analyze(self, text): return {"relevance_score": 0}
    class TelegramAlerter:
        def __init__(self, t, c): pass
        async def send_alert(self, a, b): print("Telegram-Mock")

class NewsCollector:
    def __init__(self):
        print("🚀 BIOTECH SCANNER V5 - DAYTRADING MODE ACTIVE")
        # 2026-01-21: Fokus auf schnelllebige RSS-Quellen
        self.sources = {
            'endpoints': 'https://endpts.com/feed/',
            'fierce_biotech': 'https://www.fiercebiotech.com/rss.xml',
            'stat_news': 'https://www.statnews.com/feed/',
            'fda_news': 'https://www.fda.gov/news-events/newsroom/rss.xml',
            'ema_news': 'https://www.ema.europa.eu/en/news/rss.xml',
            'biospace': 'https://www.biospace.com/rss/news',
            'genengnews': 'https://www.genengnews.com/feed/'
        }
        self.seen_urls = set()

    def fetch_all(self):
        """Sammelt News aus allen definierten Quellen."""
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
            except Exception as e:
                print(f"   ⚠️ Fehler bei {name}: {str(e)[:30]}")
        return all_news

    def filter_keywords(self, articles, keywords):
        """Vorfilterung basierend auf marktentscheidenden Begriffen."""
        filtered = []
        for article in articles:
            text = f"{article['title']} {article['summary']}".lower()
            if any(kw.lower() in text for kw in keywords):
                filtered.append(article)
        return filtered

async def main_loop():
    # --- KONFIGURATION ---
    # Hier deine echten Daten eintragen oder als Env-Variablen nutzen
    TELEGRAM_TOKEN = "DEIN_TELEGRAM_BOT_TOKEN"
    TELEGRAM_CHAT_ID = "DEINE_CHAT_ID"
    
    # Initialisierung
    collector = NewsCollector()
    ai_engine = HybridAI()
    alerter = TelegramAlerter(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    
    # 2026-01-16: Scanner erkennt englische und europäische Begriffe
    search_keywords = [
        "approval", "phase", "merger", "acquisition", "clinical trial",
        "Zulassung", "Übernahmeangebot", "Quartalszahlen", "Studie", "PDUFA"
    ]
    
    while True:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{current_time}] 🔎 Starte Scan-Zyklus...")
        
        # 1. Sammeln
        raw_articles = collector.fetch_all()
        
        # 2. Filtern nach Keywords (Vorauswahl für KI)
        relevant_news = collector.filter_keywords(raw_articles, search_keywords)
        print(f"🎯 {len(relevant_news)} News identifiziert. Starte KI-Analyse...")
        
        for article in relevant_news:
            # 3. KI-Analyse (Ticker-Erkennung & Trading-Score)
            # Nutzt deine HybridAI-Logik aus ai_engines.py
            analysis = ai_engine.analyze(f"{article['title']} {article['summary']}")
            
            # 4. Alert senden bei Trading-Signal (Score >= 7)
            # 2026-01-20: Ticker-Validierung erfolgt innerhalb der KI-Engine
            if analysis and analysis.get('relevance_score', 0) >= 7:
                await alerter.send_alert(article, analysis)
        
        # 2026-01-21: Daytrading-Intervall 15 Minuten
        print(f"⏳ Zyklus beendet. Warte 15 Minuten...")
        await asyncio.sleep(900)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n🛑 Scanner manuell gestoppt.")


