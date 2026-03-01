## ai_engines.py - TRADING-OPTIMIERTE VERSION

import json
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class UsageTracker:
    analyses_today: int = 0
    last_reset: float = 0
    
    def reset_if_needed(self):
        import time
        now = time.time()
        if now - self.last_reset > 86400:
            self.analyses_today = 0
            self.last_reset = now

class TradingScorer:
    """Trading-optimierter Scorer mit Markt-Impact-Bewertung"""
    
    def __init__(self):
        # MARKTBEWEGENDE EREIGNISSE (10 Punkte = sofortiger Kursprung)
        self.critical_events = {
            # FDA / Regulatory - Höchster Impact
            'FDA approval': 10,
            'FDA grants approval': 10,
            'FDA rejection': 10,  # Negativ aber auch bewegend
            'FDA complete response letter': 9,
            'FDA CRL': 9,
            'clinical hold': 9,  # Entwicklungsstopp
            'PDUFA date': 9,
            'PDUFA goal date': 9,
            'breakthrough therapy designation': 8,
            'fast track designation': 7,
            'orphan drug designation': 6,
            
            # Clinical Trials - Hoher Impact
            'phase 3 topline results': 9,
            'phase 3 top-line results': 9,
            'phase 3 primary endpoint met': 9,
            'phase 3 success': 9,
            'phase 3 failure': 9,  # Auch negativ bewegend
            'pivotal trial success': 9,
            'registrational trial': 8,
            'phase 2b results': 7,
            'interim analysis positive': 7,
            
            # M&A - Sehr hoher Impact
            'to be acquired': 9,
            'acquisition for': 9,  # Mit Preis
            'merger agreement': 8,
            'takeover bid': 8,
            'acquired by': 8,
            'strategic acquisition': 7,
            
            # Finanzierung - Mittlerer Impact (Verwässerung)
            'public offering': 5,
            'priced offering': 5,
            'private placement': 4,
            'at-the-market offering': 4,
            
            # Partnerschaften - Variabler Impact
            'licensing deal worth': 7,  # Mit Wertangabe
            'collaboration up to': 6,
            'partnership potential': 5,
            
            # Technologie-Durchbrüche
            'first gene therapy approval': 10,
            'first CRISPR approval': 10,
            'CAR-T approval': 9,
        }
        
        # MULTIPLIKATOREN
        self.company_tiers = {
            'mega': ['pfizer', 'johnson', 'jnj', 'roche', 'novartis', 'merck', 'lilly'],
            'large': ['amgen', 'gilead', 'bms', 'abbvie', 'astrazeneca', 'sanofi', 'gsk'],
            'mid': ['vertex', 'regeneron', 'biogen', 'alexion', 'incyte'],
        }
        
        # NEGATIVE TRIGGER (für Short-Signale)
        self.negative_triggers = [
            'clinical hold', 'safety signal', 'adverse events',
            'trial termination', 'study discontinuation', 'failed primary endpoint',
            'missed endpoint', 'negative results', 'futility analysis'
        ]
    
    def calculate_trading_score(self, text: str) -> Tuple[int, Dict]:
        """
        Berechnet Trading-Score mit:
        - Base Score (0-10)
        - Impact-Multiplikator
        - Sentiment-Adjust
        - Urgency-Bonus
        """
        text_lower = text.lower()
        
        # 1. Base Score aus kritischen Events
        base_score = 0
        matched_events = []
        
        for event, points in self.critical_events.items():
            if event.lower() in text_lower:
                base_score += points
                matched_events.append(f"{event} (+{points})")
        
        # 2. Company-Tier Multiplikator
        tier_multiplier = 1.0
        company_tier = "small"
        
        for tier, companies in self.company_tiers.items():
            for company in companies:
                if company in text_lower:
                    tier_multiplier = {'mega': 1.5, 'large': 1.3, 'mid': 1.1}[tier]
                    company_tier = tier
                    matched_events.append(f"{company} ({tier}): x{tier_multiplier}")
                    break
        
        # 3. Sentiment-Analyse (fortschrittlich)
        sentiment_score, sentiment_label = self._analyze_sentiment(text_lower)
        
        # 4. Urgency-Bonus (Same-Day-News)
        urgency_bonus = 0
        if any(word in text_lower for word in ['today', 'announced today', 'this morning', 'just announced']):
            urgency_bonus = 1
            matched_events.append("URGENT: Same-day news (+1)")
        
        # 5. Finaler Score
        raw_score = (base_score * tier_multiplier) + urgency_bonus
        
        # Cap bei 10
        if raw_score >= 9: final_score = 10
        elif raw_score >= 7.5: final_score = 9
        elif raw_score >= 6: final_score = 8
        elif raw_score >= 4.5: final_score = 7
        elif raw_score >= 3: final_score = 6
        elif raw_score >= 2: final_score = 5
        else: final_score = max(1, int(raw_score))
        
        # Trading-Metadaten
        metadata = {
            'base_score': base_score,
            'tier_multiplier': tier_multiplier,
            'company_tier': company_tier,
            'sentiment': sentiment_label,
            'sentiment_score': sentiment_score,
            'urgency_bonus': urgency_bonus,
            'matched_events': matched_events[:5],  # Top 5
            'is_short_signal': sentiment_label == 'Negativ' and base_score >= 6,
            'pre_market_relevant': final_score >= 8
        }
        
        return min(10, final_score), metadata
    
    def _analyze_sentiment(self, text: str) -> Tuple[float, str]:
        """Fortschrittliche Sentiment-Analyse"""
        
        # Positive Indikatoren
        positive_phrases = {
            'strong': 2, 'robust': 2, 'significant': 2, 'substantial': 2,
            'exceeds expectations': 3, 'beat expectations': 3,
            'breakthrough': 3, 'transformational': 3,
            'first-in-class': 2, 'best-in-class': 2,
            'blockbuster potential': 3, 'multi-billion': 3,
            'successful': 2, 'positive outcome': 2,
            'surge': 2, 'soar': 3, 'jump': 2, 'rally': 2
        }
        
        # Negative Indikatoren  
        negative_phrases = {
            'failed': -3, 'failure': -3, 'disappointing': -2,
            'missed': -2, 'below expectations': -2,
            'safety concerns': -3, 'adverse events': -3,
            'clinical hold': -4, 'terminated': -3,
            'plunge': -3, 'tumble': -2, 'crash': -3,
            'dilutive': -2, 'substantial discount': -2
        }
        
        score = 0
        for phrase, value in positive_phrases.items():
            if phrase in text:
                score += value
        
        for phrase, value in negative_phrases.items():
            if phrase in text:
                score += value
        
        # Label
        if score >= 2: return score, "Stark Positiv"
        elif score > 0: return score, "Positiv"
        elif score == 0: return score, "Neutral"
        elif score > -2: return score, "Negativ"
        else: return score, "Stark Negativ"

class TradingPredictor:
    """Trading-spezifische Prognosen"""
    
    def predict(self, score: int, metadata: Dict) -> Dict:
        """Erstellt Trading-Signal"""
        
        # Basis-Richtung
        sentiment = metadata['sentiment']
        is_short = metadata.get('is_short_signal', False)
        
        if is_short:
            direction = 'SHORT'
            strategy = 'Short-Selling oder Puts'
        elif sentiment in ['Stark Positiv', 'Positiv']:
            direction = 'LONG'
            strategy = 'Kauf oder Calls'
        elif sentiment == 'Stark Negativ':
            direction = 'SHORT'
            strategy = 'Short-Selling'
        else:
            direction = 'NEUTRAL/WATCH'
            strategy = 'Abwarten oder kleine Position'
        
        # Zeitfenster
        if metadata.get('pre_market_relevant') and score >= 8:
            timeframe = "⚡ PRE-MARKET / Sofort"
            entry_timing = "Vorbörslich oder bei Marktöffnung"
        elif score >= 7:
            timeframe = "📅 Same Day"
            entry_timing = "Innerhalb 2-4 Stunden"
        else:
            timeframe = "📆 1-3 Tage"
            entry_timing = "Bei Rücksetzer oder Bestätigung"
        
        # Erwartete Bewegung
        base_move = score * 2  # 2-20%
        if metadata['company_tier'] == 'mega':
            base_move *= 0.7  # Große Firmen bewegen sich weniger
        elif metadata['company_tier'] == 'small':
            base_move *= 1.5  # Kleine Biotechs volatile
        
        # Konfidenz
        if score >= 9 and metadata['sentiment_score'] != 0:
            confidence = "🔥🔥🔟 SEHR HOCH - Handeln!"
        elif score >= 7:
            confidence = "🔥🔥 HOCH - Starke Überlegung"
        elif score >= 5:
            confidence = "🔥 MITTEL - Beobachten"
        else:
            confidence = "❓ NIEDRIG - Ignorieren"
        
        # Risiko-Management
        if score >= 8:
            position_size = "Klein (2-3% Portfolio) - High Volatility"
            stop_loss = "8-10% unter Entry"
        elif score >= 6:
            position_size = "Sehr klein (1-2%) - Spekulativ"
            stop_loss = "5-8% unter Entry"
        else:
            position_size = "Nur Watchlist"
            stop_loss = "Nicht traden"
        
        return {
            'direction': direction,
            'strategy': strategy,
            'expected_move_percent': round(base_move, 1),
            'timeframe': timeframe,
            'entry_timing': entry_timing,
            'confidence': confidence,
            'position_size': position_size,
            'stop_loss': stop_loss,
            'rationale': f"{metadata['matched_events'][0] if metadata['matched_events'] else 'Kein klarer Trigger'} | {sentiment}"
        }

class HybridAI:
    """Trading-optimierter Algorithmus"""
    
    def __init__(self, gemini_key: str = None, groq_key: str = None):
        self.scorer = TradingScorer()
        self.predictor = TradingPredictor()
        self.usage = UsageTracker()
        self.all_scores = []
        self.trading_signals = []  # Für Statistik
    
    def analyze(self, text: str) -> Dict:
        self.usage.reset_if_needed()
        self.usage.analyses_today += 1
        
        # Trading-Score berechnen
        score, metadata = self.scorer.calculate_trading_score(text)
        
        # Trading-Prognose
        prediction = self.predictor.predict(score, metadata)
        
        # Firmen extrahieren (einfach)
        companies = self._extract_companies(text)
        
        # Zusammenfassung
        summary = self._generate_summary(score, metadata, prediction)
        
        self.all_scores.append(score)
        
        # Trading-Signal speichern wenn relevant
        if score >= 7:
            self.trading_signals.append({
                'score': score,
                'direction': prediction['direction'],
                'confidence': prediction['confidence']
            })
        
        return {
            'relevance_score': score,
            'category': self._determine_category(text.lower(), metadata),
            'sentiment': metadata['sentiment'],
            'companies': companies,
            'phase': self._determine_phase(text.lower()),
            'keywords_found': metadata['matched_events'],
            'trading_metadata': metadata,
            'summary_german': summary,
            'engine': 'trading-algorithm-v2',
            'stock_prediction': prediction
        }
    
    def _extract_companies(self, text: str) -> List[Dict]:
        """Einfache Firmen-Extraktion"""
        companies = []
        words = text.split()
        
        for i, word in enumerate(words):
            clean = re.sub(r'[^\w\s&-]', '', word)
            # Firmen mit Inc, Corp, etc.
            if i < len(words) - 1:
                next_word = words[i+1].rstrip('.,;')
                if next_word in ['Inc', 'Corp', 'Ltd', 'AG', 'NV', 'PLC', 'SA']:
                    companies.append({"name": clean, "ticker": None})
        
        # Bekannte Biotech-Firmen suchen
        known_biotechs = [
            'Moderna', 'BioNTech', 'CRISPR', 'Editas', 'Intellia',
            'Bluebird', 'Sarepta', 'Vertex', 'Regeneron', 'Biogen'
        ]
        for company in known_biotechs:
            if company in text and not any(c['name'] == company for c in companies):
                companies.append({"name": company, "ticker": None})
        
        return companies[:3]  # Max 3
    
    def _determine_category(self, text: str, metadata: Dict) -> str:
        """Bestimmt Kategorie basierend auf Events"""
        events = ' '.join(metadata.get('matched_events', [])).lower()
        
        if 'fda' in events or 'approval' in events:
            return "FDA_Zulassung"
        elif 'phase 3' in events or 'clinical' in events:
            return "Klinische_Studie"
        elif 'acquisition' in events or 'merger' in events or 'acquired' in events:
            return "M&A"
        elif 'offering' in events or 'financing' in events:
            return "Finanzierung"
        elif 'partnership' in events or 'licensing' in events:
            return "Partnerschaft"
        else:
            return "Sonstiges"
    
    def _determine_phase(self, text: str) -> str:
        if 'phase 3' in text: return "Phase 3"
        elif 'phase 2' in text: return "Phase 2"
        elif 'phase 1' in text: return "Phase 1"
        elif 'approved' in text: return "Zugelassen"
        else: return "N/A"
    
    def _generate_summary(self, score: int, metadata: Dict, prediction: Dict) -> str:
        """Trading-fokussierte Zusammenfassung"""
        events = metadata.get('matched_events', [])
        top_event = events[0] if events else 'Kein klares Event'
        
        summary = f"🎯 Score {score}/10: {prediction['direction']} | "
        summary += f"{metadata['sentiment']} | "
        summary += f"{top_event.split('(')[0].strip()} | "
        summary += f"Erwartete Bewegung: ±{prediction['expected_move_percent']}%"
        
        if prediction['direction'] in ['LONG', 'SHORT']:
            summary += f" | {prediction['entry_timing']}"
        
        return summary
    
    def get_status(self) -> Dict:
        """Erweiterte Status-Info mit Trading-Statistik"""
        distribution = {}
        if self.all_scores:
            distribution = {
                '1-3 (Ignorieren)': len([s for s in self.all_scores if s <= 3]),
                '4-5 (Beobachten)': len([s for s in self.all_scores if 4 <= s <= 5]),
                '6 (Prüfen)': len([s for s in self.all_scores if s == 6]),
                '7-8 (Handeln)': len([s for s in self.all_scores if 7 <= s <= 8]),
                '9-10 (Sofort!)': len([s for s in self.all_scores if s >= 9])
            }
        
        # Trading-Signal-Statistik
        long_signals = len([s for s in self.trading_signals if s['direction'] == 'LONG'])
        short_signals = len([s for s in self.trading_signals if s['direction'] == 'SHORT'])
        
        return {
            'analyses_today': self.usage.analyses_today,
            'score_distribution': distribution,
            'trading_signals': {
                'total': len(self.trading_signals),
                'long': long_signals,
                'short': short_signals
            },
            'last_engine': 'trading-algorithm-v2'
        }