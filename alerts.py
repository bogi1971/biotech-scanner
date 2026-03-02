import telegram
import asyncio

class TelegramAlerter:
    def __init__(self, bot_token: str, chat_id: str):
        self.token = bot_token
        self.chat_id = chat_id

    async def send_alert(self, article: dict, analysis: dict):
        if not self.token or not self.chat_id:
            return
            
        score = analysis.get('relevance_score', 0)
        direction = analysis.get('direction', 'NEUTRAL')
        ticker = analysis.get('ticker', 'N/A')
        
        emoji = "🟢📈" if direction == "LONG" else "🔴📉"
        
        message = (
            f"<b>{emoji} SIGNAL: {direction}</b>\n"
            f"<b>Ticker: ${ticker} | Score: {score}/10</b>\n\n"
            f"📝 {analysis.get('summary_german', 'Keine Zusammenfassung vorhanden')}\n\n"
            f"<a href='{article.get('link', '')}'>📰 Zum Artikel</a>"
        )
        
        try:
            # Direkte Instanzierung behebt httpx-Konflikte
            bot = telegram.Bot(token=self.token)
            async with bot:
                await bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='HTML'
                )
            print(f"✅ Telegram gesendet: ${ticker}")
        except Exception as e:
            print(f"❌ Telegram Fehler: {e}")
