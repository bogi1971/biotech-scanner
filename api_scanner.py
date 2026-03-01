# api_scanner.py - Scanner mit Gemini + Groq APIs

import asyncio
import json
from datetime import datetime
from config import GEMINI_API_KEY, GROQ_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BIOTECH_KEYWORDS
from ai_engines_api import HybridAI_API  # NEUE API-Version
from news_collector import NewsCollector
from alerts import TelegramAlerter

class APIScanner:
    def __init__(self):
        print("🤖 Initialisiere API-Scanner (Gemini + Groq)...")
        self.ai = HybridAI_API(GEMINI_API_KEY, GROQ_API_KEY)  # API-Version!
        self.collector = NewsCollector()
        self.alerter = TelegramAlerter(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.results = []
    
    async def run_once(self):
        """Ein Durchlauf mit APIs"""
        print(f"\n{'='*50}")
        print(f"🌐 API-Scan gestartet: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*50}")
        
        print("\n📰 Sammle News...")
        all_news = self.collector.fetch_all()
        print(f"   Insgesamt: {len(all_news)} Artikel")
        
        relevant = self.collector.filter_biotech(all_news, BIOTECH_KEYWORDS)
        print(f"   Relevant: {len(relevant)} Artikel")
        
        print("\n🧠 Starte KI-Analyse (APIs)...")
        print("   ⚠️  Achtung: API-Limits beachten!")
        
        for i, article in enumerate(relevant, 1):
            print(f"\n   [{i}/{len(relevant)}] {article['title'][:50]}...")
            
            full_text = f"{article['title']}\n{article['summary']}"
            analysis = self.ai.analyze(full_text)
            
            result = {
                'article': article,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            self.results.append(result)
            
            if analysis['relevance_score'] >= 7:
                print(f"   🚨 HOHE RELEVANZ! ({analysis['relevance_score']}/10)")
                print(f"   🤖 Engine: {analysis.get('engine', 'unknown')}")
                await self.alerter.send_alert(article, analysis)
            
            if i % 5 == 0:
                status = self.ai.get_status()
                print(f"   💰 API-Nutzung: Groq {status['groq_used']}, Gemini {status['gemini_used']}")
        
        # Vergleich anzeigen
        print(f"\n{'='*50}")
        print("📊 API-Scan Zusammenfassung:")
        print(f"   Gescannt: {len(relevant)} Artikel")
        
        high_priority = len([r for r in self.results if r['analysis']['relevance_score'] >= 7])
        print(f"   High Priority (≥7): {high_priority}")
        
        status = self.ai.get_status()
        print(f"   💰 API-Kosten:")
        print(f"      Groq: {status['groq_used']} Anfragen")
        print(f"      Gemini: {status['gemini_used']} Anfragen")
        print(f"   Engine-Nutzung: {status['last_engine']}")
        
        if status.get('failed_calls', 0) > 0:
            print(f"   ⚠️  Fehlgeschlagene API-Calls: {status['failed_calls']}")
        
        print(f"{'='*50}")
        
        self._save_results()
    
    def _save_results(self):
        """Ergebnisse speichern"""
        filename = f"api_scan_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"💾 Gespeichert: {filename}")
    
    async def run_continuous(self, interval_minutes: int = 60):  # Längeres Interval für APIs
        """Dauerhaft mit API-Limits"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        
        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.run_once, 'interval', minutes=interval_minutes)
        scheduler.start()
        
        print(f"⏰ API-Scheduler gestartet. Intervall: {interval_minutes} Minuten")
        print("⚠️  ACHTUNG: APIs haben Limits! Nicht zu häufig scannen.")
        print("Drücke Ctrl+C zum Beenden")
        
        try:
            await self.run_once()
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 API-Scanner beendet")
            scheduler.shutdown()

if __name__ == "__main__":
    scanner = APIScanner()
    asyncio.run(scanner.run_continuous(interval_minutes=60))  # Nur stündlich wegen Limits!