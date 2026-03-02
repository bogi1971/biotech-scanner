import google.generativeai as genai
import json
import re

# KONFIGURATION
GEMINI_API_KEY = "DEIN_GEMINI_API_KEY" # Hier deinen Key von aistudio.google.com einfügen
genai.configure(api_key=GEMINI_API_KEY)

def analyze_score(text: str):
    """
    KI-Analyse: Extrahiert Ticker und bewertet Daytrading-Potenzial.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "DEIN_GEMINI_API_KEY":
        return {"ticker": "N/A", "score": 0, "direction": "NEUTRAL", "summary": "Key fehlt"}

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Analysiere als Biotech-Daytrader diese News: "{text}"
        
        1. Welcher Aktien-Ticker ist betroffen?
        2. Score 1-10 (10 = FDA Zulassung/Übernahme, 1 = Rauschen).
        3. Richtung (LONG/SHORT).
        4. Kurze deutsche Zusammenfassung (max. 10 Wörter).

        Antworte NUR als JSON:
        {{"ticker": "TICKER", "score": 8, "direction": "LONG", "summary": "Zusammenfassung"}}
        """
        response = model.generate_content(prompt)
        # Extrahiere JSON-Block
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        return json.loads(match.group()) if match else None
    except Exception as e:
        print(f"⚠️ KI-Fehler: {e}")
        return None
