import ccxt
import pandas as pd
import time
import datetime
import sqlite3
from utils.logging_config import get_logger
from utils.cache_manager import cache_data_collection, cache_manager
from utils.performance_monitor import performance_monitor
from database.operations import get_db_connection

logger = get_logger(__name__)

def get_exchange_instance(exchange_id):
    """Initialize and return an exchange instance"""
    try:
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class({
            'enableRateLimit': True,  # required by the Manual
        })
        return exchange
    except Exception as e:
        logger.error(f"Failed to initialize exchange {exchange_id}: {str(e)}", exc_info=True)
        return None

@cache_data_collection(ttl=300)  # Cache for 5 minutes
@performance_monitor()
def get_top_cryptocurrencies(exchange, limit=100):
    """Get top cryptocurrencies by market cap"""
    try:
        markets = exchange.load_markets()
        tickers = exchange.fetch_tickers()
        
        # Filter for USDT pairs as they're most common
        usdt_pairs = [symbol for symbol in tickers.keys() if symbol.endswith('/USDT')]
        
        # Sort by volume (as a proxy for market cap)
        sorted_pairs = sorted(
            usdt_pairs, 
            key=lambda symbol: tickers[symbol]['quoteVolume'] if 'quoteVolume' in tickers[symbol] else 0,
            reverse=True
        )
        
        return sorted_pairs[:limit]
    except Exception as e:
        logger.error(f"Failed to get top cryptocurrencies: {str(e)}", exc_info=True)
        return []

def fetch_ohlcv_data(exchange, symbol, timeframe='1d', limit=365):
    """Fetch OHLCV data for a specific symbol"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['symbol'] = symbol
        df['exchange'] = exchange.id
        return df
    except Exception as e:
        logger.error(f"Failed to fetch OHLCV data for {symbol} on {exchange.id}: {str(e)}", exc_info=True)
        return pd.DataFrame()

def store_ohlcv_data(df):
    """Store OHLCV data in the database"""
    if df.empty:
        return
    
    try:
        # Since pandas has issues with different parameter styles between SQLite and PostgreSQL,
        # we'll insert the data manually with the correct parameter style
        import os
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for _, row in df.iterrows():
            # Format timestamp correctly if it's not already a string
            timestamp = row['timestamp']
            if not isinstance(timestamp, str):
                timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                
            # Use the right parameter style based on the database
            if 'DATABASE_URL' in os.environ:
                # PostgreSQL uses %s for parameters
                cursor.execute(
                    """
                    INSERT INTO ohlcv_data 
                    (symbol, exchange, timestamp, open, high, low, close, volume) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        row['symbol'], row['exchange'], timestamp,
                        float(row['open']), float(row['high']), float(row['low']),
                        float(row['close']), float(row['volume'])
                    )
                )
            else:
                # SQLite uses ? for parameters
                cursor.execute(
                    """
                    INSERT INTO ohlcv_data 
                    (symbol, exchange, timestamp, open, high, low, close, volume) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row['symbol'], row['exchange'], timestamp,
                        float(row['open']), float(row['high']), float(row['low']),
                        float(row['close']), float(row['volume'])
                    )
                )
        
        conn.commit()
        conn.close()
        logger.info(f"Stored {len(df)} OHLCV records for {df['symbol'].iloc[0]}")
    except Exception as e:
        logger.error(f"Failed to store OHLCV data: {str(e)}", exc_info=True)

def update_exchange_data(config):
    """Update cryptocurrency data from exchanges"""
    try:
        # Get configuration
        exchange_ids = config['EXCHANGES']['Exchanges'].split(',')
        top_crypto_count = int(config['EXCHANGES']['TopCryptoCount'])
        timeframes = config['EXCHANGES'].get('Timeframes', '1d').split(',')
        
        # Start with the most frequent timeframe for real-time data
        timeframes.sort(key=lambda tf: {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30, '1h': 60, '4h': 240, '1d': 1440
        }.get(tf, 9999))
        
        logger.info(f"Starting data collection for timeframes: {timeframes}")
        
        for exchange_id in exchange_ids:
            exchange_id = exchange_id.strip()
            logger.info(f"Updating data from exchange: {exchange_id}")
            
            exchange = get_exchange_instance(exchange_id)
            if not exchange:
                continue
                
            # Get top cryptocurrencies
            top_cryptos = get_top_cryptocurrencies(exchange, limit=top_crypto_count)
            logger.info(f"Found {len(top_cryptos)} top cryptocurrencies on {exchange_id}")
            
            # Track successful updates to show progress
            successful_updates = 0
            
            # For each cryptocurrency, fetch data for all timeframes
            for symbol in top_cryptos:
                for timeframe in timeframes:
                    try:
                        # Determine the appropriate limit based on timeframe to avoid fetching too much data
                        limit_map = {
                            '1m': 300,    # 5 hours of 1-minute data
                            '5m': 288,    # 24 hours of 5-minute data
                            '15m': 192,   # 48 hours of 15-minute data
                            '30m': 168,   # 3.5 days of 30-minute data
                            '1h': 168,    # 7 days of hourly data
                            '4h': 120,    # 20 days of 4-hour data
                            '1d': 365     # 1 year of daily data
                        }
                        limit = limit_map.get(timeframe, 100)
                        
                        logger.info(f"Fetching {timeframe} data for {symbol} from {exchange_id}")
                        df = fetch_ohlcv_data(exchange, symbol, timeframe=timeframe, limit=limit)
                        
                        if not df.empty:
                            # Add timeframe column
                            df['timeframe'] = timeframe
                            
                            # Clean up any existing data for this symbol, exchange, timeframe combination
                            # for the same time period to avoid duplicates
                            conn = get_db_connection()
                            min_timestamp = df['timestamp'].min()
                            max_timestamp = df['timestamp'].max()
                            
                            cursor = conn.cursor()
                            
                            # Use different parameter styles for PostgreSQL vs SQLite
                            import os
                            if 'DATABASE_URL' in os.environ:
                                # PostgreSQL
                                cursor.execute(
                                    """
                                    DELETE FROM ohlcv_data 
                                    WHERE symbol = %s AND exchange = %s AND timeframe = %s 
                                    AND timestamp BETWEEN %s AND %s
                                    """,
                                    (symbol, exchange_id, timeframe, min_timestamp, max_timestamp)
                                )
                            else:
                                # SQLite
                                cursor.execute(
                                    """
                                    DELETE FROM ohlcv_data 
                                    WHERE symbol = ? AND exchange = ? AND timeframe = ? 
                                    AND timestamp BETWEEN ? AND ?
                                    """,
                                    (symbol, exchange_id, timeframe, min_timestamp, max_timestamp)
                                )
                            conn.commit()
                            conn.close()
                            
                            # Store the new data
                            store_ohlcv_data(df)
                            successful_updates += 1
                        
                        # Respect rate limits
                        time.sleep(exchange.rateLimit / 1000)
                    except Exception as e:
                        logger.error(f"Error processing {timeframe} data for {symbol} from {exchange_id}: {str(e)}", exc_info=True)
                        continue
            
            logger.info(f"Completed update from exchange: {exchange_id}, successful updates: {successful_updates}")
    except Exception as e:
        logger.error(f"Failed to update exchange data: {str(e)}", exc_info=True)
        raise

def get_latest_prices(symbols=None, exchange_id='binance'):
    """Get latest prices for specified symbols or all available symbols"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check what database we're using
        import os
        is_postgres = 'DATABASE_URL' in os.environ
        
        if symbols:
            if is_postgres:
                # PostgreSQL
                placeholders = ','.join(['%s'] * len(symbols))
                query = f"""
                    SELECT symbol, exchange, timestamp, close 
                    FROM ohlcv_data
                    WHERE (symbol, exchange, timestamp) IN (
                        SELECT symbol, exchange, MAX(timestamp)
                        FROM ohlcv_data
                        WHERE symbol IN ({placeholders}) AND exchange = %s
                        GROUP BY symbol, exchange
                    )
                """
            else:
                # SQLite
                placeholders = ','.join(['?'] * len(symbols))
                query = f"""
                    SELECT symbol, exchange, timestamp, close 
                    FROM ohlcv_data
                    WHERE (symbol, exchange, timestamp) IN (
                        SELECT symbol, exchange, MAX(timestamp)
                        FROM ohlcv_data
                        WHERE symbol IN ({placeholders}) AND exchange = ?
                        GROUP BY symbol, exchange
                    )
                """
            cursor.execute(query, symbols + [exchange_id])
        else:
            if is_postgres:
                # PostgreSQL
                query = """
                    SELECT symbol, exchange, timestamp, close 
                    FROM ohlcv_data
                    WHERE (symbol, exchange, timestamp) IN (
                        SELECT symbol, exchange, MAX(timestamp)
                        FROM ohlcv_data
                        WHERE exchange = %s
                        GROUP BY symbol, exchange
                    )
                """
            else:
                # SQLite
                query = """
                    SELECT symbol, exchange, timestamp, close 
                    FROM ohlcv_data
                    WHERE (symbol, exchange, timestamp) IN (
                        SELECT symbol, exchange, MAX(timestamp)
                        FROM ohlcv_data
                        WHERE exchange = ?
                        GROUP BY symbol, exchange
                    )
                """
            cursor.execute(query, [exchange_id])
            
        results = cursor.fetchall()
        conn.close()
        
        prices = {}
        for row in results:
            symbol, exchange, timestamp, close = row
            prices[symbol] = {
                'price': close,
                'timestamp': timestamp,
                'exchange': exchange
            }
        
        return prices
    except Exception as e:
        logger.error(f"Failed to get latest prices: {str(e)}", exc_info=True)
        return {}
