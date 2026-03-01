# alerts.py - TRADING-OPTIMIERT

from telegram import Bot
import asyncio

class TelegramAlerter:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot = Bot(token=bot_token) if bot_token else None
        self.chat_id = str(chat_id) if chat_id else ""
    
    def _format_companies(self, companies) -> str:
        if not companies:
            return 'Keine erkannt'
        
        if isinstance(companies, str):
            return companies
        
        if isinstance(companies, list):
            names = []
            for c in companies:
                if isinstance(c, dict):
                    ticker = c.get('ticker', '')
                    name = c.get('name', '')
                    if ticker:
                        names.append(f"{name} (${ticker})")
                    else:
                        names.append(name)
                elif isinstance(c, str):
                    names.append(c)
            return ', '.join(names) if names else 'Keine erkannt'
        
        return str(companies)
    
    def _score_bar(self, score: int) -> str:
        filled = '█' * score
        empty = '░' * (10 - score)
        return f"[{filled}{empty}] {score}/10"
    
    def _get_direction_emoji(self, direction: str) -> str:
        emojis = {
            'LONG': '🟢📈',
            'SHORT': '🔴📉',
            'NEUTRAL/WATCH': '⚪',
            'LONG/SHORT': '🔵'
        }
        return emojis.get(direction, '⚪')
    
    async def send_alert(self, article: dict, analysis: dict):
        if not self.bot or not self.chat_id:
            return
            
        score = analysis.get('relevance_score', 5)
        pred = analysis.get('stock_prediction', {})
        metadata = analysis.get('trading_metadata', {})
        
        # Trading-spezifischer Header
        direction = pred.get('direction', 'NEUTRAL')
        
        if score >= 9:
            header = '🚨🔥🔥🔥 TRADING-SIGNAL SEHR STARK'
        elif score >= 7:
            header = '⚡🔥🔥 TRADING-SIGNAL STARK'
        elif score >= 5:
            header = '👁️🔥 RELEVANT (Prüfen)'
        else:
            header = '💤 Geringe Relevanz'
        
        # Short-Signal hervorheben
        is_short = direction == 'SHORT'
        short_warning = "⚠️ SHORT-SIGNAL! " if is_short else ""
        
        # Trading-Details
        strategy = pred.get('strategy', '')
        entry = pred.get('entry_timing', '')
        position = pred.get('position_size', '')
        stop = pred.get('stop_loss', '')
        
        # Sentiment
        sentiment = analysis.get('sentiment', 'Neutral')
        sent_emoji = {
            'Stark Positiv': '🟢🟢',
            'Positiv': '🟢',
            'Neutral': '⚪',
            'Negativ': '🔴',
            'Stark Negativ': '🔴🔴'
        }.get(sentiment, '⚪')
        
        # Firmen
        companies_str = self._format_companies(analysis.get('companies'))
        
        # Metadaten anzeigen
        meta = analysis.get('trading_metadata', {})
        events = meta.get('matched_events', [])
        events_text = '\n'.join([f"  • {e}" for e in events[:3]]) if events else "  • Keine klaren Trigger"
        
        message = f"""
{header}
<b>{short_warning}{article.get('title', 'Kein Titel')}</b>

━━━━━━━━━━━━━━━━━━━━━
🎯 <b>TRADING-SCORE</b>
━━━━━━━━━━━━━━━━━━━━━

<b>{self._score_bar(score)}</b>

<b>📊 Richtung:</b> {self._get_direction_emoji(direction)} {direction}
<b>💭 Sentiment:</b> {sent_emoji} {sentiment}
<b>📈 Strategie:</b> {strategy}

<b>🎯 Entry:</b> {entry}
<b>💰 Position:</b> {position}
<b>🛑 Stop-Loss:</b> {stop}

<b>📊 Erwartete Bewegung:</b> ±{pred.get('expected_move_percent', 0)}%
<b>✅ Konfidenz:</b> {pred.get('confidence', 'Unbekannt')}
<b>⏱️ Zeitfenster:</b> {pred.get('timeframe', 'Unbekannt')}

<b>🔍 Trigger-Events:</b>
{events_text}

<b>🏢 Firmen:</b> {companies_str}
<b>🏷️ Kategorie:</b> {analysis.get('category', 'Unbekannt')}

━━━━━━━━━━━━━━━━━━━━━
📝 <b>ANALYSE</b>
━━━━━━━━━━━━━━━━━━━━━
{analysis.get('summary_german', 'Keine Zusammenfassung')}

🔧 <i>Engine: {analysis.get('engine', 'unbekannt')}</i>
<a href='{article.get('link', '')}'>📰 Zum Artikel</a>
        """
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message[:4096],
                parse_mode='HTML',
                disable_web_page_preview=False
            )
            print(f"   ✅ Trading-Alert gesendet ({direction}, Score: {score}/10)")
        except Exception as e:
            print(f"   ❌ Telegram Fehler: {e}")
    
    async def send_status(self, status: dict):
        if not self.bot or not self.chat_id:
            return
        
        dist = status.get('score_distribution', {})
        dist_text = '\n'.join([f"  {k}: {v}" for k, v in dist.items()]) if dist else "  Keine Daten"
        
        trading = status.get('trading_signals', {})
        
        message = f"""
<b>📊 Trading-Scanner Status</b>

<b>📈 Trading-Signale heute:</b>
  • Total: {trading.get('total', 0)}
  • LONG: {trading.get('long', 0)} 🟢
  • SHORT: {trading.get('short', 0)} 🔴

<b>📊 Score-Verteilung:</b>
{dist_text}

<b>🔧 Analysen heute:</b> {status.get('analyses_today', 0)}
        """
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message[:4096],
                parse_mode='HTML'
            )
        except:
            pass