import json, re, asyncio, feedparser, requests, telegram
from groq import Groq

# --- CONFIGURATION ---
# Ersetze diese Werte mit deinen echten Keys!
GROQ_KEY = "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"
TG_TOKEN = "8751621172:AAHRIaXibPNTwJl0mO4ShfX_q9dSpfiK0Sg"
TG_CHAT_ID = "5338135874"

class LiveScanner:
    def __init__(self):
        print("🚀 BIOTECH SCANNER V5 - GROQ EDITION (24/7 MODE)")
        self.client = Groq(api_key=GROQ_KEY)
        self.bot = telegram.Bot(token=TG_TOKEN)
        
        # Deine 7 Biotech-Topquellen
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
        
        # Deine optimierte "Positive-Only" Liste [cite: 2026-01-16]
        self.keywords = [
            # Zulassungen & Behörden (EU & USA)
            "zulassung", "approval", "pdufa", "fda", "ema", "chmp", "mhra", 
            "fast track", "breakthrough", "orphan", "priority review", 
            "accepted", "granted", "validation",

            # Studienerfolge (Positive Daten)
            "topline", "positive", "significant", "met endpoint", "efficacy", 
            "wirksamkeit", "phase 3", "phase 2", "successful", "readout",

            # Firmen-Wachstum & M&A
            "übernahmeangebot", "merger", "buyout", "acquisition", "offer", 
            "partnership", "collaboration", "lizenzabkommen", "investment",

            # Finanzieller Erfolg
            "quartalszahlen", "earnings", "beat", "profit", "guidance", "revenue",
            "upgrade", "analyst", "price target"
        ]

    async def check_news(self):
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        while True:
            print("\n" + "="*50)
            print("🔄 STARTE NEUEN SCAN-ZYKLUS...")
            print("="*50)

            for source_name, url in self.sources.items():
                print(f"\n📡 Lese Feed: {source_name.upper()}...")
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    feed = feedparser.parse(response.content)
                    
                    for entry in feed.entries[:10]: # Prüfe die letzten 10 News
                        link = entry.link
                        
                        if link in self.seen_urls:
                            continue
                        self.seen_urls.add(link)
                        
                        text_to_check = (entry.title + " " + entry.get('description', '')).lower()
                        
                        # Lokaler Keyword-Check (Türsteher)
                        if not any(kw in text_to_check for kw in self.keywords):
                            print(f"⏩ Unwichtig: {entry.title[:45]}...")
                            continue

                        print(f"🎯 POSITIVES KEYWORD! Sende an Groq KI: {entry.title[:50]}...")
                        
                        try:
                            # KI-Analyse mit Fokus auf Long-Chancen
                            chat_completion = self.client.chat.completions.create(
                                messages=[
                                    {
                                        "role": "system",
                                        "content": "Du bist ein Biotech-Analyst. Antworte NUR im JSON-Format."
                                    },
                                    {
                                        "role": "user",
                                        "content": f"Analysiere: {entry.title}. Gib einen Score (8-10) NUR für POSITIVE Nachrichten, die den Kurs steigen lassen könnten. Negative News = Score 1. Antwort-Format: {{'score': 8, 'ticker': 'TICKER', 'summary': 'Deutsch'}}"
                                    }
                                ],
                                model="llama-3.3-70b-versatile",
                                temperature=0,
                            )
                            
                            res = chat_completion.choices[0].message.content
                            match = re.search(r'\{.*\}', res, re.DOTALL)
                            
                            if match:
                                data = json.loads(match.group())
                                if data.get('score', 0) >= 10:
                                    msg = f"🚀 <b>{data.get('ticker', 'N/A')} (Score: {data['score']}/10)</b>\n{data.get('summary', '')}\n<a href='{link}'>Link öffnen</a>"
                                    async with self.bot:
                                        await self.bot.send_message(chat_id=TG_CHAT_ID, text=msg, parse_mode='HTML')
                                    print(f"✅ Telegram Alert gesendet!")
                                else:
                                    print(f"📉 Score zu niedrig ({data.get('score', 0)}/10) - Keine Nachricht.")
                        except Exception as e:
                            print(f"⚠️ KI-Fehler: {e}")
                        
                        # Kurze Pause für API-Limits
                        await asyncio.sleep(5)
                        
                except Exception as e:
                    print(f"⚠️ Fehler bei {source_name}: {e}")
            
            print("\n💤 Zyklus beendet. Warte 5 Minuten...")
            await asyncio.sleep(300)

if __name__ == "__main__":
    scanner = LiveScanner()
    asyncio.run(scanner.check_news())
