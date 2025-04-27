import ccxt
import pandas as pd
import time
import datetime
import sqlite3
from utils.logging_config import get_logger
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
        conn = get_db_connection()
        df.to_sql('ohlcv_data', conn, if_exists='append', index=False)
        conn.close()
        logger.info(f"Stored {len(df)} OHLCV records for {df['symbol'].iloc[0]}")
    except Exception as e:
        logger.error(f"Failed to store OHLCV data: {str(e)}", exc_info=True)

def update_exchange_data(config):
    """Update cryptocurrency data from exchanges"""
    try:
        # Get list of exchanges from config
        exchange_ids = config['EXCHANGES']['Exchanges'].split(',')
        top_crypto_count = int(config['EXCHANGES']['TopCryptoCount'])
        
        for exchange_id in exchange_ids:
            exchange_id = exchange_id.strip()
            logger.info(f"Updating data from exchange: {exchange_id}")
            
            exchange = get_exchange_instance(exchange_id)
            if not exchange:
                continue
                
            # Get top cryptocurrencies
            top_cryptos = get_top_cryptocurrencies(exchange, limit=top_crypto_count)
            logger.info(f"Found {len(top_cryptos)} top cryptocurrencies on {exchange_id}")
            
            # Fetch and store OHLCV data for each cryptocurrency
            for symbol in top_cryptos:
                try:
                    logger.info(f"Fetching data for {symbol} from {exchange_id}")
                    df = fetch_ohlcv_data(exchange, symbol)
                    
                    if not df.empty:
                        # Clean up any existing data for this symbol/exchange combination for the same dates
                        conn = get_db_connection()
                        min_date = df['timestamp'].min().strftime('%Y-%m-%d')
                        max_date = df['timestamp'].max().strftime('%Y-%m-%d')
                        
                        cursor = conn.cursor()
                        cursor.execute(
                            "DELETE FROM ohlcv_data WHERE symbol = ? AND exchange = ? AND date(timestamp) BETWEEN ? AND ?",
                            (symbol, exchange_id, min_date, max_date)
                        )
                        conn.commit()
                        conn.close()
                        
                        # Store the new data
                        store_ohlcv_data(df)
                    
                    # Respect rate limits
                    time.sleep(exchange.rateLimit / 1000)
                except Exception as e:
                    logger.error(f"Error processing {symbol} from {exchange_id}: {str(e)}", exc_info=True)
                    continue
            
            logger.info(f"Completed update from exchange: {exchange_id}")
    except Exception as e:
        logger.error(f"Failed to update exchange data: {str(e)}", exc_info=True)
        raise

def get_latest_prices(symbols=None, exchange_id='binance'):
    """Get latest prices for specified symbols or all available symbols"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if symbols:
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
