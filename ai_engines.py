from google import genai
import json
import re

# KONFIGURATION
GEMINI_API_KEY = "AIzaSyBlvbSAcdo-GCI5f0Wnn0QTHJTjMq7sFhE" # Hier deinen Key einfügen

class HybridAI:
    def __init__(self):
        # Wir nutzen den neuen offiziellen Client für 2026
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def analyze(self, text: str):
        if not GEMINI_API_KEY or "AIza" not in GEMINI_API_KEY:
            return {"relevance_score": 0}

        try:
            prompt = f"""
            Analysiere als Biotech-Daytrader diese News: "{text}"
            Gib als Antwort NUR ein JSON-Objekt zurück:
            {{"ticker": "TICKER", "relevance_score": 8, "direction": "LONG", "summary_german": "Zusammenfassung"}}
            """
            # Neue, stabile Syntax für den 2026 Client
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            
            # JSON extrahieren (Gemini liefert jetzt oft Text direkt)
            json_text = response.text
            match = re.search(r'\{.*\}', json_text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"relevance_score": 0}
            
        except Exception as e:
            print(f"⚠️ KI-Fehler: {e}")
            return {"relevance_score": 0}
