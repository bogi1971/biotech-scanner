# main.py - HAUPTANWENDUNG (Trading Scanner)

import asyncio
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BIOTECH_KEYWORDS
from ai_engines import HybridAI
from news_collector import NewsCollector
from alerts import TelegramAlerter

class TradingScanner:
    def __init__(self):
        print("🚀 Biotech Trading Scanner v2.0")
        print("="*50)
        self.ai = HybridAI()
        self.collector = NewsCollector()
        self.alerter = TelegramAlerter(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.results = []
    
    async def run_once(self):
        """Ein Scan-Durchlauf"""
        print(f"\n🔍 Scan: {datetime.now().strftime('%H:%M:%S')}")
        
        # News sammeln
        all_news = self.collector.fetch_all()
        relevant = self.collector.filter_biotech(all_news, BIOTECH_KEYWORDS)
        print(f"📊 {len(relevant)} relevante Artikel")
        
        # Analysieren
        for article in relevant[:15]:
            full_text = f"{article['title']}\n{article['summary']}"
            analysis = self.ai.analyze(full_text)
            
            score = analysis['relevance_score']
            if score >= 7:
                print(f"🚨 {article['title'][:50]}... (Score: {score}/10)")
                await self.alerter.send_alert(article, analysis)
        
        print(f"✅ Fertig - {len(self.ai.trading_signals)} Signale heute")
    
    async def run_continuous(self):
        """Dauerhaft laufen"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        
        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.run_once, 'interval', minutes=15)
        scheduler.start()
        
        print("⏰ Scanner läuft (Ctrl+C zum Beenden)")
        await self.run_once()
        
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    scanner = TradingScanner()
    asyncio.run(scanner.run_continuous())