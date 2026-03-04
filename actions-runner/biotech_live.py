import json
import re
import asyncio
import feedparser
import aiohttp
import telegram
import time
import logging
import os
import random
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from groq import Groq
import yfinance as yf

# --- LOGGING KONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('biotech_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- KONFIGURATION AUS UMEBUNGSVARIABLEN ---
GROQ_KEY = os.getenv("GROQ_KEY")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

if not all([GROQ_KEY, TG_TOKEN, TG_CHAT_ID]):
    logger.error("Fehlende Umgebungsvariablen!")
    logger.error("Bitte setzen: GROQ_KEY, TG_TOKEN, TG_CHAT_ID")
    raise ValueError("Fehlende Umgebungsvariablen: GROQ_KEY, TG_TOKEN, TG_CHAT_ID")

# --- DATENKLASSEN ---
@dataclass
class WatchlistEntry:
    timestamp: float
    score: int
    ticker: str

# --- ROTATING USER AGENTS ---
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15'
]

# --- KURS-ABFRAGE FUNKTION ---
async def get_market_data(ticker: str) -> Tuple[str, float, float]:
    try:
        loop = asyncio.get_event_loop()
        stock = await loop.run_in_executor(None, yf.Ticker, ticker)
        
        try:
            info = await loop.run_in_executor(None, lambda: stock.fast_info)
            price = getattr(info, 'last_price', None) or getattr(info, 'lastPrice', None)
            change_pct = getattr(info, 'day_change_percent', None) or getattr(info, 'dayChangePercent', None)
            
            if price is None:
                raise AttributeError("No price data")
                
        except (AttributeError, Exception) as e:
            logger.debug(f"FastInfo failed for {ticker}, trying regular info: {e}")
            info = await loop.run_in_executor(None, lambda: stock.info)
            price = info.get('regularMarketPrice', info.get('currentPrice', 0))
            prev_close = info.get('regularMarketPreviousClose', info.get('previousClose', 0))
            
            if price and prev_close and prev_close > 0:
                change_pct = ((price - prev_close) / prev_close) * 100
            else:
                change_pct = 0
        
        price = float(price) if price else 0.0
        change_pct = float(change_pct) if change_pct else 0.0
        
        if change_pct >= 5.0:
            status = "🚀 EXTREMER AUSBRUCH (>5%)"
        elif change_pct >= 3.0:
            status = "🟢 STARKER KAUFDRUCK (>3%)"
        elif change_pct > 0:
            status = "🟡 POSITIVER TREND"
        elif change_pct > -2:
            status = "⚪ NEUTRAL"
        else:
            status = "🔴 NEGATIV"
            
        return status, price, change_pct
        
    except Exception as e:
        logger.error(f"Fehler bei Kursabfrage für {ticker}: {e}")
        return "⚪ KURS NICHT VERFÜGBAR", 0.0, 0.0

# --- HAUPTKLASSE ---
class LiveScanner:
    def __init__(self):
        logger.info("🚀 BIOTECH SCANNER V11.3 - DAILY HEARTBEAT")
        
        self.client = Groq(api_key=GROQ_KEY)
        self.bot = telegram.Bot(token=TG_TOKEN)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Die sauberen und funktionierenden Quellen
        self.sources = {
            'stat_news': 'https://www.statnews.com/feed/',
            'endpts': 'https://endpts.com/feed/',
            'fierce_biotech': 'https://www.fiercebiotech.com/rss.xml',
            'ema_news': 'https://www.ema.europa.eu/en/news.xml',
            'biospace': 'https://www.biospace.com/rss'
        }
        
        self.backup_sources = {}
        
        self.seen_urls: Dict[str, float] = {}
        self.max_url_history = 5000
        
        self.watchlist: Dict[str, WatchlistEntry] = {}
        self.watchlist_timeout = 1800  # 30 Minuten
        
        # NEU: Variable für den täglichen Report
        self.last_status_date = None
        
        self.last_groq_call = 0
        self.groq_min_interval = 2
        
        self.keywords = [
            "zulassung", "approval", "pdufa", "fda", "ema", "chmp", "mhra",
            "fast track", "breakthrough", "orphan", "priority review",
            "accepted", "granted", "validation", "cleared", "green light",
            "recommendation", "designation", "topline", "positive", "significant",
            "met endpoint", "efficacy", "wirksamkeit", "phase 3", "phase 2",
            "successful", "readout", "meets primary", "statistically significant",
            "superiority", "interim data", "übernahmeangebot", "merger", "buyout",
            "acquisition", "offer", "partnership", "collaboration", "lizenzabkommen",
            "investment", "acquires", "takeover", "terms agreed", "joint venture",
            "quartalszahlen", "earnings", "beat", "profit", "guidance", "revenue",
            "upgrade", "analyst", "price target", "raised", "outperforms"
        ]

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=20)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _get_headers(self) -> dict:
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

    def _clean_url_history(self):
        if len(self.seen_urls) > self.max_url_history:
            sorted_urls = sorted(self.seen_urls.items(), key=lambda x: x[1])
            cutoff = int(len(sorted_urls) * 0.2)
            self.seen_urls = dict(sorted_urls[cutoff:])
            logger.info(f"URL-History bereinigt: {len(self.seen_urls)} Einträge verbleibend")

    async def fetch_feed(self, url: str) -> Optional[str]:
        headers = self._get_headers()
        
        for attempt in range(3):
            try:
                async with self.session.get(url, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 403:
                        logger.warning(f"403 Forbidden für {url}")
                        await asyncio.sleep(5 * (attempt + 1))
                    else:
                        logger.warning(f"HTTP {response.status} für {url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout bei {url}, Versuch {attempt + 1}/3")
            except Exception as e:
                logger.error(f"Fehler beim Abruf von {url}: {e}")
            
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(wait_time)
        
        return None

    async def analyze_with_groq(self, title: str) -> Optional[dict]:
        time_since_last = time.time() - self.last_groq_call
        if time_since_last < self.groq_min_interval:
            await asyncio.sleep(self.groq_min_interval - time_since_last)
        
        for attempt in range(3):
            try:
                self.last_groq_call = time.time()
                
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "Du bist ein präziser Biotech-Analyst. Antworte NUR im JSON-Format."
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Analysiere: '{title}'. "
                                "Bewerte die Kursrelevanz (1-10). "
                                "Nur bei eindeutig positiven News Score 8-10. "
                                "Bei negativen/neutralen News: Score 1-5. "
                                "Format: {\"score\": 8, \"ticker\": \"TICKER\", \"summary\": \"Deutsche Zusammenfassung\"}"
                            )
                        }
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0,
                    max_tokens=150
                )
                
                res = chat_completion.choices[0].message.content
                match = re.search(r'\{.*\}', res, re.DOTALL)
                
                if match:
                    data = json.loads(match.group())
                    return {
                        'score': int(data.get('score', 0)),
                        'ticker': data.get('ticker', 'N/A').upper().strip(),
                        'summary': data.get('summary', 'Keine Zusammenfassung')
                    }
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON Parse-Fehler: {e}")
            except Exception as e:
                logger.error(f"Groq API-Fehler (Versuch {attempt + 1}/3): {e}")
                await asyncio.sleep(2 ** attempt)
        
        return None

    async def send_telegram_alert(self, message: str):
        try:
            await self.bot.send_message(
                chat_id=TG_CHAT_ID,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
        except telegram.error.TelegramError as e:
            logger.error(f"Telegram-Fehler: {e}")

    async def check_watchlist(self):
        if not self.watchlist:
            return

        logger.info(f"👀 Prüfe {len(self.watchlist)} Watchlist-Einträge...")
        current_time = time.time()
        to_remove = []

        for ticker, entry in self.watchlist.items():
            if current_time - entry.timestamp > self.watchlist_timeout:
                logger.info(f"⏳ {ticker} von Watchlist entfernt (Timeout)")
                to_remove.append(ticker)
                continue
            
            try:
                status, price, change = await get_market_data(ticker)
                
                if change >= 3.0:
                    logger.info(f"🚀 NACHTRÄGLICHER AUSBRUCH: {ticker}")
                    
                    tv_link = f"https://www.tradingview.com/chart/?symbol={ticker}"
                    msg = (
                        f"🟢 <b>UPDATE: PREIS-AUSBRUCH!</b>\n\n"
                        f"Der Markt reagiert jetzt auf die News!\n\n"
                        f"📈 <b>{ticker}</b> (Urspr. Score: {entry.score}/10)\n"
                        f"Status: {status}\n"
                        f"Preis: ${price:.2f} (<b>{change:+.2f}%</b>)\n\n"
                        f"📊 <a href='{tv_link}'>TradingView Chart</a>"
                    )
                    
                    await self.send_telegram_alert(msg)
                    to_remove.append(ticker)
                else:
                    logger.debug(f"  -> {ticker}: {change:+.2f}%")
                    
            except Exception as e:
                logger.error(f"Fehler bei Watchlist-Check für {ticker}: {e}")

        for ticker in to_remove:
            self.watchlist.pop(ticker, None)

    async def process_news_item(self, entry, source_name: str):
        link = entry.link
        
        if link in self.seen_urls:
            return
        
        self.seen_urls[link] = time.time()
        self._clean_url_history()
        
        text_to_check = (entry.title + " " + entry.get('description', '')).lower()
        
        if not any(kw in text_to_check for kw in self.keywords):
            return
        
        logger.info(f"🎯 Keyword-Match in {source_name}: {entry.title[:60]}...")
        
        analysis = await self.analyze_with_groq(entry.title)
        
        if not analysis or analysis['score'] < 9:
            if analysis:
                logger.info(f"📉 Score zu niedrig ({analysis['score']}/10)")
            return
        
        ticker = analysis['ticker']
        
        status, price, change = await get_market_data(ticker)
        tv_link = f"https://www.tradingview.com/chart/?symbol={ticker}"
        
        msg = (
            f"{status}\n\n"
            f"🚀 <b>{ticker}</b> (Score: {analysis['score']}/10)\n"
            f"Preis: ${price:.2f} ({change:+.2f}%)\n\n"
            f"📝 {analysis['summary']}\n\n"
            f"📰 <i>{entry.title}</i>\n"
            f"Quelle: {source_name}\n\n"
            f"📊 <a href='{tv_link}'>Chart</a> | "
            f"<a href='{link}'>Original</a>"
        )
        
        await self.send_telegram_alert(msg)
        logger.info(f"✅ Alert gesendet für {ticker}")
        
        if change < 3.0 and ticker != 'N/A' and ticker not in self.watchlist:
            self.watchlist[ticker] = WatchlistEntry(
                timestamp=time.time(),
                score=analysis['score'],
                ticker=ticker
            )
            logger.info(f"📌 {ticker} auf Watchlist gesetzt")

    async def scan_cycle(self):
        logger.info("=" * 50)
        logger.info("🔄 STARTE SCAN-ZYKLUS")
        logger.info("=" * 50)
        
        # --- NEU: TÄGLICHER MORGEN-REPORT (Um 08:00 Uhr) ---
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        
        # Prüfen ob es 8 Uhr ist UND wir heute noch keinen Report gesendet haben
        if now.hour == 8 and self.last_status_date != current_date:
            try:
                status_msg = (
                    "🌅 <b>Guten Morgen! System läuft fehlerfrei.</b>\n\n"
                    "Dein Biotech-Scanner ist aktiv und überwacht die Märkte für dich. 🚀\n\n"
                    f"📡 <b>Feeds aktiv:</b> {len(self.sources)}\n"
                    f"👀 <b>Aktuell auf Watchlist:</b> {len(self.watchlist)} Ticker\n"
                    f"🤖 <b>KI-Modell:</b> Llama-3.3 (Online)"
                )
                await self.send_telegram_alert(status_msg)
                self.last_status_date = current_date
                logger.info("✅ Tägliches Morgen-Update gesendet!")
            except Exception as e:
                logger.error(f"Fehler beim Senden des Morgen-Reports: {e}")
        # ----------------------------------------------------

        await self.check_watchlist()
        
        tasks = []
        for source_name, url in self.sources.items():
            tasks.append(self._scan_single_source(source_name, url))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        logger.info(f"📊 {successful}/{len(self.sources)} Haupt-Feeds erfolgreich")
        
        if successful < 2:
            logger.info("🔄 Versuche Backup-Feeds...")
            for source_name, url in self.backup_sources.items():
                await self._scan_single_source(source_name, url)
        
        logger.info("💤 Zyklus beendet. Warte 5 Minuten...")
        await asyncio.sleep(300)

    async def _scan_single_source(self, source_name: str, url: str) -> bool:
        logger.info(f"📡 Lese: {source_name}")
        
        content = await self.fetch_feed(url)
        if not content:
            return False
        
        try:
            feed = feedparser.parse(content)
            
            if not feed.entries:
                logger.warning(f"Keine Einträge in {source_name}")
                return False
            
            for entry in feed.entries[:10]:
                await self.process_news_item(entry, source_name)
                await asyncio.sleep(0.5)
            
            return True
                
        except Exception as e:
            logger.error(f"Fehler beim Parsen von {source_name}: {e}")
            return False

    async def run(self):
        logger.info("Scanner gestartet. Drücke Ctrl+C zum Beenden.")
        
        try:
            while True:
                await self.scan_cycle()
        except asyncio.CancelledError:
            logger.info("Scanner wird beendet...")
        except Exception as e:
            logger.critical(f"Kritischer Fehler: {e}")
            raise

# --- START ---
if __name__ == "__main__":
    async def main():
        async with LiveScanner() as scanner:
            await scanner.run()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Scanner beendet")
