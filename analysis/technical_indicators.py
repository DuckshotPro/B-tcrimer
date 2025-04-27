import pandas as pd
import numpy as np
import datetime
from scipy import stats
from utils.logging_config import get_logger
from database.operations import get_db_connection

logger = get_logger(__name__)

def load_ohlcv_data(symbol, exchange='binance', days=180):
    """Load OHLCV data for a specific symbol from the database"""
    try:
        # Calculate the date threshold
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        query = """
            SELECT timestamp, open, high, low, close, volume
            FROM ohlcv_data
            WHERE symbol = ? AND exchange = ? AND date(timestamp) >= ?
            ORDER BY timestamp
        """
        
        df = pd.read_sql_query(query, conn, params=(symbol, exchange, threshold_date))
        conn.close()
        
        if df.empty:
            logger.warning(f"No OHLCV data found for {symbol} on {exchange}")
            return None
            
        # Convert timestamp to datetime if it's a string
        if isinstance(df['timestamp'].iloc[0], str):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
        # Set timestamp as index
        df.set_index('timestamp', inplace=True)
        
        return df
    except Exception as e:
        logger.error(f"Failed to load OHLCV data for {symbol}: {str(e)}", exc_info=True)
        return None

def calculate_rsi(data, window=14):
    """Calculate Relative Strength Index (RSI)"""
    try:
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    except Exception as e:
        logger.error(f"Failed to calculate RSI: {str(e)}", exc_info=True)
        return pd.Series(np.nan, index=data.index)

def calculate_macd(data, fast=12, slow=26, signal=9):
    """Calculate Moving Average Convergence Divergence (MACD)"""
    try:
        # Calculate the fast and slow EMA
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        })
    except Exception as e:
        logger.error(f"Failed to calculate MACD: {str(e)}", exc_info=True)
        return pd.DataFrame({
            'macd': pd.Series(np.nan, index=data.index),
            'signal': pd.Series(np.nan, index=data.index),
            'histogram': pd.Series(np.nan, index=data.index)
        })

def calculate_bollinger_bands(data, window=20, num_std=2):
    """Calculate Bollinger Bands"""
    try:
        # Calculate rolling mean and standard deviation
        rolling_mean = data.rolling(window=window).mean()
        rolling_std = data.rolling(window=window).std()
        
        # Calculate upper and lower bands
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)
        
        return pd.DataFrame({
            'middle': rolling_mean,
            'upper': upper_band,
            'lower': lower_band
        })
    except Exception as e:
        logger.error(f"Failed to calculate Bollinger Bands: {str(e)}", exc_info=True)
        return pd.DataFrame({
            'middle': pd.Series(np.nan, index=data.index),
            'upper': pd.Series(np.nan, index=data.index),
            'lower': pd.Series(np.nan, index=data.index)
        })

def calculate_sma(data, window=20):
    """Calculate Simple Moving Average (SMA)"""
    try:
        return data.rolling(window=window).mean()
    except Exception as e:
        logger.error(f"Failed to calculate SMA: {str(e)}", exc_info=True)
        return pd.Series(np.nan, index=data.index)

def calculate_ema(data, span=20):
    """Calculate Exponential Moving Average (EMA)"""
    try:
        return data.ewm(span=span, adjust=False).mean()
    except Exception as e:
        logger.error(f"Failed to calculate EMA: {str(e)}", exc_info=True)
        return pd.Series(np.nan, index=data.index)

def calculate_atr(data, window=14):
    """Calculate Average True Range (ATR)"""
    try:
        high = data['high']
        low = data['low']
        close = data['close']
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.DataFrame({
            'tr1': tr1,
            'tr2': tr2,
            'tr3': tr3
        }).max(axis=1)
        
        # Calculate ATR
        atr = tr.rolling(window=window).mean()
        
        return atr
    except Exception as e:
        logger.error(f"Failed to calculate ATR: {str(e)}", exc_info=True)
        return pd.Series(np.nan, index=data.index)

def detect_support_resistance(data, window=20):
    """Detect support and resistance levels using rolling min/max"""
    try:
        # Calculate rolling min and max for support and resistance
        support = data.rolling(window=window).min()
        resistance = data.rolling(window=window).max()
        
        return pd.DataFrame({
            'support': support,
            'resistance': resistance
        })
    except Exception as e:
        logger.error(f"Failed to detect support and resistance: {str(e)}", exc_info=True)
        return pd.DataFrame({
            'support': pd.Series(np.nan, index=data.index),
            'resistance': pd.Series(np.nan, index=data.index)
        })

def detect_trend(data, window=20):
    """Detect trend using linear regression"""
    try:
        # Calculate rolling linear regression slope
        def rolling_slope(series, window):
            result = [np.nan] * (window - 1)
            for i in range(window-1, len(series)):
                y = series[i-window+1:i+1].values
                x = np.arange(window)
                slope = stats.linregress(x, y)[0]
                result.append(slope)
            return pd.Series(result, index=series.index)
        
        slope = rolling_slope(data, window)
        
        # Classify trend based on slope
        trend = pd.Series(index=data.index)
        trend[slope > 0.01] = 'uptrend'
        trend[(slope >= -0.01) & (slope <= 0.01)] = 'sideways'
        trend[slope < -0.01] = 'downtrend'
        
        return pd.DataFrame({
            'slope': slope,
            'trend': trend
        })
    except Exception as e:
        logger.error(f"Failed to detect trend: {str(e)}", exc_info=True)
        return pd.DataFrame({
            'slope': pd.Series(np.nan, index=data.index),
            'trend': pd.Series(np.nan, index=data.index)
        })

def calculate_all_indicators(symbol, exchange='binance', days=180):
    """Calculate all technical indicators for a symbol"""
    try:
        # Load OHLCV data
        df = load_ohlcv_data(symbol, exchange, days)
        
        if df is None or df.empty:
            logger.warning(f"No data available for {symbol}, skipping indicators calculation")
            return None
            
        # Calculate indicators
        result = df.copy()
        
        # RSI
        result['rsi_14'] = calculate_rsi(df['close'], window=14)
        
        # MACD
        macd_data = calculate_macd(df['close'])
        result['macd'] = macd_data['macd']
        result['macd_signal'] = macd_data['signal']
        result['macd_histogram'] = macd_data['histogram']
        
        # Bollinger Bands
        bb_data = calculate_bollinger_bands(df['close'])
        result['bb_middle'] = bb_data['middle']
        result['bb_upper'] = bb_data['upper']
        result['bb_lower'] = bb_data['lower']
        
        # Moving Averages
        result['sma_20'] = calculate_sma(df['close'], window=20)
        result['sma_50'] = calculate_sma(df['close'], window=50)
        result['sma_200'] = calculate_sma(df['close'], window=200)
        result['ema_20'] = calculate_ema(df['close'], span=20)
        result['ema_50'] = calculate_ema(df['close'], span=50)
        result['ema_200'] = calculate_ema(df['close'], span=200)
        
        # ATR
        result['atr_14'] = calculate_atr(df, window=14)
        
        # Support and Resistance
        sr_data = detect_support_resistance(df['close'])
        result['support'] = sr_data['support']
        result['resistance'] = sr_data['resistance']
        
        # Trend
        trend_data = detect_trend(df['close'])
        result['trend_slope'] = trend_data['slope']
        result['trend'] = trend_data['trend']
        
        # Reset index to make timestamp a column
        result.reset_index(inplace=True)
        
        return result
    except Exception as e:
        logger.error(f"Failed to calculate indicators for {symbol}: {str(e)}", exc_info=True)
        return None

def store_technical_indicators(symbol, indicators_df):
    """Store calculated technical indicators in the database"""
    if indicators_df is None or indicators_df.empty:
        return
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if we need to remove existing data
        cursor.execute(
            "SELECT COUNT(*) FROM technical_indicators WHERE symbol = ?",
            (symbol,)
        )
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Delete existing indicators for this symbol
            cursor.execute(
                "DELETE FROM technical_indicators WHERE symbol = ?",
                (symbol,)
            )
            logger.info(f"Deleted {count} existing indicator records for {symbol}")
            
        # Store the indicators
        indicators_df['symbol'] = symbol
        indicators_df.to_sql('technical_indicators', conn, if_exists='append', index=False)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Stored {len(indicators_df)} technical indicator records for {symbol}")
    except Exception as e:
        logger.error(f"Failed to store technical indicators for {symbol}: {str(e)}", exc_info=True)

def generate_signals(symbol, exchange='binance'):
    """Generate trading signals based on technical indicators"""
    try:
        # Load indicators
        conn = get_db_connection()
        query = """
            SELECT * FROM technical_indicators 
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """
        
        indicators = pd.read_sql_query(query, conn, params=(symbol,))
        conn.close()
        
        if indicators.empty:
            logger.warning(f"No indicators found for {symbol}, skipping signal generation")
            return None
            
        # Sort by timestamp ascending to ensure proper order
        indicators.sort_values('timestamp', inplace=True)
        
        # Generate signals
        signals = []
        
        # Latest data point
        latest = indicators.iloc[-1]
        
        # RSI signals
        if not pd.isna(latest['rsi_14']):
            if latest['rsi_14'] < 30:
                signals.append({
                    'indicator': 'RSI',
                    'signal': 'Buy',
                    'strength': 'Strong',
                    'value': round(latest['rsi_14'], 2),
                    'description': 'RSI below 30 indicates oversold conditions'
                })
            elif latest['rsi_14'] > 70:
                signals.append({
                    'indicator': 'RSI',
                    'signal': 'Sell',
                    'strength': 'Strong',
                    'value': round(latest['rsi_14'], 2),
                    'description': 'RSI above 70 indicates overbought conditions'
                })
        
        # MACD signals
        if not pd.isna(latest['macd']) and not pd.isna(latest['macd_signal']):
            # Check for MACD crossover
            if len(indicators) >= 2:
                prev = indicators.iloc[-2]
                if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                    signals.append({
                        'indicator': 'MACD',
                        'signal': 'Buy',
                        'strength': 'Moderate',
                        'value': round(latest['macd_histogram'], 4),
                        'description': 'MACD crossed above signal line'
                    })
                elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                    signals.append({
                        'indicator': 'MACD',
                        'signal': 'Sell',
                        'strength': 'Moderate',
                        'value': round(latest['macd_histogram'], 4),
                        'description': 'MACD crossed below signal line'
                    })
        
        # Bollinger Bands signals
        if not pd.isna(latest['bb_upper']) and not pd.isna(latest['bb_lower']):
            if latest['close'] < latest['bb_lower']:
                signals.append({
                    'indicator': 'Bollinger Bands',
                    'signal': 'Buy',
                    'strength': 'Moderate',
                    'value': round(latest['close'], 2),
                    'description': 'Price below lower Bollinger Band indicates potential reversal'
                })
            elif latest['close'] > latest['bb_upper']:
                signals.append({
                    'indicator': 'Bollinger Bands',
                    'signal': 'Sell',
                    'strength': 'Moderate',
                    'value': round(latest['close'], 2),
                    'description': 'Price above upper Bollinger Band indicates potential reversal'
                })
        
        # Moving Average crossovers
        if not pd.isna(latest['sma_50']) and not pd.isna(latest['sma_200']):
            # Check for Golden Cross / Death Cross
            if len(indicators) >= 2:
                prev = indicators.iloc[-2]
                if latest['sma_50'] > latest['sma_200'] and prev['sma_50'] <= prev['sma_200']:
                    signals.append({
                        'indicator': 'Moving Averages',
                        'signal': 'Buy',
                        'strength': 'Strong',
                        'value': None,
                        'description': 'Golden Cross: 50-day SMA crossed above 200-day SMA'
                    })
                elif latest['sma_50'] < latest['sma_200'] and prev['sma_50'] >= prev['sma_200']:
                    signals.append({
                        'indicator': 'Moving Averages',
                        'signal': 'Sell',
                        'strength': 'Strong',
                        'value': None,
                        'description': 'Death Cross: 50-day SMA crossed below 200-day SMA'
                    })
        
        # Price crossing above/below moving averages
        if not pd.isna(latest['sma_20']):
            if len(indicators) >= 2:
                prev = indicators.iloc[-2]
                if latest['close'] > latest['sma_20'] and prev['close'] <= prev['sma_20']:
                    signals.append({
                        'indicator': 'Moving Averages',
                        'signal': 'Buy',
                        'strength': 'Weak',
                        'value': None,
                        'description': 'Price crossed above 20-day SMA'
                    })
                elif latest['close'] < latest['sma_20'] and prev['close'] >= prev['sma_20']:
                    signals.append({
                        'indicator': 'Moving Averages',
                        'signal': 'Sell',
                        'strength': 'Weak',
                        'value': None,
                        'description': 'Price crossed below 20-day SMA'
                    })
        
        # Trend-based signals
        if not pd.isna(latest['trend']):
            trend = latest['trend']
            if trend == 'uptrend':
                signals.append({
                    'indicator': 'Trend',
                    'signal': 'Buy',
                    'strength': 'Moderate',
                    'value': round(latest['trend_slope'], 4) if not pd.isna(latest['trend_slope']) else None,
                    'description': 'Price is in an uptrend'
                })
            elif trend == 'downtrend':
                signals.append({
                    'indicator': 'Trend',
                    'signal': 'Sell',
                    'strength': 'Moderate',
                    'value': round(latest['trend_slope'], 4) if not pd.isna(latest['trend_slope']) else None,
                    'description': 'Price is in a downtrend'
                })
        
        return {
            'symbol': symbol,
            'timestamp': latest['timestamp'],
            'close': latest['close'],
            'signals': signals
        }
    except Exception as e:
        logger.error(f"Failed to generate signals for {symbol}: {str(e)}", exc_info=True)
        return None

def update_technical_indicators(config):
    """Update technical indicators for all available symbols"""
    try:
        if not config.getboolean('TECHNICAL', 'Enabled'):
            logger.info("Technical analysis is disabled in config")
            return
            
        # Get list of symbols from the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT symbol FROM ohlcv_data
            ORDER BY (
                SELECT MAX(timestamp) FROM ohlcv_data as t2 
                WHERE t2.symbol = ohlcv_data.symbol
            ) DESC
        """)
        symbols = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        logger.info(f"Updating technical indicators for {len(symbols)} symbols")
        
        for symbol in symbols:
            try:
                logger.info(f"Calculating indicators for {symbol}")
                
                # Calculate indicators
                indicators_df = calculate_all_indicators(symbol)
                
                if indicators_df is not None and not indicators_df.empty:
                    # Store indicators
                    store_technical_indicators(symbol, indicators_df)
                    
                    # Generate signals
                    signals = generate_signals(symbol)
                    if signals:
                        # Log strong signals
                        strong_signals = [s for s in signals['signals'] if s['strength'] == 'Strong']
                        if strong_signals:
                            for signal in strong_signals:
                                logger.info(f"Strong {signal['signal']} signal for {symbol} from {signal['indicator']}: {signal['description']}")
            except Exception as e:
                logger.error(f"Error processing technical indicators for {symbol}: {str(e)}", exc_info=True)
                continue
                
        logger.info("Technical indicators update completed")
    except Exception as e:
        logger.error(f"Failed to update technical indicators: {str(e)}", exc_info=True)
