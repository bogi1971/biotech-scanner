import google.generativeai as genai
import json
import re

# KONFIGURATION
GEMINI_API_KEY = "AIzaSyBlvbSAcdo-GCI5f0Wnn0QTHJTjMq7sFhE" # Stelle sicher, dass der Key korrekt ist
genai.configure(api_key=GEMINI_API_KEY)

class HybridAI:
    def __init__(self):
        # Wir nutzen den Basisnamen
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze(self, text: str):
        if not GEMINI_API_KEY or "AIza" not in GEMINI_API_KEY:
            return {"relevance_score": 0}

        try:
            prompt = f"""
            Analysiere als Biotech-Daytrader diese News: "{text}"
            Gib als Antwort NUR ein JSON-Objekt zurück:
            {{"ticker": "TICKER", "relevance_score": 8, "direction": "LONG", "summary_german": "Zusammenfassung"}}
            """
            # Anfrage an die KI
            response = self.model.generate_content(prompt)
            
            # JSON extrahieren
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"relevance_score": 0}
            
        except Exception as e:
            print(f"⚠️ KI-Fehler im Detail: {e}")
            return {"relevance_score": 0}
