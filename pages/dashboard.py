import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

from data_collection.exchange_data import get_latest_prices
from database.operations import get_db_connection, get_sqlalchemy_engine
from utils.logging_config import get_logger

logger = get_logger(__name__)

def show():
    """Display the main dashboard"""
    st.markdown("""
    <h1 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 1.5rem; 
               background: linear-gradient(to right, #00B0F0, #00D1C4); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Cryptocurrency Analysis Dashboard
    </h1>
    """, unsafe_allow_html=True)
    
    # Introduction message
    st.markdown("""
    <div style="background-color: rgba(0, 176, 240, 0.1); border-left: 4px solid #00B0F0; 
                padding: 0.8rem; border-radius: 0px 8px 8px 0px; margin-bottom: 1.5rem;">
        <p style="margin: 0; padding: 0;">
            This dashboard provides real-time cryptocurrency market analysis with price tracking, 
            sentiment analysis, and technical indicators. Data is collected from multiple exchanges 
            and updated regularly.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Get top cryptocurrencies
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the top cryptocurrencies by recent volume
        cursor.execute("""
            SELECT DISTINCT symbol, 
                   (SELECT MAX(timestamp) FROM ohlcv_data as t2 
                    WHERE t2.symbol = ohlcv_data.symbol) as last_update
            FROM ohlcv_data
            ORDER BY last_update DESC
            LIMIT 20
        """)
        
        top_symbols = [row[0] for row in cursor.fetchall()]
        
        if not top_symbols:
            st.warning("No cryptocurrency data found. Please refresh data to fetch from exchanges.")
            conn.close()
            return
            
        # Get latest prices for these symbols
        latest_prices = get_latest_prices(top_symbols)
        
        # Close the connection
        conn.close()
        
        # Create columns for dashboard layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Market Overview")
            
            # Create a DataFrame for display
            market_data = []
            
            for symbol in top_symbols:
                if symbol in latest_prices:
                    # Extract symbol base (e.g., BTC from BTC/USDT)
                    base_symbol = symbol.split('/')[0] if '/' in symbol else symbol
                    
                    # Get price data
                    price_info = latest_prices[symbol]
                    price = price_info['price']
                    timestamp = price_info['timestamp']
                    
                    # Get 24h change
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # Find price from 24h ago
                    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("""
                        SELECT close FROM ohlcv_data
                        WHERE symbol = %s AND timestamp <= %s
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (symbol, yesterday))
                    
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result:
                        prev_price = result[0]
                        change_24h = ((price - prev_price) / prev_price) * 100
                    else:
                        change_24h = 0
                    
                    market_data.append({
                        'Symbol': base_symbol,
                        'Price (USDT)': price,
                        '24h Change (%)': change_24h,
                        'Last Update': timestamp
                    })
            
            # Create DataFrame and display
            if market_data:
                df = pd.DataFrame(market_data)
                
                # Format the dataframe
                df['Price (USDT)'] = df['Price (USDT)'].map('${:,.2f}'.format)
                df['24h Change (%)'] = df['24h Change (%)'].map('{:+.2f}%'.format)
                
                # Show the table
                st.dataframe(df, use_container_width=True)
                
                # Get sentiment overview
                st.subheader("Market Sentiment")
                
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Get average sentiment for news and social over the past 7 days
                seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                
                cursor.execute("""
                    SELECT AVG(score) FROM sentiment_data
                    WHERE source = 'news' AND date(analyzed_at) >= %s
                """, (seven_days_ago,))
                
                result = cursor.fetchone()
                avg_news_sentiment = result[0] if result and result[0] is not None else 0
                
                cursor.execute("""
                    SELECT AVG(score) FROM sentiment_data
                    WHERE source = 'social' AND date(analyzed_at) >= %s
                """, (seven_days_ago,))
                
                result = cursor.fetchone()
                avg_social_sentiment = result[0] if result and result[0] is not None else 0
                
                # Calculate overall sentiment
                overall_sentiment = (avg_news_sentiment + avg_social_sentiment) / 2
                
                # Create sentiment gauge chart
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = overall_sentiment,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Overall Market Sentiment", 'font': {'color': '#FAFAFA', 'size': 18}},
                    number = {'font': {'color': '#FAFAFA', 'size': 30}},
                    gauge = {
                        'axis': {'range': [-1, 1], 'tickfont': {'color': '#FAFAFA'}},
                        'bar': {'color': "#00B0F0"},
                        'bgcolor': "rgba(255, 255, 255, 0.1)",
                        'borderwidth': 0,
                        'steps': [
                            {'range': [-1, -0.5], 'color': "rgba(255, 77, 77, 0.7)"},
                            {'range': [-0.5, -0.1], 'color': "rgba(255, 153, 153, 0.5)"},
                            {'range': [-0.1, 0.1], 'color': "rgba(180, 180, 180, 0.3)"},
                            {'range': [0.1, 0.5], 'color': "rgba(102, 255, 102, 0.5)"},
                            {'range': [0.5, 1], 'color': "rgba(0, 204, 0, 0.7)"}
                        ],
                    }
                ))
                
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)
                
                # Display sentiment breakdown
                col_news, col_social = st.columns(2)
                
                with col_news:
                    st.metric("News Sentiment", f"{avg_news_sentiment:.2f}", 
                              delta=None,
                              delta_color="normal")
                
                with col_social:
                    st.metric("Social Media Sentiment", f"{avg_social_sentiment:.2f}", 
                              delta=None,
                              delta_color="normal")
            else:
                st.warning("No price data available. Please refresh data.")
        
        with col2:
            st.subheader("Technical Signals")
            
            # Get recent signals
            conn = get_db_connection()
            cursor = conn.cursor()
            
            signals_data = []
            
            for symbol in top_symbols[:5]:  # Limit to top 5 for display
                # Extract base symbol
                base_symbol = symbol.split('/')[0] if '/' in symbol else symbol
                
                # Get technical indicators
                cursor.execute("""
                    SELECT timestamp, rsi_14, macd, macd_signal, trend
                    FROM technical_indicators
                    WHERE symbol = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (symbol,))
                
                result = cursor.fetchone()
                
                if result:
                    timestamp, rsi, macd, macd_signal, trend = result
                    
                    signal = "Neutral"
                    if rsi < 30:
                        signal = "Oversold"
                    elif rsi > 70:
                        signal = "Overbought"
                        
                    if macd > macd_signal:
                        signal = "Bullish" if signal == "Neutral" else signal
                    elif macd < macd_signal:
                        signal = "Bearish" if signal == "Neutral" else signal
                    
                    signals_data.append({
                        'Symbol': base_symbol,
                        'RSI': rsi,
                        'MACD Signal': "Bullish" if macd > macd_signal else "Bearish",
                        'Trend': trend.capitalize() if trend else "Unknown",
                        'Overall': signal
                    })
            
            conn.close()
            
            # Display signals
            if signals_data:
                signals_df = pd.DataFrame(signals_data)
                
                # Format RSI
                signals_df['RSI'] = signals_df['RSI'].map('{:.1f}'.format)
                
                # Show the table
                st.dataframe(signals_df, use_container_width=True)
            else:
                st.warning("No technical indicators available. Please refresh data.")
            
            # Recent News Section
            st.subheader("Recent News")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get recent news with sentiment
            cursor.execute("""
                SELECT n.title, n.published_date, n.link, s.score
                FROM news_data n
                LEFT JOIN sentiment_data s ON CAST(n.id AS TEXT) = s.item_id AND s.source = 'news'
                ORDER BY n.published_date DESC
                LIMIT 5
            """)
            
            news_items = cursor.fetchall()
            conn.close()
            
            # Display news items
            if news_items:
                for item in news_items:
                    title, date, link, sentiment = item
                    
                    # Determine color based on sentiment
                    if sentiment:
                        if sentiment > 0.3:
                            sentiment_label = "📈 Positive"
                            sentiment_color = "green"
                        elif sentiment < -0.3:
                            sentiment_label = "📉 Negative"
                            sentiment_color = "red"
                        else:
                            sentiment_label = "➖ Neutral"
                            sentiment_color = "gray"
                    else:
                        sentiment_label = "❓ Unknown"
                        sentiment_color = "gray"
                    
                    # Format date
                    if isinstance(date, str):
                        try:
                            date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                            formatted_date = date_obj.strftime('%b %d, %Y')
                        except:
                            formatted_date = date
                    else:
                        formatted_date = date.strftime('%b %d, %Y') if hasattr(date, 'strftime') else str(date)
                    
                    # Display news item
                    st.markdown(f"**{title}**")
                    st.markdown(f"<span style='color: {sentiment_color}'>{sentiment_label}</span> · {formatted_date}", unsafe_allow_html=True)
                    st.markdown(f"[Read more]({link})")
                    st.markdown("---")
            else:
                st.warning("No news data available. Please refresh data.")
        
        # Price Chart Section
        st.subheader("Price Charts")
        
        # Create a dropdown for symbol selection
        selected_symbol = st.selectbox("Select cryptocurrency", top_symbols)
        
        # Create time period options
        time_periods = {
            "1D": 1,
            "1W": 7,
            "1M": 30,
            "3M": 90,
            "6M": 180,
            "1Y": 365
        }
        
        selected_period = st.radio("Select time period", list(time_periods.keys()), horizontal=True)
        
        # Get OHLCV data for the selected symbol and period
        days = time_periods[selected_period]
        threshold_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Use SQLAlchemy engine for pandas
        engine = get_sqlalchemy_engine()
        query = """
            SELECT timestamp, open, high, low, close, volume
            FROM ohlcv_data
            WHERE symbol = %s AND date(timestamp) >= %s
            ORDER BY timestamp
        """
        
        import os
        if 'DATABASE_URL' in os.environ:
            # PostgreSQL - Use psycopg2 format with %s placeholders
            df = pd.read_sql_query(query, engine, params=(selected_symbol, threshold_date))
        else:
            # SQLite - Use named parameters
            params = {"symbol": selected_symbol, "date": threshold_date}
            modified_query = query.replace("%s", "?")  # Convert to SQLite placeholders
            df = pd.read_sql_query(modified_query, engine, params=(selected_symbol, threshold_date))
        
        if not df.empty:
            # Convert timestamp if it's a string
            if isinstance(df['timestamp'].iloc[0], str):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Create candlestick chart
            fig = go.Figure(data=[go.Candlestick(
                x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=selected_symbol
            )])
            
            # Get technical indicators if available
            # Use SQLAlchemy engine for pandas
            query = """
                SELECT timestamp, sma_20, sma_50
                FROM technical_indicators
                WHERE symbol = %s AND date(timestamp) >= %s
                ORDER BY timestamp
            """
            
            if 'DATABASE_URL' in os.environ:
                # PostgreSQL - Use psycopg2 format with %s placeholders
                indicators = pd.read_sql_query(query, engine, params=(selected_symbol, threshold_date))
            else:
                # SQLite - Use question mark placeholders
                modified_query = query.replace("%s", "?")
                indicators = pd.read_sql_query(modified_query, engine, params=(selected_symbol, threshold_date))
            
            if not indicators.empty:
                # Convert timestamp if it's a string
                if isinstance(indicators['timestamp'].iloc[0], str):
                    indicators['timestamp'] = pd.to_datetime(indicators['timestamp'])
                
                # Add SMA lines
                fig.add_trace(go.Scatter(
                    x=indicators['timestamp'],
                    y=indicators['sma_20'],
                    mode='lines',
                    name='SMA 20',
                    line=dict(color='rgba(255, 165, 0, 0.7)')
                ))
                
                fig.add_trace(go.Scatter(
                    x=indicators['timestamp'],
                    y=indicators['sma_50'],
                    mode='lines',
                    name='SMA 50',
                    line=dict(color='rgba(255, 0, 255, 0.7)')
                ))
            
            # Update layout
            fig.update_layout(
                title=f"{selected_symbol} Price Chart",
                xaxis_title="Date",
                yaxis_title="Price (USDT)",
                height=500,
                template="plotly_dark",
                font=dict(
                    family="sans-serif",
                    size=14,
                    color="#FAFAFA"
                ),
                plot_bgcolor="rgba(0, 0, 0, 0)",
                paper_bgcolor="rgba(0, 0, 0, 0)",
                margin=dict(t=50, l=40, r=40, b=40),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis=dict(
                    showgrid=True, 
                    gridcolor="rgba(255, 255, 255, 0.1)",
                    zeroline=False
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor="rgba(255, 255, 255, 0.1)",
                    zeroline=False
                ),
                xaxis_rangeslider_visible=False
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Volume Chart
            volume_fig = px.bar(
                df, 
                x='timestamp', 
                y='volume',
                labels={'timestamp': 'Date', 'volume': 'Volume'},
                title=f"{selected_symbol} Volume",
                color_discrete_sequence=["#00B0F0"]
            )
            
            volume_fig.update_layout(
                height=300,
                template="plotly_dark",
                font=dict(
                    family="sans-serif",
                    size=14,
                    color="#FAFAFA"
                ),
                plot_bgcolor="rgba(0, 0, 0, 0)",
                paper_bgcolor="rgba(0, 0, 0, 0)",
                margin=dict(t=50, l=40, r=40, b=40),
                xaxis=dict(
                    showgrid=True, 
                    gridcolor="rgba(255, 255, 255, 0.1)",
                    zeroline=False
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor="rgba(255, 255, 255, 0.1)",
                    zeroline=False
                )
            )
            st.plotly_chart(volume_fig, use_container_width=True)
        else:
            st.warning(f"No price data available for {selected_symbol} in the selected time period.")
        
    except Exception as e:
        logger.error(f"Error displaying dashboard: {str(e)}", exc_info=True)
        st.error(f"An error occurred while loading the dashboard: {str(e)}")
