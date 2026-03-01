# config.py - Konfiguration für Biotech-Scanner

import os

# =============================================================================
# API KEYS - HIER DEINE KEYS EINFÜGEN
# =============================================================================

# Von https://aistudio.google.com/app/apikey (kostenlos)
GEMINI_API_KEY = "AIzaSyCygTUdNndCc7PfHd4uC36V2B8FYv_NprI"

# Von https://console.groq.com/keys (kostenlos)
GROQ_API_KEY = "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"

# Optional: Telegram für Alerts
# Von https://t.me/BotFather → /newbot
TELEGRAM_BOT_TOKEN = "8751621172:AAHRIaXibPNTwJl0mO4ShfX_q9dSpfiK0Sg"
# Chat-ID herausfinden: https://t.me/userinfobot
TELEGRAM_CHAT_ID = "5338135874"

# =============================================================================
# LIMITS (NICHT ÄNDERN - Das sind die kostenlosen Limits)
# =============================================================================

LIMITS = {
    'gemini': {
        'daily': 1500,        # 1500 Anfragen pro Tag
        'per_minute': 60      # 60 Anfragen pro Minute
    },
    'groq': {
        'daily': 28800,       # 20 pro Minute = 28.800 pro Tag
        'per_minute': 20
    }
}

# =============================================================================
# KEYWORDS FÜR FILTER
# =============================================================================

BIOTECH_KEYWORDS = [
    # Regulatory
    'FDA approval',
    'FDA rejection', 
    'FDA clearance',
    'PDUFA',
    'breakthrough therapy',
    'fast track',
    'orphan drug',
    'clinical hold',
    'complete response letter',
    'CRL',
    
    # Clinical Trials
    'phase 1',
    'phase 2', 
    'phase 3',
    'phase I',
    'phase II',
    'phase III',
    'top-line results',
    'primary endpoint',
    'secondary endpoint',
    'interim analysis',
    
    # Business
    'merger',
    'acquisition',
    'takeover',
    'IPO',
    'initial public offering',
    'public offering',
    'private placement',
    'partnership',
    'collaboration',
    'licensing deal',
    
    # Technologies
    'gene therapy',
    'cell therapy',
    'CAR-T',
    'CRISPR',
    'mRNA',
    'antisense',
    'RNAi',
    'monoclonal antibody',
    'bispecific',
    'ADC',
    'radiopharmaceutical',
    
    # Therapeutic Areas
    'oncology',
    'cancer',
    'immunology',
    'rare disease',
    'orphan disease',
    'neurology',
    'Alzheimer',
    'Parkinson',
    'diabetes',
    'obesity',
    'GLP-1',
    'cardiovascular',
    
    # General
    'biotech',
    'biotechnology',
    'pharma',
    'pharmaceutical',
    'drug approval',
    'regulatory approval',
    'EMA approval',
    'NMPA approval'
]

# =============================================================================
# ERWEITERTE EINSTELLUNGEN
# =============================================================================

# Minimale Relevanz für Alerts (1-10)
ALERT_THRESHOLD = 7

# Maximale Artikel pro Quelle
MAX_ARTICLES_PER_SOURCE = 10

# Sprache für Zusammenfassungen
OUTPUT_LANGUAGE = "german"  # oder "english"

# Debug-Modus (mehr Ausgaben in Konsole)
DEBUG = False