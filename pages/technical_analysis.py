import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

from database.operations import get_db_connection
from analysis.technical_indicators import calculate_all_indicators, generate_signals
from utils.logging_config import get_logger

logger = get_logger(__name__)

def show():
    """Display the technical analysis page"""
    st.title("Technical Analysis")
    
    try:
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
            st.warning("No cryptocurrency data found. Please refresh data to fetch from exchanges.")
            return
        
        # Sidebar for cryptocurrency selection
        st.sidebar.header("Cryptocurrency Selection")
        selected_symbol = st.sidebar.selectbox("Select cryptocurrency", available_symbols)
        
        # Main content
        st.header(f"Technical Analysis for {selected_symbol}")
        
        # Calculate indicators (or load from database)
        indicators_df = None
        
        # Check if we have recent indicators in the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT MAX(timestamp) FROM technical_indicators
            WHERE symbol = %s
        """, (selected_symbol,))
        
        result = cursor.fetchone()
        latest_indicator_time = result[0] if result and result[0] is not None else None
        
        if latest_indicator_time:
            # If indicators exist, check how recent they are
            if isinstance(latest_indicator_time, str):
                latest_indicator_time = datetime.strptime(latest_indicator_time, '%Y-%m-%d %H:%M:%S')
                
            time_diff = datetime.now() - latest_indicator_time
            hours_diff = time_diff.total_seconds() / 3600
            
            # If indicators are recent (less than 24 hours old), load from database
            if hours_diff < 24:
                query = """
                    SELECT * FROM technical_indicators
                    WHERE symbol = %s
                    ORDER BY timestamp DESC
                    LIMIT 180  -- Last 180 data points
                """
                
                indicators_df = pd.read_sql_query(query, conn, params=[selected_symbol])
                # Sort by timestamp ascending
                indicators_df.sort_values('timestamp', inplace=True)
        
        conn.close()
        
        # If we don't have recent indicators, calculate them
        if indicators_df is None or indicators_df.empty:
            with st.spinner("Calculating technical indicators..."):
                indicators_df = calculate_all_indicators(selected_symbol)
        
        if indicators_df is None or indicators_df.empty:
            st.error(f"No data available for {selected_symbol}")
            return
        
        # Generate trading signals
        signals = generate_signals(selected_symbol)
        
        if signals and signals['signals']:
            # Display signals
            st.subheader("Trading Signals")
            
            # Group signals by strength
            strong_signals = [s for s in signals['signals'] if s['strength'] == 'Strong']
            moderate_signals = [s for s in signals['signals'] if s['strength'] == 'Moderate']
            weak_signals = [s for s in signals['signals'] if s['strength'] == 'Weak']
            
            # Display strong signals prominently
            if strong_signals:
                for signal in strong_signals:
                    signal_color = "green" if signal['signal'] == 'Buy' else "red" if signal['signal'] == 'Sell' else "gray"
                    signal_emoji = "🟢" if signal['signal'] == 'Buy' else "🔴" if signal['signal'] == 'Sell' else "⚪"
                    
                    st.markdown(f"""
                    <div style="padding: 10px; border-radius: 5px; background-color: {signal_color}20; border-left: 5px solid {signal_color};">
                        <h3 style="color: {signal_color};">{signal_emoji} Strong {signal['signal']} Signal: {signal['indicator']}</h3>
                        <p>{signal['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Display other signals in a table
            other_signals = moderate_signals + weak_signals
            if other_signals:
                signals_data = []
                
                for signal in other_signals:
                    signals_data.append({
                        'Indicator': signal['indicator'],
                        'Signal': signal['signal'],
                        'Strength': signal['strength'],
                        'Description': signal['description']
                    })
                
                signals_df = pd.DataFrame(signals_data)
                st.dataframe(signals_df)
            
            if not strong_signals and not other_signals:
                st.info("No clear trading signals at this time.")
        else:
            st.info("No trading signals generated for this cryptocurrency.")
        
        # Display latest prices and indicators
        latest_data = indicators_df.iloc[-1]
        
        st.subheader("Latest Data")
        
        # Create metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Price", f"${latest_data['close']:.2f}")
        
        with col2:
            if 'rsi_14' in latest_data and not pd.isna(latest_data['rsi_14']):
                rsi_value = latest_data['rsi_14']
                rsi_status = None
                
                if rsi_value < 30:
                    rsi_status = "Oversold"
                elif rsi_value > 70:
                    rsi_status = "Overbought"
                
                st.metric("RSI (14)", f"{rsi_value:.2f}", delta=rsi_status, delta_color="off")
            else:
                st.metric("RSI (14)", "N/A")
        
        with col3:
            if 'macd' in latest_data and 'macd_signal' in latest_data and not pd.isna(latest_data['macd']) and not pd.isna(latest_data['macd_signal']):
                macd_status = "Bullish" if latest_data['macd'] > latest_data['macd_signal'] else "Bearish"
                st.metric("MACD", f"{latest_data['macd']:.4f}", delta=macd_status, delta_color="off")
            else:
                st.metric("MACD", "N/A")
        
        with col4:
            if 'trend' in latest_data and not pd.isna(latest_data['trend']):
                st.metric("Trend", latest_data['trend'].capitalize())
            else:
                st.metric("Trend", "N/A")
        
        # Price and indicators charts
        st.subheader("Price Chart with Indicators")
        
        # Select indicators to display
        indicators_options = {
            "SMA 20": "sma_20",
            "SMA 50": "sma_50",
            "SMA 200": "sma_200",
            "EMA 20": "ema_20",
            "EMA 50": "ema_50",
            "Bollinger Bands": "bb_bands",
            "Support/Resistance": "support_resistance"
        }
        
        selected_indicators = st.multiselect(
            "Select Indicators to Display",
            list(indicators_options.keys()),
            default=["SMA 20", "SMA 50"]
        )
        
        # Create candlestick chart
        fig = go.Figure()
        
        # Add candlestick trace
        fig.add_trace(go.Candlestick(
            x=pd.to_datetime(indicators_df['timestamp']),
            open=indicators_df['open'],
            high=indicators_df['high'],
            low=indicators_df['low'],
            close=indicators_df['close'],
            name=selected_symbol
        ))
        
        # Add selected indicators
        for indicator_name in selected_indicators:
            indicator_key = indicators_options[indicator_name]
            
            if indicator_key == "bb_bands" and 'bb_middle' in indicators_df.columns:
                # Add Bollinger Bands
                fig.add_trace(go.Scatter(
                    x=pd.to_datetime(indicators_df['timestamp']),
                    y=indicators_df['bb_middle'],
                    mode='lines',
                    line=dict(color='rgba(100, 100, 100, 0.7)'),
                    name='BB Middle'
                ))
                
                fig.add_trace(go.Scatter(
                    x=pd.to_datetime(indicators_df['timestamp']),
                    y=indicators_df['bb_upper'],
                    mode='lines',
                    line=dict(color='rgba(0, 0, 255, 0.5)'),
                    name='BB Upper'
                ))
                
                fig.add_trace(go.Scatter(
                    x=pd.to_datetime(indicators_df['timestamp']),
                    y=indicators_df['bb_lower'],
                    mode='lines',
                    line=dict(color='rgba(0, 0, 255, 0.5)'),
                    fill='tonexty',
                    fillcolor='rgba(0, 0, 255, 0.1)',
                    name='BB Lower'
                ))
            elif indicator_key == "support_resistance" and 'support' in indicators_df.columns:
                # Add Support/Resistance levels
                fig.add_trace(go.Scatter(
                    x=pd.to_datetime(indicators_df['timestamp']),
                    y=indicators_df['support'],
                    mode='lines',
                    line=dict(color='rgba(0, 255, 0, 0.7)'),
                    name='Support'
                ))
                
                fig.add_trace(go.Scatter(
                    x=pd.to_datetime(indicators_df['timestamp']),
                    y=indicators_df['resistance'],
                    mode='lines',
                    line=dict(color='rgba(255, 0, 0, 0.7)'),
                    name='Resistance'
                ))
            elif indicator_key in indicators_df.columns:
                # Add line indicator
                fig.add_trace(go.Scatter(
                    x=pd.to_datetime(indicators_df['timestamp']),
                    y=indicators_df[indicator_key],
                    mode='lines',
                    name=indicator_name
                ))
        
        # Update layout
        fig.update_layout(
            title=f"{selected_symbol} Price with Technical Indicators",
            xaxis_title="Date",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            height=600
        )
        
        # Show the chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Additional indicator charts
        st.subheader("Technical Indicator Charts")
        
        # RSI Chart
        if 'rsi_14' in indicators_df.columns:
            rsi_fig = go.Figure()
            
            rsi_fig.add_trace(go.Scatter(
                x=pd.to_datetime(indicators_df['timestamp']),
                y=indicators_df['rsi_14'],
                mode='lines',
                name='RSI (14)'
            ))
            
            # Add overbought/oversold lines
            rsi_fig.add_shape(
                type="line",
                x0=pd.to_datetime(indicators_df['timestamp'].iloc[0]),
                y0=70,
                x1=pd.to_datetime(indicators_df['timestamp'].iloc[-1]),
                y1=70,
                line=dict(color="red", width=2, dash="dash"),
            )
            
            rsi_fig.add_shape(
                type="line",
                x0=pd.to_datetime(indicators_df['timestamp'].iloc[0]),
                y0=30,
                x1=pd.to_datetime(indicators_df['timestamp'].iloc[-1]),
                y1=30,
                line=dict(color="green", width=2, dash="dash"),
            )
            
            rsi_fig.update_layout(
                title="Relative Strength Index (RSI)",
                xaxis_title="Date",
                yaxis_title="RSI",
                yaxis=dict(range=[0, 100]),
                height=400
            )
            
            st.plotly_chart(rsi_fig, use_container_width=True)
        
        # MACD Chart
        if all(col in indicators_df.columns for col in ['macd', 'macd_signal', 'macd_histogram']):
            macd_fig = go.Figure()
            
            # Add MACD line
            macd_fig.add_trace(go.Scatter(
                x=pd.to_datetime(indicators_df['timestamp']),
                y=indicators_df['macd'],
                mode='lines',
                name='MACD Line'
            ))
            
            # Add Signal line
            macd_fig.add_trace(go.Scatter(
                x=pd.to_datetime(indicators_df['timestamp']),
                y=indicators_df['macd_signal'],
                mode='lines',
                name='Signal Line'
            ))
            
            # Add Histogram
            macd_fig.add_trace(go.Bar(
                x=pd.to_datetime(indicators_df['timestamp']),
                y=indicators_df['macd_histogram'],
                name='Histogram',
                marker_color=np.where(indicators_df['macd_histogram'] >= 0, 'green', 'red')
            ))
            
            macd_fig.update_layout(
                title="Moving Average Convergence Divergence (MACD)",
                xaxis_title="Date",
                yaxis_title="Value",
                height=400
            )
            
            st.plotly_chart(macd_fig, use_container_width=True)
        
        # Display indicator values in a table
        st.subheader("Indicator Values")
        
        # Select which columns to display
        display_columns = ['timestamp', 'close']
        indicator_columns = [col for col in indicators_df.columns if col not in ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
        
        display_indicators = st.multiselect(
            "Select Indicators to Display in Table",
            indicator_columns,
            default=['rsi_14', 'sma_20', 'sma_50', 'macd', 'macd_signal']
        )
        
        display_columns.extend(display_indicators)
        
        # Display recent indicator values (last 20 rows)
        display_df = indicators_df[display_columns].tail(20).copy()
        
        # Format timestamp
        # Handle different timestamp formats
        if 'timestamp' in display_df.columns:
            if pd.api.types.is_datetime64_any_dtype(display_df['timestamp']):
                display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d')
            elif isinstance(display_df['timestamp'].iloc[0], str):
                display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d')
        
        st.dataframe(display_df)
        
        # Additional technical analysis insights
        st.subheader("Technical Analysis Insights")
        
        # Get latest indicator values
        latest = indicators_df.iloc[-1]
        
        # Moving Average Analysis
        if all(col in latest.index for col in ['sma_20', 'sma_50', 'sma_200']):
            st.write("**Moving Average Analysis:**")
            
            ma_insights = []
            
            if latest['close'] > latest['sma_20']:
                ma_insights.append("✅ Price is above 20-day SMA, indicating short-term uptrend")
            else:
                ma_insights.append("❌ Price is below 20-day SMA, indicating short-term downtrend")
                
            if latest['close'] > latest['sma_50']:
                ma_insights.append("✅ Price is above 50-day SMA, indicating medium-term uptrend")
            else:
                ma_insights.append("❌ Price is below 50-day SMA, indicating medium-term downtrend")
                
            if latest['close'] > latest['sma_200']:
                ma_insights.append("✅ Price is above 200-day SMA, indicating long-term uptrend")
            else:
                ma_insights.append("❌ Price is below 200-day SMA, indicating long-term downtrend")
                
            if latest['sma_20'] > latest['sma_50']:
                ma_insights.append("✅ 20-day SMA is above 50-day SMA (bullish crossover)")
            else:
                ma_insights.append("❌ 20-day SMA is below 50-day SMA (bearish crossover)")
                
            for insight in ma_insights:
                st.write(insight)
        
        # RSI Analysis
        if 'rsi_14' in latest.index:
            st.write("**RSI Analysis:**")
            
            rsi_value = latest['rsi_14']
            
            if rsi_value < 30:
                st.write(f"🔔 RSI is {rsi_value:.2f} - Oversold condition (potential buy signal)")
            elif rsi_value > 70:
                st.write(f"🔔 RSI is {rsi_value:.2f} - Overbought condition (potential sell signal)")
            elif rsi_value >= 40 and rsi_value <= 60:
                st.write(f"ℹ️ RSI is {rsi_value:.2f} - Neutral zone")
            elif rsi_value > 60:
                st.write(f"ℹ️ RSI is {rsi_value:.2f} - Bullish momentum")
            elif rsi_value < 40:
                st.write(f"ℹ️ RSI is {rsi_value:.2f} - Bearish momentum")
        
        # MACD Analysis
        if all(col in latest.index for col in ['macd', 'macd_signal']):
            st.write("**MACD Analysis:**")
            
            if latest['macd'] > latest['macd_signal']:
                st.write("✅ MACD is above Signal Line (bullish)")
                
                # Check if recent crossover
                if len(indicators_df) >= 3:
                    if indicators_df.iloc[-3]['macd'] <= indicators_df.iloc[-3]['macd_signal'] and \
                       indicators_df.iloc[-1]['macd'] > indicators_df.iloc[-1]['macd_signal']:
                        st.write("🔔 Recent MACD bullish crossover detected (strong buy signal)")
            else:
                st.write("❌ MACD is below Signal Line (bearish)")
                
                # Check if recent crossover
                if len(indicators_df) >= 3:
                    if indicators_df.iloc[-3]['macd'] >= indicators_df.iloc[-3]['macd_signal'] and \
                       indicators_df.iloc[-1]['macd'] < indicators_df.iloc[-1]['macd_signal']:
                        st.write("🔔 Recent MACD bearish crossover detected (strong sell signal)")
        
        # Bollinger Bands Analysis
        if all(col in latest.index for col in ['bb_upper', 'bb_lower', 'bb_middle']):
            st.write("**Bollinger Bands Analysis:**")
            
            if latest['close'] > latest['bb_upper']:
                st.write("🔔 Price is above upper Bollinger Band (potential overbought condition)")
            elif latest['close'] < latest['bb_lower']:
                st.write("🔔 Price is below lower Bollinger Band (potential oversold condition)")
            else:
                distance_to_upper = (latest['bb_upper'] - latest['close']) / (latest['bb_upper'] - latest['bb_lower'])
                if distance_to_upper < 0.2:
                    st.write("ℹ️ Price is near upper Bollinger Band (approaching resistance)")
                elif distance_to_upper > 0.8:
                    st.write("ℹ️ Price is near lower Bollinger Band (approaching support)")
                else:
                    st.write("ℹ️ Price is within Bollinger Bands (normal volatility)")
        
        # Support and Resistance Analysis
        if all(col in latest.index for col in ['support', 'resistance']):
            st.write("**Support and Resistance Analysis:**")
            
            distance_to_support = (latest['close'] - latest['support']) / latest['close'] * 100
            distance_to_resistance = (latest['resistance'] - latest['close']) / latest['close'] * 100
            
            st.write(f"ℹ️ Current price is {distance_to_support:.2f}% above support level")
            st.write(f"ℹ️ Current price is {distance_to_resistance:.2f}% below resistance level")
            
            if distance_to_support < 2:
                st.write("🔔 Price is near support level (potential bounce area)")
            elif distance_to_resistance < 2:
                st.write("🔔 Price is near resistance level (potential reversal area)")
        
        # Volume Analysis
        if 'volume' in latest.index:
            st.write("**Volume Analysis:**")
            
            # Calculate average volume over last 20 periods
            avg_volume = indicators_df['volume'].tail(20).mean()
            volume_ratio = latest['volume'] / avg_volume
            
            if volume_ratio > 1.5:
                st.write(f"🔔 Current volume is {volume_ratio:.2f}x higher than average (increased interest)")
            elif volume_ratio < 0.5:
                st.write(f"ℹ️ Current volume is {volume_ratio:.2f}x lower than average (decreased interest)")
            else:
                st.write(f"ℹ️ Current volume is normal ({volume_ratio:.2f}x compared to average)")
    
    except Exception as e:
        logger.error(f"Error displaying technical analysis: {str(e)}", exc_info=True)
        st.error(f"An error occurred while loading the technical analysis: {str(e)}")
