import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

from database.operations import get_db_connection
from analysis.sentiment_analysis import (
    get_sentiment_trends, get_cryptocurrency_sentiment, 
    analyze_news_sentiment, analyze_social_sentiment, run_sentiment_analysis
)
from utils.logging_config import get_logger

logger = get_logger(__name__)

def show():
    """Display the sentiment analysis page"""
    st.title("Sentiment Analysis")
    
    try:
        # Sidebar for options
        st.sidebar.header("Sentiment Options")
        
        # Get sentiment provider from config
        import configparser
        config = configparser.ConfigParser()
        config.read('config.ini')
        provider = config['SENTIMENT']['Provider']
        
        provider_name = "Google NLP" if provider == "google_nlp" else "Basic"
        st.sidebar.write(f"Current sentiment provider: **{provider_name}**")
        
        # Button to run sentiment analysis manually
        if st.sidebar.button("Run Sentiment Analysis"):
            with st.spinner("Analyzing sentiment data..."):
                try:
                    run_sentiment_analysis(config)
                    st.sidebar.success("Sentiment analysis completed successfully!")
                except Exception as e:
                    logger.error(f"Error running sentiment analysis: {str(e)}", exc_info=True)
                    st.sidebar.error(f"Error: {str(e)}")
        
        # Display sentiment trends
        st.header("Overall Sentiment Trends")
        
        # Time period selection
        time_periods = {
            "1 Week": 7,
            "1 Month": 30,
            "3 Months": 90
        }
        
        selected_period = st.radio("Select time period", list(time_periods.keys()), horizontal=True)
        days_back = time_periods[selected_period]
        
        # Get sentiment trends
        trends = get_sentiment_trends(days_back=days_back, interval='day')
        
        if not trends['news'] and not trends['social']:
            st.warning("No sentiment data available. Please run sentiment analysis first.")
        else:
            # Create trend chart
            fig = go.Figure()
            
            # Add news sentiment line
            if trends['news']:
                news_df = pd.DataFrame(trends['news'])
                fig.add_trace(go.Scatter(
                    x=news_df['period'],
                    y=news_df['avg_score'],
                    mode='lines+markers',
                    name='News Sentiment',
                    line=dict(color='blue')
                ))
            
            # Add social sentiment line
            if trends['social']:
                social_df = pd.DataFrame(trends['social'])
                fig.add_trace(go.Scatter(
                    x=social_df['period'],
                    y=social_df['avg_score'],
                    mode='lines+markers',
                    name='Social Media Sentiment',
                    line=dict(color='green')
                ))
            
            # Add neutral line
            if trends['news'] or trends['social']:
                x_values = news_df['period'] if trends['news'] else social_df['period']
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=[0] * len(x_values),
                    mode='lines',
                    name='Neutral Line',
                    line=dict(color='gray', dash='dash')
                ))
            
            # Update layout
            fig.update_layout(
                title="Sentiment Trends Over Time",
                xaxis_title="Date",
                yaxis_title="Sentiment Score (-1 to 1)",
                yaxis=dict(range=[-1, 1]),
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display additional insights
            if trends['news'] or trends['social']:
                # Calculate average sentiment
                if trends['news']:
                    avg_news_sentiment = np.mean([item['avg_score'] for item in trends['news']])
                    latest_news_sentiment = trends['news'][-1]['avg_score']
                else:
                    avg_news_sentiment = 0
                    latest_news_sentiment = 0
                
                if trends['social']:
                    avg_social_sentiment = np.mean([item['avg_score'] for item in trends['social']])
                    latest_social_sentiment = trends['social'][-1]['avg_score']
                else:
                    avg_social_sentiment = 0
                    latest_social_sentiment = 0
                
                # Display metrics
                col1, col2 = st.columns(2)
                
                with col1:
                    news_delta = latest_news_sentiment - avg_news_sentiment if trends['news'] else None
                    st.metric(
                        "Latest News Sentiment", 
                        f"{latest_news_sentiment:.2f}" if trends['news'] else "N/A",
                        delta=f"{news_delta:.2f}" if news_delta is not None else None
                    )
                
                with col2:
                    social_delta = latest_social_sentiment - avg_social_sentiment if trends['social'] else None
                    st.metric(
                        "Latest Social Sentiment", 
                        f"{latest_social_sentiment:.2f}" if trends['social'] else "N/A",
                        delta=f"{social_delta:.2f}" if social_delta is not None else None
                    )
                
                # Sentiment volume/count
                if trends['news'] or trends['social']:
                    st.subheader("Sentiment Data Volume")
                    
                    volume_data = []
                    for period_data in (trends['news'] if trends['news'] else trends['social']):
                        date = period_data['period']
                        news_count = next((item['count'] for item in trends['news'] if item['period'] == date), 0) if trends['news'] else 0
                        social_count = next((item['count'] for item in trends['social'] if item['period'] == date), 0) if trends['social'] else 0
                        
                        volume_data.append({
                            'date': date,
                            'News': news_count,
                            'Social': social_count
                        })
                    
                    volume_df = pd.DataFrame(volume_data)
                    volume_fig = px.bar(
                        volume_df, 
                        x='date', 
                        y=['News', 'Social'],
                        title="Data Volume by Source",
                        labels={'date': 'Date', 'value': 'Count', 'variable': 'Source'}
                    )
                    
                    st.plotly_chart(volume_fig, use_container_width=True)
        
        # Cryptocurrency-specific sentiment
        st.header("Cryptocurrency-Specific Sentiment")
        
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
            st.warning("No cryptocurrency data found.")
        else:
            # Cryptocurrency selection
            selected_crypto = st.selectbox("Select cryptocurrency", available_symbols)
            
            # Get sentiment for selected cryptocurrency
            crypto_sentiment = get_cryptocurrency_sentiment(selected_crypto, days_back=days_back)
            
            if crypto_sentiment['news_count'] == 0 and crypto_sentiment['social_count'] == 0:
                st.warning(f"No sentiment data available for {selected_crypto}. Please run sentiment analysis first.")
            else:
                # Display sentiment metrics
                st.subheader(f"Sentiment Analysis for {selected_crypto}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Overall sentiment
                    sentiment_value = crypto_sentiment['overall_sentiment']
                    sentiment_label = "Positive" if sentiment_value > 0.3 else "Negative" if sentiment_value < -0.3 else "Neutral"
                    sentiment_color = "green" if sentiment_value > 0.3 else "red" if sentiment_value < -0.3 else "gray"
                    
                    st.metric(
                        "Overall Sentiment", 
                        f"{sentiment_value:.2f}", 
                        delta=sentiment_label,
                        delta_color="normal"
                    )
                
                with col2:
                    # News sentiment
                    news_sentiment = crypto_sentiment['avg_news_sentiment']
                    st.metric(
                        "News Sentiment", 
                        f"{news_sentiment:.2f}" if crypto_sentiment['news_count'] > 0 else "N/A",
                        delta=f"Based on {crypto_sentiment['news_count']} articles",
                        delta_color="off"
                    )
                
                with col3:
                    # Social sentiment
                    social_sentiment = crypto_sentiment['avg_social_sentiment']
                    st.metric(
                        "Social Sentiment", 
                        f"{social_sentiment:.2f}" if crypto_sentiment['social_count'] > 0 else "N/A",
                        delta=f"Based on {crypto_sentiment['social_count']} posts",
                        delta_color="off"
                    )
                
                # Create sentiment gauge chart
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = sentiment_value,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': f"Overall {selected_crypto} Sentiment"},
                    gauge = {
                        'axis': {'range': [-1, 1]},
                        'bar': {'color': sentiment_color},
                        'steps': [
                            {'range': [-1, -0.5], 'color': "red"},
                            {'range': [-0.5, -0.1], 'color': "salmon"},
                            {'range': [-0.1, 0.1], 'color': "lightgray"},
                            {'range': [0.1, 0.5], 'color': "lightgreen"},
                            {'range': [0.5, 1], 'color': "green"}
                        ],
                    }
                ))
                
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
                
                # Display news and social posts with sentiment
                if crypto_sentiment['news_items']:
                    st.subheader("News Articles")
                    
                    for item in crypto_sentiment['news_items']:
                        # Determine sentiment color
                        if item['score'] > 0.3:
                            sentiment_label = "📈 Positive"
                            sentiment_color = "green"
                        elif item['score'] < -0.3:
                            sentiment_label = "📉 Negative"
                            sentiment_color = "red"
                        else:
                            sentiment_label = "➖ Neutral"
                            sentiment_color = "gray"
                        
                        # Format date
                        if isinstance(item['date'], str):
                            try:
                                date_obj = datetime.strptime(item['date'], '%Y-%m-%d %H:%M:%S')
                                formatted_date = date_obj.strftime('%b %d, %Y')
                            except:
                                formatted_date = item['date']
                        else:
                            formatted_date = item['date'].strftime('%b %d, %Y') if hasattr(item['date'], 'strftime') else str(item['date'])
                        
                        # Display news item
                        st.markdown(f"**{item['title']}**")
                        st.markdown(f"<span style='color: {sentiment_color}'>{sentiment_label} ({item['score']:.2f})</span> · {formatted_date}", unsafe_allow_html=True)
                        st.markdown("---")
                
                if crypto_sentiment['social_items']:
                    st.subheader("Social Media Posts")
                    
                    for item in crypto_sentiment['social_items']:
                        # Determine sentiment color
                        if item['score'] > 0.3:
                            sentiment_label = "📈 Positive"
                            sentiment_color = "green"
                        elif item['score'] < -0.3:
                            sentiment_label = "📉 Negative"
                            sentiment_color = "red"
                        else:
                            sentiment_label = "➖ Neutral"
                            sentiment_color = "gray"
                        
                        # Format date
                        if isinstance(item['date'], str):
                            try:
                                date_obj = datetime.strptime(item['date'], '%Y-%m-%d %H:%M:%S')
                                formatted_date = date_obj.strftime('%b %d, %Y')
                            except:
                                formatted_date = item['date']
                        else:
                            formatted_date = item['date'].strftime('%b %d, %Y') if hasattr(item['date'], 'strftime') else str(item['date'])
                        
                        # Display social post
                        st.markdown(f"**{item['text'][:100]}{'...' if len(item['text']) > 100 else ''}**")
                        st.markdown(f"<span style='color: {sentiment_color}'>{sentiment_label} ({item['score']:.2f})</span> · {formatted_date}", unsafe_allow_html=True)
                        st.markdown("---")
        
        # Latest Analyzed Content
        st.header("Latest Analyzed Content")
        
        # Get latest sentiment data
        conn = get_db_connection()
        
        # Get latest news with sentiment
        news_query = """
            SELECT n.title, n.published_date, n.link, s.score, s.magnitude, s.analyzed_at
            FROM news_data n
            JOIN sentiment_data s ON CAST(n.id AS TEXT) = s.item_id AND s.source = 'news'
            ORDER BY s.analyzed_at DESC
            LIMIT 10
        """
        
        news_df = pd.read_sql_query(news_query, conn)
        
        # Get latest social posts with sentiment
        social_query = """
            SELECT s.text, s.created_at, s.platform, sd.score, sd.magnitude, sd.analyzed_at
            FROM social_data s
            JOIN sentiment_data sd ON s.id = sd.item_id AND sd.source = 'social'
            ORDER BY sd.analyzed_at DESC
            LIMIT 10
        """
        
        social_df = pd.read_sql_query(social_query, conn)
        conn.close()
        
        # Create tabs for news and social
        news_tab, social_tab = st.tabs(["News Sentiment", "Social Media Sentiment"])
        
        with news_tab:
            if news_df.empty:
                st.info("No analyzed news articles available.")
            else:
                for _, row in news_df.iterrows():
                    # Determine sentiment color
                    if row['score'] > 0.3:
                        sentiment_label = "📈 Positive"
                        sentiment_color = "green"
                    elif row['score'] < -0.3:
                        sentiment_label = "📉 Negative"
                        sentiment_color = "red"
                    else:
                        sentiment_label = "➖ Neutral"
                        sentiment_color = "gray"
                    
                    # Format date
                    if isinstance(row['published_date'], str):
                        try:
                            date_obj = datetime.strptime(row['published_date'], '%Y-%m-%d %H:%M:%S')
                            formatted_date = date_obj.strftime('%b %d, %Y')
                        except:
                            formatted_date = row['published_date']
                    else:
                        formatted_date = row['published_date'].strftime('%b %d, %Y') if hasattr(row['published_date'], 'strftime') else str(row['published_date'])
                    
                    # Display news item
                    st.markdown(f"**{row['title']}**")
                    st.markdown(
                        f"<span style='color: {sentiment_color}'>{sentiment_label} (Score: {row['score']:.2f}, Magnitude: {row['magnitude']:.2f})</span> · {formatted_date}", 
                        unsafe_allow_html=True
                    )
                    if row['link']:
                        st.markdown(f"[Read more]({row['link']})")
                    st.markdown("---")
        
        with social_tab:
            if social_df.empty:
                st.info("No analyzed social media posts available.")
            else:
                for _, row in social_df.iterrows():
                    # Determine sentiment color
                    if row['score'] > 0.3:
                        sentiment_label = "📈 Positive"
                        sentiment_color = "green"
                    elif row['score'] < -0.3:
                        sentiment_label = "📉 Negative"
                        sentiment_color = "red"
                    else:
                        sentiment_label = "➖ Neutral"
                        sentiment_color = "gray"
                    
                    # Format date
                    if isinstance(row['created_at'], str):
                        try:
                            date_obj = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
                            formatted_date = date_obj.strftime('%b %d, %Y')
                        except:
                            formatted_date = row['created_at']
                    else:
                        formatted_date = row['created_at'].strftime('%b %d, %Y') if hasattr(row['created_at'], 'strftime') else str(row['created_at'])
                    
                    # Display social post
                    st.markdown(f"**{row['text'][:100]}{'...' if len(row['text']) > 100 else ''}**")
                    st.markdown(
                        f"<span style='color: {sentiment_color}'>{sentiment_label} (Score: {row['score']:.2f}, Magnitude: {row['magnitude']:.2f})</span> · {formatted_date} · {row['platform']}", 
                        unsafe_allow_html=True
                    )
                    st.markdown("---")
    
    except Exception as e:
        logger.error(f"Error displaying sentiment analysis: {str(e)}", exc_info=True)
        st.error(f"An error occurred while loading the sentiment analysis: {str(e)}")
