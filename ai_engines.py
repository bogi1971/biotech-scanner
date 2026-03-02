import google.generativeai as genai
import json
import re

# API-Key konfigurieren
GEMINI_API_KEY = "DEIN_API_KEY_HIER"
genai.configure(api_key=GEMINI_API_KEY)

def analyze_with_gemini(text: str) -> dict:
    """
    Analysiert News, extrahiert Firma, Ticker und Score dynamisch.
    Keine Watchliste nötig, die KI erkennt es aus dem Kontext.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = (
        "Analysiere diese Biotech-News für einen Daytrader. "
        "1. Identifiziere die Hauptfirma und den Ticker (wenn kein Ticker bekannt, schätze ihn oder gib 'N/A'). "
        "2. Gib einen Score von 1-10 für das Daytrading-Potenzial (FDA/Phase3/M&A = 10). "
        "3. Antworte AUSSCHLIESSLICH im folgenden JSON-Format: "
        "{'firma': 'Name', 'ticker': 'TICKER', 'score': 10, 'grund': 'Kurze Erklärung'}"
        f"\n\nText: {text}"
    )
    
    try:
        response = model.generate_content(prompt)
        # JSON aus dem Antwort-Text extrahieren (falls die KI drumherum quatscht)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"⚠️ Gemini KI-Fehler: {e}")
    
    return {'firma': 'Unknown', 'ticker': 'N/A', 'score': 0, 'grund': 'Fehler'}
