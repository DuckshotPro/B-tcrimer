
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from analysis.technical_indicators import generate_signals
from analysis.ml_predictions import MLPredictor
from analysis.sentiment_analysis import get_symbol_sentiment
from utils.logging_config import get_logger

logger = get_logger(__name__)

class AutomatedSignalGenerator:
    def __init__(self):
        self.ml_predictor = MLPredictor()
        self.signal_weights = {
            'technical': 0.4,
            'ml': 0.35,
            'sentiment': 0.25
        }
    
    def generate_mega_signals(self, symbols):
        """Generate comprehensive trading signals combining all analysis methods"""
        mega_signals = []
        
        for symbol in symbols:
            try:
                # Get technical signals
                tech_signals = generate_signals(symbol)
                
                # Get ML prediction
                ml_pred = self.ml_predictor.predict_price_movement(symbol)
                
                # Get sentiment
                sentiment_data = get_symbol_sentiment(symbol)
                
                # Combine signals
                combined_score = self._combine_signals(tech_signals, ml_pred, sentiment_data)
                
                if combined_score:
                    mega_signals.append({
                        'symbol': symbol,
                        'signal': combined_score['signal'],
                        'confidence': combined_score['confidence'],
                        'expected_return': combined_score['expected_return'],
                        'risk_level': combined_score['risk_level'],
                        'technical_score': combined_score['technical_score'],
                        'ml_score': combined_score['ml_score'],
                        'sentiment_score': combined_score['sentiment_score'],
                        'timestamp': datetime.now()
                    })
                    
            except Exception as e:
                logger.error(f"Signal generation failed for {symbol}: {str(e)}", exc_info=True)
                continue
        
        # Sort by confidence and expected return
        mega_signals.sort(key=lambda x: x['confidence'] * abs(x['expected_return']), reverse=True)
        
        return mega_signals
    
    def _combine_signals(self, tech_signals, ml_pred, sentiment_data):
        """Combine different signal sources into a unified signal"""
        try:
            # Technical analysis score
            tech_score = self._score_technical_signals(tech_signals)
            
            # ML score
            ml_score = 0
            if ml_pred['direction'] == 'buy':
                ml_score = ml_pred['confidence']
            elif ml_pred['direction'] == 'sell':
                ml_score = -ml_pred['confidence']
            
            # Sentiment score
            sentiment_score = 0
            if sentiment_data:
                sentiment_score = sentiment_data.get('compound_score', 0)
            
            # Weighted combination
            combined_score = (
                tech_score * self.signal_weights['technical'] +
                ml_score * self.signal_weights['ml'] +
                sentiment_score * self.signal_weights['sentiment']
            )
            
            # Determine signal
            if combined_score > 0.3:
                signal = 'BUY'
            elif combined_score < -0.3:
                signal = 'SELL'
            else:
                signal = 'HOLD'
            
            # Calculate confidence
            confidence = min(abs(combined_score), 1.0)
            
            # Expected return (combine ML prediction with technical momentum)
            expected_return = ml_pred.get('expected_return', 0) * confidence
            
            # Risk level
            risk_level = 'LOW' if confidence < 0.5 else 'MEDIUM' if confidence < 0.8 else 'HIGH'
            
            return {
                'signal': signal,
                'confidence': confidence,
                'expected_return': expected_return,
                'risk_level': risk_level,
                'technical_score': tech_score,
                'ml_score': ml_score,
                'sentiment_score': sentiment_score
            }
            
        except Exception as e:
            logger.error(f"Signal combination failed: {str(e)}", exc_info=True)
            return None
    
    def _score_technical_signals(self, tech_signals):
        """Score technical analysis signals"""
        if not tech_signals or not tech_signals.get('signals'):
            return 0
        
        total_score = 0
        signal_weights = {'Strong': 1.0, 'Moderate': 0.6, 'Weak': 0.3}
        
        for signal in tech_signals['signals']:
            weight = signal_weights.get(signal['strength'], 0.5)
            if signal['signal'] == 'Buy':
                total_score += weight
            elif signal['signal'] == 'Sell':
                total_score -= weight
        
        # Normalize to [-1, 1] range
        return max(-1, min(1, total_score / 5))
    
    def get_top_opportunities(self, limit=10):
        """Get top trading opportunities"""
        # Get available symbols
        from database.operations import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT symbol FROM ohlcv_data 
            ORDER BY (SELECT MAX(timestamp) FROM ohlcv_data t2 WHERE t2.symbol = ohlcv_data.symbol) DESC 
            LIMIT 20
        """)
        symbols = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Generate signals
        signals = self.generate_mega_signals(symbols)
        
        # Filter for strong buy/sell signals
        strong_signals = [s for s in signals if s['confidence'] > 0.6 and s['signal'] != 'HOLD']
        
        return strong_signals[:limit]
