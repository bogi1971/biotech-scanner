# news_collector.py - MIT WEB-SCRAPING

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import re
# Test-Start
class NewsCollector:
    def __init__(self):
        print("🔥 WEB-SCRAPING NEWS COLLECTOR V3")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.seen_urls = set()
    
    def scrape_endpoints(self) -> List[Dict]:
        """Endpoints direkt scrapen"""
        try:
            url = "https://endpoints.news/"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = []
            # Suche nach Artikel-Links
            for link in soup.find_all('a', href=re.compile('/\\d{4}/\\d{2}/')):
                title = link.get_text().strip()
                href = link.get('href', '')
                
                if title and href and href not in self.seen_urls:
                    if not href.startswith('http'):
                        href = 'https://endpoints.news' + href
                    
                    articles.append({
                        'title': title,
                        'summary': 'Endpoints News Article',
                        'link': href,
                        'published': datetime.now().isoformat(),
                        'source': 'endpoints_web'
                    })
                    self.seen_urls.add(href)
            
            return articles[:10]
        except Exception as e:
            print(f"   ⚠️  Endpoints Web: {str(e)[:40]}")
            return []
    
    def scrape_fierce_biotech(self) -> List[Dict]:
        """Fierce Biotech direkt scrapen"""
        try:
            url = "https://www.fiercebiotech.com/"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = []
            for link in soup.find_all('a', href=re.compile('/\\d{4}-')):
                title_elem = link.find(['h2', 'h3', 'span', 'div'], class_=re.compile('title|headline'))
                title = title_elem.get_text().strip() if title_elem else link.get_text().strip()
                href = link.get('href', '')
                
                if title and href and len(title) > 20 and href not in self.seen_urls:
                    if not href.startswith('http'):
                        href = 'https://www.fiercebiotech.com' + href
                    
                    articles.append({
                        'title': title,
                        'summary': 'Fierce Biotech Article',
                        'link': href,
                        'published': datetime.now().isoformat(),
                        'source': 'fierce_biotech_web'
                    })
                    self.seen_urls.add(href)
            
            return articles[:10]
        except Exception as e:
            print(f"   ⚠️  Fierce Biotech Web: {str(e)[:40]}")
            return []
    
    def fetch_all(self) -> List[Dict]:
        """Alle Quellen scrapen"""
        all_news = []
        
        print("\n📰 Scrape News aus Webseiten...")
        print("="*50)
        
        print(f"📡 Endpoints (Web)...")
        articles = self.scrape_endpoints()
        all_news.extend(articles)
        print(f"   ✅ {len(articles)} Artikel")
        
        print(f"📡 Fierce Biotech (Web)...")
        articles = self.scrape_fierce_biotech()
        all_news.extend(articles)
        print(f"   ✅ {len(articles)} Artikel")
        
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

