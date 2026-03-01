# news_collector.py - ERWEITERTE VERSION

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import json
import re

class NewsCollector:
    def __init__(self):
        print("🔥 ERWEITERTE NEWS COLLECTOR V2")
        
        # RSS-FEEDS
        self.sources = {
            # Bestehende
            'endpoints': 'https://endpts.com/feed/',
            'fierce_pharma': 'https://www.fiercepharma.com/rss.xml',
            'fierce_biotech': 'https://www.fiercebiotech.com/rss.xml',
            'stat_news': 'https://www.statnews.com/feed/',
            
            # NEU: Regulatory
            'fda_news': 'https://www.fda.gov/news-events/newsroom/rss.xml',
            'ema_news': 'https://www.ema.europa.eu/en/news/rss.xml',
            
            # NEU: Finanz/Investor
            'biospace': 'https://www.biospace.com/rss/news',
            'genengnews': 'https://www.genengnews.com/feed/',
            
            # NEU: Klinische Studien
            'medpage_today': 'https://www.medpagetoday.com/rss/headlines.xml',
        }
        
        self.seen_urls = set()
    
    def fetch_rss(self, url: str, source_name: str) -> List[Dict]:
        """RSS-Feed parsen"""
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
        """FDA Zulassungen direkt"""
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
        """Alle Quellen abrufen"""
        all_news = []
        
        print("\n📰 Sammle News aus allen Quellen...")
        print("="*50)
        
        # RSS-Feeds
        for name, url in self.sources.items():
            print(f"📡 {name}...")
            articles = self.fetch_rss(url, name)
            all_news.extend(articles)
            print(f"   ✅ {len(articles)} Artikel")
        
        # FDA Direkt
        print(f"🏛️  FDA Direkt...")
        fda_articles = self.fetch_fda_direct()
        all_news.extend(fda_articles)
        print(f"   ✅ {len(fda_articles)} Zulassungen")
        
        print("="*50)
        print(f"📊 GESAMT: {len(all_news)} Artikel")
        
        return all_news
    
    def filter_biotech(self, articles: List[Dict], keywords: List[str]) -> List[Dict]:
        """Nur relevante Biotech-News"""
        filtered = []
        for article in articles:
            text = f"{article['title']} {article['summary']}".lower()
            if any(kw.lower() in text for kw in keywords):
                article['matched_keywords'] = [
                    kw for kw in keywords if kw.lower() in text
                ]
                filtered.append(article)
        return filtered