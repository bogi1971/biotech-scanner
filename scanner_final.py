import os, sys, json, re, asyncio, feedparser, requests, telegram
from google import genai # Nutzt das moderne 2026-Paket

# --- KONFIGURATION ---
GEMINI_KEY = "AIzaSyBlvbSAcdo-GCI5f0Wnn0QTHJTjMq7sFhE"
TG_TOKEN = "8751621172:AAHRIaXibPNTwJl0mO4ShfX_q9dSpfiK0Sg"
TG_CHAT_ID = "5338135874"

# --- KI LOGIK (HybridAI direkt integriert) ---
class SimpleAI:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_KEY)
    def analyze(self, text):
        try:
            res = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=f"Biotech-Check: {text}. Antworte NUR JSON: {{'score': 8, 'ticker': 'ABC', 'summary': '...'}}"
            )
            return json.loads(re.search(r'\{.*\}', res.text, re.DOTALL).group())
        except: return {"score": 0}

# --- ALERTS (Telegram direkt integriert) ---
async def send_now(msg):
    try:
        bot = telegram.Bot(token=TG_TOKEN)
        async with bot:
            await bot.send_message(chat_id=TG_CHAT_ID, text=msg, parse_mode='HTML')
            print("✅ Alert gesendet!")
    except Exception as e: print(f"❌ Alert-Fehler: {e}")

# --- MAIN LOOP ---
async def main():
    ai = SimpleAI()
    print("🚀 Scanner gestartet (Standalone Mode 2026)")
    
    # Beispiel-Zyklus
    feed = feedparser.parse("https://www.globenewswire.com/RssFeed/industry/1351/Biotechnology")
    for entry in feed.entries[:5]:
        print(f"Prüfe: {entry.title}")
        result = ai.analyze(entry.title)
        if result.get('score', 0) >= 7:
            await send_now(f"<b>🚀 SIGNAL: {result['ticker']} (Score: {result['score']}/10)</b>\n{result['summary']}")
    
    print("💤 Zyklus beendet. Warte 15 Min...")

if __name__ == "__main__":
    asyncio.run(main())
