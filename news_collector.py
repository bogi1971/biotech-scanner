# news_collector.py - COMPLETE VERSION (RSS, Scraping, KI & Telegram)

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import time
import re

# -------------------------------------------------------------------
# WICHTIG: Import deiner eigenen Module!
# Da ich die genauen Namen in deinen Dateien nicht kenne, 
# nutze ich hier Platzhalter (analyze_score, get_eps_data, send_to_telegram).
# -------------------------------------------------------------------
try:
    from ai_engines import analyze_score, get_eps_data
    from alerts import send_to_telegram
except ImportError:
    print("⚠️ Warnung: Eigene Module nicht gefunden. Nutze Fallback-Funktionen.")
    def analyze_score(text): return 0
    def get_eps_data(text): return 0
    def send_to_telegram(msg): print(f"TELEGRAM-MOCK: {msg}")

class NewsCollector:
    def __init__(self):
        print("🔥 RSS & SCRAPING NEWS COLLECTOR (KI & Telegram Edition)")
        
        self.sources = {
            'endpoints': 'https://endpts.com/feed/',
            'fierce_pharma': 'https://www.fiercepharma.com/rss.xml',
            'fierce_biotech': 'https://www.fiercebiotech.com/rss.xml',
            'stat_news': 'https://www.statnews.com/feed/',
            'fda_news': 'https://www.fda.gov/news-events/newsroom/rss.xml',
            'ema_news': 'https://www.ema.europa.eu/en/news/rss.xml',
            'biospace': 'https://www.biospace.com/rss/news',
            'genengnews': 'https://www.genengnews.com/feed/',
            'medpage_today': 'https://www.medpagetoday.com/rss/headlines.xml',
        }
        self.seen_urls = set()
    
    def fetch_rss(self, url: str, source_name: str) -> List[Dict]:
        try:
            feed = feedparser.parse(url)
            articles = []
            for entry in feed.entries[:10]:
                if entry.link not in self.seen_urls:
                    articles.append({
                        'title': entry.get('title', ''),
                        'summary': entry.get('summary', entry.get('description', '')),
                        'link': entry.link,
                        'published': entry.get('published', ''),
                        'source': source_name
                    })
                    self.seen_urls.add(entry.link)
            return articles
        except Exception as e:
            print(f"   ⚠️  {source_name}: {str(e)[:40]}")
            return []
    
    def fetch_fda_direct(self) -> List[Dict]:
        try:
            url = "https://www.fda.gov/drugs/drug-approvals-and-databases/drug-approvals-and-databases"
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = []
            links = soup.find_all('a', href=re.compile('approval'))
            
            for link in links[:5]:
                title = link.get_text().strip()
                if title and 'approval' in title.lower():
                    href = link.get('href', '')
                    if href.startswith('/'):
                        href = 'https://www.fda.gov' + href
                    
                    if href not in self.seen_urls:
                        articles.append({
                            'title': f"FDA: {title}",
                            'summary': 'FDA Drug Approval',
                            'link': href,
                            'published': datetime.now().isoformat(),
                            'source': 'fda_direct'
                        })
                        self.seen_urls.add(href)
            return articles
        except Exception as e:
            print(f"   ⚠️  FDA direkt: {str(e)[:40]}")
            return []
    
    def fetch_all(self) -> List[Dict]:
        all_news = []
        print("\n📰 Sammle News aus allen Quellen...")
        
        for name, url in self.sources.items():
            articles = self.fetch_rss(url, name)
            all_news.extend(articles)
        
        fda_articles = self.fetch_fda_direct()
        all_news.extend(fda_articles)
        
        return all_news
    
    def filter_biotech(self, articles: List[Dict], keywords: List[str]) -> List[Dict]:
        filtered = []
        for article in articles:
            text = f"{article['title']} {article['summary']}".lower()
            if any(kw.lower() in text for kw in keywords):
                article['matched_keywords'] = [kw for kw in keywords if kw.lower() in text]
                filtered.append(article)
        return filtered

if __name__ == "__main__":
    collector = NewsCollector()
    
    search_keywords = [
        "approval", "phase", "merger", "earnings", "acquisition",
        "Zulassung", "Übernahmeangebot", "Quartalszahlen"
    ]
    
    while True:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{current_time}] Starte neuen Sammel-Zyklus...")
        
        all_articles = collector.fetch_all()
        relevant_news = collector.filter_biotech(all_articles, search_keywords)
        
        print(f"🎯 {len(relevant_news)} relevante Biotech-Artikel gefunden.")
        
        for article in relevant_news:
            print(f"- {article['source'].upper()}: {article['title']}")
            
            text_to_analyze = f"{article['title']} {article['summary']}"
            
            # KI-Bewertung durchführen (anhand deiner ai_engines.py)
            score = analyze_score(text_to_analyze)
            eps_growth = get_eps_data(text_to_analyze)
            
            # Warnung nur auslösen, wenn Score > 7 UND EPS > 15%
            if score > 7 and eps_growth > 15:
                nachricht = f"🚨 HOT NEWS (Score: {score} | EPS: +{eps_growth}%)\n\n{article['title']}\n{article['link']}"
                send_to_telegram(nachricht)
            
        print("\n⏳ Warte 1 Stunde bis zur nächsten Ausführung...")
        time.sleep(3600)
