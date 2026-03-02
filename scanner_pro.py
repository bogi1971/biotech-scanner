import os, json, re, asyncio, feedparser, telegram
from google import genai # Nutzt das neue 2026-Paket

# ==========================================
# 1. DEINE DATEN (HIER EINTRAGEN)
# ==========================================
GEMINI_KEY = "AIzaSyBlvbSAcdo-GCI5f0Wnn0QTHJTjMq7sFhE"
TG_TOKEN = "8751621172:AAHRIaXibPNTwJl0mO4ShfX_q9dSpfiK0Sg"
TG_CHAT_ID = "5338135874"
# ==========================================

class BiotechScanner:
    def __init__(self):
        # Der moderne Client umgeht die 404-Fehler
        self.client = genai.Client(api_key=GEMINI_KEY)
        self.bot = telegram.Bot(token=TG_TOKEN)

    async def analyze(self, text):
        try:
            prompt = f"Analysiere Biotech-News: '{text}'. Antworte NUR JSON: {{'score': 8, 'ticker': 'TICKER', 'reason': 'Deutsch'}}"
            # Stabile Abfrage ohne v1beta-Pfad
            res = self.client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            return json.loads(re.search(r'\{.*\}', res.text, re.DOTALL).group())
        except Exception as e:
            print(f"⚠️ KI-Fehler: {e}")
            return {"score": 0}

    async def run(self):
        print("🚀 Scanner aktiv - Suche News...")
        feed = feedparser.parse("https://www.globenewswire.com/RssFeed/industry/1351/Biotechnology")
        
        for entry in feed.entries[:10]:
            print(f"🔎 Check: {entry.title[:50]}...")
            data = await self.analyze(entry.title)
            
            # Wir setzen den Score zum Testen auf 1, damit du SOFORT ein Signal siehst!
            if data.get('score', 0) >= 1: 
                msg = f"🚀 <b>{data.get('ticker', 'N/A')}</b> (Score: {data['score']}/10)\n\n{data.get('reason', '')}\n\n<a href='{entry.link}'>Link</a>"
                async with self.bot:
                    await self.bot.send_message(chat_id=TG_CHAT_ID, text=msg, parse_mode='HTML')
                print(f"✅ Alert gesendet für {data.get('ticker')}")
                break # Nur ein Test-Alert pro Lauf

if __name__ == "__main__":
    scanner = BiotechScanner()
    asyncio.run(scanner.run())
