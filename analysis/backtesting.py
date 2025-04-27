import pandas as pd
import numpy as np
import datetime
from utils.logging_config import get_logger
from database.operations import get_db_connection

logger = get_logger(__name__)

class Strategy:
    """Base class for trading strategies"""
    def __init__(self, name, description):
        self.name = name
        self.description = description
        
    def generate_signals(self, data):
        """Generate buy/sell signals - to be implemented by subclasses"""
        raise NotImplementedError()

class MovingAverageCrossoverStrategy(Strategy):
    """Simple moving average crossover strategy"""
    def __init__(self, short_period=20, long_period=50):
        name = f"MA Crossover ({short_period},{long_period})"
        description = f"Moving Average Crossover Strategy using {short_period} and {long_period} day periods"
        super().__init__(name, description)
        self.short_period = short_period
        self.long_period = long_period
        
    def generate_signals(self, data):
        """Generate buy/sell signals based on moving average crossovers"""
        try:
            # Calculate moving averages
            data['short_ma'] = data['close'].rolling(window=self.short_period).mean()
            data['long_ma'] = data['close'].rolling(window=self.long_period).mean()
            
            # Initialize signal column
            data['signal'] = 0
            
            # Generate signals: 1 for buy, -1 for sell
            # Buy when short MA crosses above long MA
            # Sell when short MA crosses below long MA
            for i in range(1, len(data)):
                if (data['short_ma'].iloc[i-1] <= data['long_ma'].iloc[i-1] and 
                    data['short_ma'].iloc[i] > data['long_ma'].iloc[i]):
                    data.loc[data.index[i], 'signal'] = 1
                elif (data['short_ma'].iloc[i-1] >= data['long_ma'].iloc[i-1] and 
                      data['short_ma'].iloc[i] < data['long_ma'].iloc[i]):
                    data.loc[data.index[i], 'signal'] = -1
            
            return data
        except Exception as e:
            logger.error(f"Error generating signals for MA Crossover strategy: {str(e)}", exc_info=True)
            return data

class RSIStrategy(Strategy):
    """RSI-based trading strategy"""
    def __init__(self, period=14, overbought=70, oversold=30):
        name = f"RSI ({period})"
        description = f"RSI Strategy using {period} day period, overbought at {overbought}, oversold at {oversold}"
        super().__init__(name, description)
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        
    def generate_signals(self, data):
        """Generate buy/sell signals based on RSI"""
        try:
            # Calculate RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
            
            rs = gain / loss
            data['rsi'] = 100 - (100 / (1 + rs))
            
            # Initialize signal column
            data['signal'] = 0
            
            # Generate signals: 1 for buy, -1 for sell
            # Buy when RSI crosses above oversold threshold
            # Sell when RSI crosses below overbought threshold
            for i in range(1, len(data)):
                if (data['rsi'].iloc[i-1] <= self.oversold and 
                    data['rsi'].iloc[i] > self.oversold):
                    data.loc[data.index[i], 'signal'] = 1
                elif (data['rsi'].iloc[i-1] >= self.overbought and 
                      data['rsi'].iloc[i] < self.overbought):
                    data.loc[data.index[i], 'signal'] = -1
            
            return data
        except Exception as e:
            logger.error(f"Error generating signals for RSI strategy: {str(e)}", exc_info=True)
            return data

class MACDStrategy(Strategy):
    """MACD-based trading strategy"""
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        name = f"MACD ({fast_period},{slow_period},{signal_period})"
        description = f"MACD Strategy using fast={fast_period}, slow={slow_period}, signal={signal_period}"
        super().__init__(name, description)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
    def generate_signals(self, data):
        """Generate buy/sell signals based on MACD crossovers"""
        try:
            # Calculate MACD
            ema_fast = data['close'].ewm(span=self.fast_period, adjust=False).mean()
            ema_slow = data['close'].ewm(span=self.slow_period, adjust=False).mean()
            
            data['macd'] = ema_fast - ema_slow
            data['macd_signal'] = data['macd'].ewm(span=self.signal_period, adjust=False).mean()
            data['macd_hist'] = data['macd'] - data['macd_signal']
            
            # Initialize signal column
            data['signal'] = 0
            
            # Generate signals: 1 for buy, -1 for sell
            # Buy when MACD crosses above signal line
            # Sell when MACD crosses below signal line
            for i in range(1, len(data)):
                if (data['macd'].iloc[i-1] <= data['macd_signal'].iloc[i-1] and 
                    data['macd'].iloc[i] > data['macd_signal'].iloc[i]):
                    data.loc[data.index[i], 'signal'] = 1
                elif (data['macd'].iloc[i-1] >= data['macd_signal'].iloc[i-1] and 
                      data['macd'].iloc[i] < data['macd_signal'].iloc[i]):
                    data.loc[data.index[i], 'signal'] = -1
            
            return data
        except Exception as e:
            logger.error(f"Error generating signals for MACD strategy: {str(e)}", exc_info=True)
            return data

def simulate_trading(data, initial_capital=10000.0, position_size=0.1, stop_loss=0.05):
    """Simulate trading based on signals"""
    try:
        # Make a copy of the data to avoid modifying the original
        df = data.copy()
        
        # Initialize columns for tracking portfolio
        df['position'] = 0  # Current position: 0 for no position, 1 for long
        df['entry_price'] = np.nan  # Price at which we entered the position
        df['exit_price'] = np.nan  # Price at which we exited the position
        df['pnl'] = 0.0  # Profit/Loss for each trade
        df['portfolio'] = initial_capital  # Portfolio value
        df['cash'] = initial_capital  # Cash on hand
        df['equity'] = 0.0  # Value of equity holdings
        
        # Iterate through the data to simulate trading
        position = 0
        entry_price = 0
        stop_price = 0
        
        for i in range(len(df)):
            # Get current signal and price
            signal = df['signal'].iloc[i]
            close_price = df['close'].iloc[i]
            
            # Update current position
            df.loc[df.index[i], 'position'] = position
            
            # If we have a buy signal and no position, enter long
            if signal == 1 and position == 0:
                # Calculate position size
                cash = df['cash'].iloc[i]
                position_value = cash * position_size
                shares = position_value / close_price
                
                # Enter position
                position = 1
                entry_price = close_price
                stop_price = entry_price * (1 - stop_loss)  # Set stop loss
                
                # Update portfolio
                df.loc[df.index[i], 'entry_price'] = entry_price
                df.loc[df.index[i], 'position'] = position
                df.loc[df.index[i], 'cash'] = cash - position_value
                df.loc[df.index[i], 'equity'] = shares * close_price
                df.loc[df.index[i], 'portfolio'] = df['cash'].iloc[i] + df['equity'].iloc[i]
                
            # If we have a sell signal and have a position, exit long
            elif (signal == -1 or close_price <= stop_price) and position == 1:
                # Calculate profit/loss
                cash = df['cash'].iloc[i]
                equity = df['equity'].iloc[i]
                exit_price = close_price
                pnl = (exit_price / entry_price - 1) * equity
                
                # Exit position
                position = 0
                
                # Update portfolio
                df.loc[df.index[i], 'exit_price'] = exit_price
                df.loc[df.index[i], 'position'] = position
                df.loc[df.index[i], 'pnl'] = pnl
                df.loc[df.index[i], 'cash'] = cash + equity
                df.loc[df.index[i], 'equity'] = 0.0
                df.loc[df.index[i], 'portfolio'] = df['cash'].iloc[i] + df['equity'].iloc[i]
            
            # Otherwise just update the portfolio value
            else:
                if i > 0:
                    df.loc[df.index[i], 'cash'] = df['cash'].iloc[i-1]
                    
                    if position == 1:
                        # Update equity value based on current price
                        shares = df['equity'].iloc[i-1] / df['close'].iloc[i-1]
                        df.loc[df.index[i], 'equity'] = shares * close_price
                    else:
                        df.loc[df.index[i], 'equity'] = 0.0
                        
                    df.loc[df.index[i], 'portfolio'] = df['cash'].iloc[i] + df['equity'].iloc[i]
        
        return df
    except Exception as e:
        logger.error(f"Error simulating trading: {str(e)}", exc_info=True)
        return data

def calculate_performance_metrics(data):
    """Calculate performance metrics for a backtest"""
    try:
        # Extract relevant data
        portfolio = data['portfolio']
        close_prices = data['close']
        
        # Calculate returns
        portfolio_returns = portfolio.pct_change().dropna()
        market_returns = close_prices.pct_change().dropna()
        
        # Calculate metrics
        initial_capital = portfolio.iloc[0]
        final_capital = portfolio.iloc[-1]
        total_return = (final_capital / initial_capital - 1) * 100
        
        # Daily metrics
        annual_return = (1 + total_return / 100) ** (252 / len(portfolio_returns)) - 1
        annual_return *= 100  # Convert to percentage
        
        daily_std = portfolio_returns.std() * 100
        annual_std = daily_std * np.sqrt(252)
        
        if annual_std == 0:
            sharpe_ratio = 0
        else:
            sharpe_ratio = annual_return / annual_std
        
        # Calculate drawdown
        rolling_max = portfolio.cummax()
        drawdown = (portfolio / rolling_max - 1) * 100
        max_drawdown = drawdown.min()
        
        # Calculate win rate
        trades = data[data['pnl'] != 0]
        if len(trades) > 0:
            win_rate = len(trades[trades['pnl'] > 0]) / len(trades) * 100
            avg_profit = trades[trades['pnl'] > 0]['pnl'].mean() if len(trades[trades['pnl'] > 0]) > 0 else 0
            avg_loss = trades[trades['pnl'] < 0]['pnl'].mean() if len(trades[trades['pnl'] < 0]) > 0 else 0
            profit_factor = abs(avg_profit / avg_loss) if avg_loss != 0 else float('inf')
        else:
            win_rate = 0
            avg_profit = 0
            avg_loss = 0
            profit_factor = 0
        
        # Market comparison
        market_return = (close_prices.iloc[-1] / close_prices.iloc[0] - 1) * 100
        outperformance = total_return - market_return
        
        return {
            'initial_capital': initial_capital,
            'final_capital': final_capital,
            'total_return_pct': total_return,
            'annual_return_pct': annual_return,
            'annual_volatility_pct': annual_std,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown,
            'total_trades': len(trades),
            'win_rate_pct': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'market_return_pct': market_return,
            'outperformance_pct': outperformance
        }
    except Exception as e:
        logger.error(f"Error calculating performance metrics: {str(e)}", exc_info=True)
        return {
            'initial_capital': 0,
            'final_capital': 0,
            'total_return_pct': 0,
            'annual_return_pct': 0,
            'annual_volatility_pct': 0,
            'sharpe_ratio': 0,
            'max_drawdown_pct': 0,
            'total_trades': 0,
            'win_rate_pct': 0,
            'avg_profit': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'market_return_pct': 0,
            'outperformance_pct': 0
        }

def run_backtest(symbol, strategy, exchange='binance', days=365, initial_capital=10000.0, position_size=0.1, stop_loss=0.05):
    """Run a backtest for a given symbol and strategy"""
    try:
        # Load historical data
        conn = get_db_connection()
        
        # Calculate the date threshold
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        
        query = """
            SELECT timestamp, open, high, low, close, volume
            FROM ohlcv_data
            WHERE symbol = ? AND exchange = ? AND date(timestamp) >= ?
            ORDER BY timestamp
        """
        
        data = pd.read_sql_query(query, conn, params=(symbol, exchange, threshold_date))
        conn.close()
        
        if data.empty:
            logger.warning(f"No historical data available for {symbol} on {exchange}")
            return None
            
        # Generate trading signals
        data = strategy.generate_signals(data)
        
        # Simulate trading
        results = simulate_trading(data, initial_capital, position_size, stop_loss)
        
        # Calculate performance metrics
        metrics = calculate_performance_metrics(results)
        
        return {
            'symbol': symbol,
            'strategy': strategy.name,
            'exchange': exchange,
            'period_days': days,
            'metrics': metrics,
            'results': results
        }
    except Exception as e:
        logger.error(f"Failed to run backtest for {symbol} with strategy {strategy.name}: {str(e)}", exc_info=True)
        return None

def get_available_strategies():
    """Get a list of available trading strategies"""
    return [
        MovingAverageCrossoverStrategy(20, 50),
        MovingAverageCrossoverStrategy(10, 30),
        MovingAverageCrossoverStrategy(5, 20),
        RSIStrategy(14, 70, 30),
        RSIStrategy(7, 75, 25),
        MACDStrategy(12, 26, 9),
        MACDStrategy(8, 17, 9)
    ]

def save_backtest_results(backtest):
    """Save backtest results to the database"""
    if not backtest:
        return
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Save backtest summary
        cursor.execute(
            """
            INSERT INTO backtest_results 
            (symbol, strategy, exchange, period_days, initial_capital, final_capital, 
             total_return, annual_return, annual_volatility, sharpe_ratio, max_drawdown,
             total_trades, win_rate, profit_factor, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                backtest['symbol'],
                backtest['strategy'],
                backtest['exchange'],
                backtest['period_days'],
                backtest['metrics']['initial_capital'],
                backtest['metrics']['final_capital'],
                backtest['metrics']['total_return_pct'],
                backtest['metrics']['annual_return_pct'],
                backtest['metrics']['annual_volatility_pct'],
                backtest['metrics']['sharpe_ratio'],
                backtest['metrics']['max_drawdown_pct'],
                backtest['metrics']['total_trades'],
                backtest['metrics']['win_rate_pct'],
                backtest['metrics']['profit_factor'],
                datetime.datetime.now()
            )
        )
        
        # Get the backtest ID
        backtest_id = cursor.lastrowid
        
        # Save detailed trade results
        trades = backtest['results'][backtest['results']['pnl'] != 0].copy()
        if not trades.empty:
            for _, trade in trades.iterrows():
                cursor.execute(
                    """
                    INSERT INTO backtest_trades
                    (backtest_id, entry_date, entry_price, exit_date, exit_price, pnl)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        backtest_id,
                        trade['timestamp'] if trade['entry_price'] > 0 else None,
                        trade['entry_price'] if not pd.isna(trade['entry_price']) else 0,
                        trade['timestamp'] if trade['exit_price'] > 0 else None,
                        trade['exit_price'] if not pd.isna(trade['exit_price']) else 0,
                        trade['pnl']
                    )
                )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved backtest results for {backtest['symbol']} with strategy {backtest['strategy']}")
        return backtest_id
    except Exception as e:
        logger.error(f"Failed to save backtest results: {str(e)}", exc_info=True)
        return None

def get_recent_backtests(limit=10):
    """Get most recent backtest results from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, symbol, strategy, exchange, period_days, 
                   initial_capital, final_capital, total_return, 
                   annual_return, sharpe_ratio, total_trades, win_rate,
                   timestamp
            FROM backtest_results
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,)
        )
        
        results = cursor.fetchall()
        conn.close()
        
        backtests = []
        for row in results:
            (id, symbol, strategy, exchange, period_days, 
             initial_capital, final_capital, total_return, 
             annual_return, sharpe_ratio, total_trades, win_rate,
             timestamp) = row
             
            backtests.append({
                'id': id,
                'symbol': symbol,
                'strategy': strategy,
                'exchange': exchange,
                'period_days': period_days,
                'initial_capital': initial_capital,
                'final_capital': final_capital,
                'total_return': total_return,
                'annual_return': annual_return,
                'sharpe_ratio': sharpe_ratio,
                'total_trades': total_trades,
                'win_rate': win_rate,
                'timestamp': timestamp
            })
        
        return backtests
    except Exception as e:
        logger.error(f"Failed to get recent backtests: {str(e)}", exc_info=True)
        return []

def get_backtest_details(backtest_id):
    """Get detailed information for a specific backtest"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get backtest summary
        cursor.execute(
            """
            SELECT * FROM backtest_results
            WHERE id = ?
            """,
            (backtest_id,)
        )
        
        summary = cursor.fetchone()
        if not summary:
            conn.close()
            return None
            
        # Get backtest trades
        cursor.execute(
            """
            SELECT entry_date, entry_price, exit_date, exit_price, pnl
            FROM backtest_trades
            WHERE backtest_id = ?
            ORDER BY entry_date
            """,
            (backtest_id,)
        )
        
        trades = cursor.fetchall()
        conn.close()
        
        # Convert summary to dict
        columns = [desc[0] for desc in cursor.description]
        summary_dict = {columns[i]: summary[i] for i in range(len(columns))}
        
        # Convert trades to list of dicts
        trades_list = []
        for trade in trades:
            entry_date, entry_price, exit_date, exit_price, pnl = trade
            trades_list.append({
                'entry_date': entry_date,
                'entry_price': entry_price,
                'exit_date': exit_date,
                'exit_price': exit_price,
                'pnl': pnl
            })
        
        return {
            'summary': summary_dict,
            'trades': trades_list
        }
    except Exception as e:
        logger.error(f"Failed to get backtest details for ID {backtest_id}: {str(e)}", exc_info=True)
        return None
