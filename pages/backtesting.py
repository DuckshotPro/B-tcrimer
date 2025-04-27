import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

from database.operations import get_db_connection
from analysis.backtesting import (
    get_available_strategies, run_backtest, save_backtest_results,
    get_recent_backtests, get_backtest_details,
    MovingAverageCrossoverStrategy, RSIStrategy, MACDStrategy
)
from utils.logging_config import get_logger

logger = get_logger(__name__)

def show():
    """Display the backtesting page"""
    st.title("Strategy Backtesting")
    
    try:
        # Create tabs for different backtesting functions
        tabs = st.tabs(["Run Backtest", "Results History"])
        
        # Run backtest tab
        with tabs[0]:
            show_run_backtest()
        
        # Results history tab
        with tabs[1]:
            show_backtest_history()
    
    except Exception as e:
        logger.error(f"Error displaying backtesting page: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")

def show_run_backtest():
    """Display the run backtest interface"""
    st.header("Run Backtest")
    st.write("Backtest trading strategies on historical cryptocurrency data.")
    
    # Get available cryptocurrencies
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT symbol FROM ohlcv_data
        ORDER BY symbol
    """)
    
    available_symbols = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if not available_symbols:
        st.warning("No cryptocurrency data found. Please refresh data first.")
        return
    
    # Define available strategies
    strategies = get_available_strategies()
    strategy_names = [strategy.name for strategy in strategies]
    
    # Define available time periods
    time_periods = {
        "1 Month": 30,
        "3 Months": 90,
        "6 Months": 180,
        "1 Year": 365
    }
    
    # Create form for backtest parameters
    with st.form("backtest_form"):
        st.subheader("Backtest Parameters")
        
        # Select cryptocurrency
        symbol = st.selectbox("Cryptocurrency", available_symbols)
        
        # Select strategy
        strategy_name = st.selectbox("Trading Strategy", strategy_names)
        
        # Select time period
        period_name = st.selectbox("Time Period", list(time_periods.keys()))
        period_days = time_periods[period_name]
        
        # Trading parameters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            initial_capital = st.number_input("Initial Capital (USDT)", min_value=100.0, value=10000.0, step=1000.0)
        
        with col2:
            position_size = st.slider("Position Size (%)", min_value=10, max_value=100, value=25) / 100
        
        with col3:
            stop_loss = st.slider("Stop Loss (%)", min_value=1, max_value=20, value=5) / 100
        
        # Submit button
        submitted = st.form_submit_button("Run Backtest")
        
        if submitted:
            try:
                # Find the selected strategy object
                selected_strategy = next((s for s in strategies if s.name == strategy_name), None)
                
                if not selected_strategy:
                    st.error("Strategy not found.")
                    return
                
                # Run backtest
                with st.spinner(f"Running backtest for {symbol} with {strategy_name}..."):
                    backtest_results = run_backtest(
                        symbol=symbol,
                        strategy=selected_strategy,
                        days=period_days,
                        initial_capital=initial_capital,
                        position_size=position_size,
                        stop_loss=stop_loss
                    )
                
                if backtest_results:
                    # Save results to database
                    backtest_id = save_backtest_results(backtest_results)
                    
                    if backtest_id:
                        st.success(f"Backtest completed and saved (ID: {backtest_id})")
                    
                    # Display results
                    display_backtest_results(backtest_results)
                else:
                    st.error("Failed to run backtest. Please check logs for details.")
            
            except Exception as e:
                logger.error(f"Error running backtest: {str(e)}", exc_info=True)
                st.error(f"Error running backtest: {str(e)}")
    
    # Advanced strategy configuration
    with st.expander("Advanced Strategy Configuration"):
        st.write("Customize strategy parameters")
        
        # Moving Average Crossover strategy parameters
        st.subheader("Moving Average Crossover")
        ma_col1, ma_col2 = st.columns(2)
        
        with ma_col1:
            ma_short = st.number_input("Short MA Period", min_value=1, max_value=50, value=20)
        
        with ma_col2:
            ma_long = st.number_input("Long MA Period", min_value=5, max_value=200, value=50)
        
        if st.button("Create Custom MA Crossover"):
            custom_ma = MovingAverageCrossoverStrategy(short_period=ma_short, long_period=ma_long)
            st.session_state.custom_strategy = custom_ma
            st.success(f"Custom MA Crossover ({ma_short},{ma_long}) strategy created")
        
        # RSI strategy parameters
        st.subheader("RSI Strategy")
        rsi_col1, rsi_col2, rsi_col3 = st.columns(3)
        
        with rsi_col1:
            rsi_period = st.number_input("RSI Period", min_value=1, max_value=30, value=14)
        
        with rsi_col2:
            rsi_overbought = st.number_input("Overbought Level", min_value=50, max_value=90, value=70)
        
        with rsi_col3:
            rsi_oversold = st.number_input("Oversold Level", min_value=10, max_value=50, value=30)
        
        if st.button("Create Custom RSI Strategy"):
            custom_rsi = RSIStrategy(period=rsi_period, overbought=rsi_overbought, oversold=rsi_oversold)
            st.session_state.custom_strategy = custom_rsi
            st.success(f"Custom RSI ({rsi_period}) strategy created")
        
        # MACD strategy parameters
        st.subheader("MACD Strategy")
        macd_col1, macd_col2, macd_col3 = st.columns(3)
        
        with macd_col1:
            macd_fast = st.number_input("Fast Period", min_value=5, max_value=30, value=12)
        
        with macd_col2:
            macd_slow = st.number_input("Slow Period", min_value=10, max_value=50, value=26)
        
        with macd_col3:
            macd_signal = st.number_input("Signal Period", min_value=1, max_value=20, value=9)
        
        if st.button("Create Custom MACD Strategy"):
            custom_macd = MACDStrategy(fast_period=macd_fast, slow_period=macd_slow, signal_period=macd_signal)
            st.session_state.custom_strategy = custom_macd
            st.success(f"Custom MACD ({macd_fast},{macd_slow},{macd_signal}) strategy created")
        
        # Use custom strategy for backtest
        if 'custom_strategy' in st.session_state:
            if st.button("Use Custom Strategy for Backtest"):
                strategies.append(st.session_state.custom_strategy)
                st.success("Custom strategy added to available strategies.")
                st.rerun()

def show_backtest_history():
    """Display backtest history and results"""
    st.header("Backtest History")
    
    # Get recent backtests
    backtests = get_recent_backtests(limit=20)
    
    if not backtests:
        st.info("No backtest history found. Run a backtest to get started.")
        return
    
    # Display backtest summary table
    st.subheader("Recent Backtest Results")
    
    # Prepare data for table
    table_data = []
    for backtest in backtests:
        table_data.append({
            'ID': backtest['id'],
            'Symbol': backtest['symbol'],
            'Strategy': backtest['strategy'],
            'Initial Capital': f"${backtest['initial_capital']:,.2f}",
            'Final Capital': f"${backtest['final_capital']:,.2f}",
            'Return': f"{backtest['total_return']:+.2f}%",
            'Sharpe': f"{backtest['sharpe_ratio']:.2f}",
            'Win Rate': f"{backtest['win_rate']:.2f}%",
            'Date': backtest['timestamp']
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)
    
    # Select backtest to view
    selected_id = st.selectbox(
        "Select backtest to view details",
        [b['id'] for b in backtests],
        format_func=lambda x: f"ID {x}: {next((b['symbol'] for b in backtests if b['id'] == x), 'Unknown')} - {next((b['strategy'] for b in backtests if b['id'] == x), 'Unknown')}"
    )
    
    # Get and display selected backtest details
    if selected_id:
        backtest_details = get_backtest_details(selected_id)
        
        if backtest_details:
            display_backtest_details(backtest_details)
        else:
            st.error("Failed to load backtest details.")

def display_backtest_results(results):
    """Display backtest results with charts and metrics"""
    metrics = results['metrics']
    results_df = results['results']
    
    # Display summary metrics
    st.subheader("Backtest Results Summary")
    
    # Create metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Return", 
            f"{metrics['total_return_pct']:+.2f}%",
            delta=f"{metrics['outperformance_pct']:+.2f}% vs Market"
        )
    
    with col2:
        st.metric(
            "Annual Return", 
            f"{metrics['annual_return_pct']:+.2f}%"
        )
    
    with col3:
        st.metric(
            "Sharpe Ratio", 
            f"{metrics['sharpe_ratio']:.2f}"
        )
    
    with col4:
        st.metric(
            "Max Drawdown", 
            f"{metrics['max_drawdown_pct']:.2f}%"
        )
    
    # Create second row of metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Win Rate", 
            f"{metrics['win_rate_pct']:.2f}%"
        )
    
    with col2:
        st.metric(
            "Total Trades", 
            f"{metrics['total_trades']}"
        )
    
    with col3:
        profit_factor_str = "∞" if metrics['profit_factor'] == float('inf') else f"{metrics['profit_factor']:.2f}"
        st.metric(
            "Profit Factor", 
            profit_factor_str
        )
    
    with col4:
        st.metric(
            "Market Return", 
            f"{metrics['market_return_pct']:+.2f}%"
        )
    
    # Portfolio vs Market Performance chart
    st.subheader("Portfolio Performance")
    
    # Create portfolio chart
    fig = go.Figure()
    
    # Add close price line
    fig.add_trace(go.Scatter(
        x=results_df['timestamp'],
        y=results_df['close'] / results_df['close'].iloc[0] * metrics['initial_capital'],
        mode='lines',
        name='Buy & Hold'
    ))
    
    # Add portfolio value line
    fig.add_trace(go.Scatter(
        x=results_df['timestamp'],
        y=results_df['portfolio'],
        mode='lines',
        name='Strategy'
    ))
    
    # Update layout
    fig.update_layout(
        title=f"{results['symbol']} Strategy vs Buy & Hold",
        xaxis_title="Date",
        yaxis_title="Portfolio Value (USDT)",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display trade markers on price chart
    st.subheader("Trading Signals")
    
    # Create candlestick chart with trade markers
    fig = go.Figure()
    
    # Add candlestick trace
    fig.add_trace(go.Candlestick(
        x=results_df['timestamp'],
        open=results_df['open'],
        high=results_df['high'],
        low=results_df['low'],
        close=results_df['close'],
        name=results['symbol']
    ))
    
    # Add buy markers
    buy_signals = results_df[results_df['signal'] == 1]
    if not buy_signals.empty:
        fig.add_trace(go.Scatter(
            x=buy_signals['timestamp'],
            y=buy_signals['close'] * 0.98,  # Slightly below the price for visibility
            mode='markers',
            marker=dict(
                symbol='triangle-up',
                size=12,
                color='green',
                line=dict(width=2, color='darkgreen')
            ),
            name='Buy Signal'
        ))
    
    # Add sell markers
    sell_signals = results_df[results_df['signal'] == -1]
    if not sell_signals.empty:
        fig.add_trace(go.Scatter(
            x=sell_signals['timestamp'],
            y=sell_signals['close'] * 1.02,  # Slightly above the price for visibility
            mode='markers',
            marker=dict(
                symbol='triangle-down',
                size=12,
                color='red',
                line=dict(width=2, color='darkred')
            ),
            name='Sell Signal'
        ))
    
    # Update layout
    fig.update_layout(
        title=f"{results['symbol']} Price with Trading Signals",
        xaxis_title="Date",
        yaxis_title="Price",
        height=500,
        xaxis_rangeslider_visible=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display equity curve
    st.subheader("Equity Curve")
    
    # Create equity chart
    equity_fig = go.Figure()
    
    # Add equity line
    equity_fig.add_trace(go.Scatter(
        x=results_df['timestamp'],
        y=results_df['portfolio'],
        mode='lines',
        name='Portfolio Value',
        line=dict(color='blue')
    ))
    
    # Add drawdown as area chart below
    if 'portfolio' in results_df.columns:
        # Calculate drawdown
        rolling_max = results_df['portfolio'].cummax()
        drawdown = (results_df['portfolio'] / rolling_max - 1) * 100
        
        # Add drawdown trace
        equity_fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=drawdown,
            mode='lines',
            name='Drawdown (%)',
            line=dict(color='red'),
            yaxis='y2'
        ))
    
    # Update layout
    equity_fig.update_layout(
        title="Portfolio Value and Drawdown",
        xaxis_title="Date",
        yaxis_title="Portfolio Value (USDT)",
        yaxis2=dict(
            title="Drawdown (%)",
            titlefont=dict(color="red"),
            tickfont=dict(color="red"),
            anchor="x",
            overlaying="y",
            side="right",
            range=[min(drawdown) * 1.1, 5]  # Adjust range to make drawdown visible
        ),
        height=500
    )
    
    st.plotly_chart(equity_fig, use_container_width=True)
    
    # Display trades table
    st.subheader("Trades Summary")
    
    # Extract trades
    trades_df = results_df[results_df['pnl'] != 0].copy()
    
    if trades_df.empty:
        st.info("No trades were executed during the backtest period.")
    else:
        # Format trades for display
        trades_for_display = []
        
        for _, trade in trades_df.iterrows():
            trades_for_display.append({
                'Entry Date': trade['timestamp'],
                'Entry Price': f"${trade['entry_price']:.2f}" if not pd.isna(trade['entry_price']) else 'N/A',
                'Exit Price': f"${trade['exit_price']:.2f}" if not pd.isna(trade['exit_price']) else 'N/A',
                'P&L': f"${trade['pnl']:.2f}",
                'P&L %': f"{(trade['exit_price'] / trade['entry_price'] - 1) * 100:+.2f}%" if not pd.isna(trade['entry_price']) and not pd.isna(trade['exit_price']) else 'N/A'
            })
        
        trades_display_df = pd.DataFrame(trades_for_display)
        st.dataframe(trades_display_df, use_container_width=True)
        
        # Display trade statistics
        profitable_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] < 0]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Profitable Trades", len(profitable_trades))
        
        with col2:
            st.metric("Losing Trades", len(losing_trades))
        
        with col3:
            avg_profit = profitable_trades['pnl'].mean() if not profitable_trades.empty else 0
            avg_loss = losing_trades['pnl'].mean() if not losing_trades.empty else 0
            st.metric("Avg Profit/Loss Ratio", f"{abs(avg_profit / avg_loss):.2f}" if avg_loss != 0 else "∞")

def display_backtest_details(backtest_details):
    """Display details of a saved backtest"""
    summary = backtest_details['summary']
    trades = backtest_details['trades']
    
    # Display summary metrics
    st.subheader("Backtest Summary")
    
    # Create metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Symbol", 
            summary['symbol']
        )
    
    with col2:
        st.metric(
            "Strategy", 
            summary['strategy']
        )
    
    with col3:
        st.metric(
            "Period", 
            f"{summary['period_days']} days"
        )
    
    with col4:
        st.metric(
            "Date", 
            summary['timestamp'] if isinstance(summary['timestamp'], str) else summary['timestamp'].strftime('%Y-%m-%d')
        )
    
    # Display performance metrics
    st.subheader("Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Initial Capital", 
            f"${summary['initial_capital']:,.2f}"
        )
    
    with col2:
        st.metric(
            "Final Capital", 
            f"${summary['final_capital']:,.2f}"
        )
    
    with col3:
        st.metric(
            "Total Return", 
            f"{summary['total_return']:+.2f}%"
        )
    
    with col4:
        st.metric(
            "Annual Return", 
            f"{summary['annual_return']:+.2f}%"
        )
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Sharpe Ratio", 
            f"{summary['sharpe_ratio']:.2f}"
        )
    
    with col2:
        st.metric(
            "Max Drawdown", 
            f"{summary['max_drawdown']:.2f}%"
        )
    
    with col3:
        st.metric(
            "Win Rate", 
            f"{summary['win_rate']:.2f}%"
        )
    
    with col4:
        profit_factor_str = "∞" if summary['profit_factor'] == float('inf') else f"{summary['profit_factor']:.2f}"
        st.metric(
            "Profit Factor", 
            profit_factor_str
        )
    
    # Display trades
    st.subheader("Trades")
    
    if not trades:
        st.info("No trades recorded for this backtest.")
    else:
        # Prepare trades for display
        trades_for_display = []
        
        for trade in trades:
            # Format dates
            entry_date = trade['entry_date']
            if isinstance(entry_date, str):
                entry_date = datetime.strptime(entry_date, '%Y-%m-%d %H:%M:%S')
            
            exit_date = trade['exit_date']
            if isinstance(exit_date, str):
                exit_date = datetime.strptime(exit_date, '%Y-%m-%d %H:%M:%S')
            
            trades_for_display.append({
                'Entry Date': entry_date,
                'Entry Price': f"${trade['entry_price']:.2f}" if trade['entry_price'] else 'N/A',
                'Exit Date': exit_date,
                'Exit Price': f"${trade['exit_price']:.2f}" if trade['exit_price'] else 'N/A',
                'P&L': f"${trade['pnl']:.2f}",
                'P&L %': f"{(trade['exit_price'] / trade['entry_price'] - 1) * 100:+.2f}%" if trade['entry_price'] and trade['exit_price'] else 'N/A'
            })
        
        trades_display_df = pd.DataFrame(trades_for_display)
        st.dataframe(trades_display_df, use_container_width=True)
        
        # Display trade distribution chart
        st.subheader("Trade Profit Distribution")
        
        profit_values = [trade['pnl'] for trade in trades]
        fig = px.histogram(
            x=profit_values,
            nbins=20,
            labels={"x": "Profit/Loss (USDT)"},
            title="Trade Profit Distribution"
        )
        
        # Color positive and negative profits differently
        fig.update_traces(marker_color='green', selector=dict(x=[p for p in profit_values if p > 0]))
        fig.update_traces(marker_color='red', selector=dict(x=[p for p in profit_values if p <= 0]))
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Add some additional statistics
        profitable_trades = [trade for trade in trades if trade['pnl'] > 0]
        losing_trades = [trade for trade in trades if trade['pnl'] < 0]
        
        avg_profit = sum([trade['pnl'] for trade in profitable_trades]) / len(profitable_trades) if profitable_trades else 0
        avg_loss = sum([trade['pnl'] for trade in losing_trades]) / len(losing_trades) if losing_trades else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Average Profit", f"${avg_profit:.2f}")
        
        with col2:
            st.metric("Average Loss", f"${avg_loss:.2f}")
        
        with col3:
            st.metric("Largest Win", f"${max([trade['pnl'] for trade in trades], default=0):.2f}")
