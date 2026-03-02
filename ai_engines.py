from google import genai
import json
import re

# KONFIGURATION
GEMINI_API_KEY = "AIzaSyBlvbSAcdo-GCI5f0Wnn0QTHJTjMq7sFhE" # Hier deinen Key einfügen

class HybridAI:
    def __init__(self):
        # Der stabile Client für 2026
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def analyze(self, text: str):
        if not GEMINI_API_KEY or "AIza" not in GEMINI_API_KEY:
            return {"relevance_score": 0}

        try:
            prompt = (
                f"Analysiere als Biotech-Daytrader diese News: '{text}'. "
                f"Antworte NUR mit einem JSON-Objekt: "
                f"{{\"ticker\": \"TICKER\", \"relevance_score\": 8, \"direction\": \"LONG\", \"summary_german\": \"Zusammenfassung\"}}"
            )
            
            # Neue Syntax für 2026 (vermeidet v1beta 404-Fehler)
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            return json.loads(match.group()) if match else {"relevance_score": 0}
            
        except Exception as e:
            print(f"⚠️ KI-Fehler: {e}")
            return {"relevance_score": 0}
