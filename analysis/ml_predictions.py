
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from utils.logging_config import get_logger
from database.operations import get_db_connection

logger = get_logger(__name__)

class MLPredictor:
    def __init__(self):
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_features(self, symbol, days=500):
        """Prepare ML features from technical indicators and price data"""
        try:
            conn = get_db_connection()
            
            # Get OHLCV data with technical indicators
            query = """
                SELECT o.timestamp, o.open, o.high, o.low, o.close, o.volume,
                       t.rsi_14, t.macd, t.macd_signal, t.bb_upper, t.bb_lower,
                       t.sma_20, t.sma_50, t.ema_20, t.ema_50, t.atr_14
                FROM ohlcv_data o
                LEFT JOIN technical_indicators t ON o.timestamp = t.timestamp AND o.symbol = t.symbol
                WHERE o.symbol = ? AND o.timeframe = '1d'
                ORDER BY o.timestamp DESC
                LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=(symbol, days))
            conn.close()
            
            if df.empty:
                return None, None
                
            # Sort chronologically
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Create features
            features = pd.DataFrame()
            
            # Price-based features
            features['price_change'] = df['close'].pct_change()
            features['price_volatility'] = df['close'].rolling(20).std()
            features['volume_change'] = df['volume'].pct_change()
            
            # Technical indicator features
            features['rsi'] = df['rsi_14']
            features['macd_signal'] = df['macd'] - df['macd_signal']
            features['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            features['sma_cross'] = (df['close'] - df['sma_20']) / df['sma_20']
            features['ema_momentum'] = (df['ema_20'] - df['ema_50']) / df['ema_50']
            
            # Lag features (previous values)
            for lag in [1, 2, 3, 5]:
                features[f'price_change_lag_{lag}'] = features['price_change'].shift(lag)
                features[f'rsi_lag_{lag}'] = features['rsi'].shift(lag)
            
            # Target: next day's return
            target = df['close'].pct_change().shift(-1)  # Next day's return
            
            # Remove NaN values
            valid_idx = ~(features.isnull().any(axis=1) | target.isnull())
            features = features[valid_idx]
            target = target[valid_idx]
            
            return features, target
        except Exception as e:
            logger.error(f"Feature preparation failed: {str(e)}", exc_info=True)
            return None, None
    
    def train_models(self, symbols):
        """Train ML models on multiple symbols"""
        try:
            all_features = []
            all_targets = []
            
            for symbol in symbols:
                features, target = self.prepare_features(symbol)
                if features is not None and len(features) > 50:
                    all_features.append(features)
                    all_targets.append(target)
            
            if not all_features:
                logger.warning("No valid data for ML training")
                return False
            
            # Combine all data
            X = pd.concat(all_features, ignore_index=True)
            y = pd.concat(all_targets, ignore_index=True)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
            
            # Train models
            for name, model in self.models.items():
                model.fit(X_train, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test)
                mae = mean_absolute_error(y_test, y_pred)
                logger.info(f"Model {name} MAE: {mae:.6f}")
            
            self.is_trained = True
            return True
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}", exc_info=True)
            return False
    
    def predict_price_movement(self, symbol, confidence_threshold=0.6):
        """Predict next price movement with confidence score"""
        if not self.is_trained:
            return {'direction': 'hold', 'confidence': 0, 'expected_return': 0}
            
        try:
            features, _ = self.prepare_features(symbol, days=100)
            if features is None or features.empty:
                return {'direction': 'hold', 'confidence': 0, 'expected_return': 0}
            
            # Use latest data point
            latest_features = features.iloc[-1:].values
            latest_scaled = self.scaler.transform(latest_features)
            
            # Get predictions from all models
            predictions = []
            for model in self.models.values():
                pred = model.predict(latest_scaled)[0]
                predictions.append(pred)
            
            # Ensemble prediction
            avg_prediction = np.mean(predictions)
            prediction_std = np.std(predictions)
            
            # Confidence based on agreement between models
            confidence = max(0, 1 - (prediction_std / abs(avg_prediction)) if avg_prediction != 0 else 0)
            
            # Direction
            if avg_prediction > 0.005 and confidence > confidence_threshold:  # 0.5% threshold
                direction = 'buy'
            elif avg_prediction < -0.005 and confidence > confidence_threshold:
                direction = 'sell'
            else:
                direction = 'hold'
            
            return {
                'direction': direction,
                'confidence': min(confidence, 1.0),
                'expected_return': avg_prediction * 100  # Convert to percentage
            }
        except Exception as e:
            logger.error(f"Price prediction failed: {str(e)}", exc_info=True)
            return {'direction': 'hold', 'confidence': 0, 'expected_return': 0}
