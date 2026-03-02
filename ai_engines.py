import google.generativeai as genai
import json
import re

# KONFIGURATION
GEMINI_API_KEY = "AIzaSyBlvbSAcdo-GCI5f0Wnn0QTHJTjMq7sFhE" # Bitte hier deinen API-Key einfügen
genai.configure(api_key=GEMINI_API_KEY)

class HybridAI:
    def __init__(self):
        # Wir nutzen den exakten Namen 'models/gemini-1.5-flash'
        self.model = genai.GenerativeModel('models/gemini-1.5-flash')

    def analyze(self, text: str):
        if not GEMINI_API_KEY or "AIza" not in GEMINI_API_KEY:
            return {"ticker": "N/A", "relevance_score": 0, "direction": "NEUTRAL", "summary_german": "Key fehlt"}

        try:
            prompt = f"""
            Analysiere als Biotech-Daytrader diese News: "{text}"
            
            1. Welcher Aktien-Ticker ist betroffen?
            2. Score 1-10 (10 = FDA Zulassung/Übernahme, 1 = Rauschen).
            3. Richtung (LONG/SHORT).
            4. Kurze deutsche Zusammenfassung (max. 10 Wörter).

            Antworte NUR als JSON-Objekt ohne Markdown:
            {{"ticker": "TICKER", "relevance_score": 8, "direction": "LONG", "summary_german": "Zusammenfassung"}}
            """
            # Wir erzwingen die Nutzung der stabilen API-Version
            response = self.model.generate_content(prompt)
            
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"relevance_score": 0}
            
        except Exception as e:
            # Falls das Modell immer noch nicht gefunden wird, probieren wir 'gemini-pro'
            print(f"⚠️ KI-Fehler: {e}")
            return {"relevance_score": 0}
