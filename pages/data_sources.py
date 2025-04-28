import streamlit as st
import pandas as pd
import datetime
import uuid
import json
from database.operations import get_db_connection
from data_collection.custom_sources import (
    get_custom_sources, save_custom_source, delete_custom_source,
    ApiDataSource, CsvDataSource, update_custom_source_data
)
from data_collection.exchange_data import update_exchange_data
from data_collection.news_data import update_news_data
from data_collection.social_data import update_social_data
import os
from utils.logging_config import get_logger

logger = get_logger(__name__)

def show():
    """Display the data sources management page"""
    st.markdown("""
    <h1 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 1.5rem; 
               background: linear-gradient(to right, #00B0F0, #00D1C4); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Data Sources Management
    </h1>
    """, unsafe_allow_html=True)
    
    # Introduction message
    st.markdown("""
    <div style="background-color: rgba(0, 176, 240, 0.1); border-left: 4px solid #00B0F0; 
                padding: 0.8rem; border-radius: 0px 8px 8px 0px; margin-bottom: 1.5rem;">
        <p style="margin: 0; padding: 0;">
            Configure and manage data sources for your cryptocurrency analysis. Add custom data sources, 
            update existing sources, and monitor data collection status across exchanges, news, and social media.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different sections
    tabs = st.tabs(["Exchanges", "News", "Social Media", "Custom Sources"])
    
    # Exchanges tab
    with tabs[0]:
        show_exchange_sources()
    
    # News tab
    with tabs[1]:
        show_news_sources()
    
    # Social Media tab
    with tabs[2]:
        show_social_sources()
    
    # Custom Sources tab
    with tabs[3]:
        show_custom_sources()

def show_exchange_sources():
    """Display exchange data sources"""
    st.markdown("""
    <h2 style="font-weight: 600; color: #00B0F0; margin-bottom: 1rem;">
        Cryptocurrency Exchanges
    </h2>
    """, unsafe_allow_html=True)
    
    try:
        # Load current exchange configuration
        import configparser
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        # Display current exchanges
        exchanges = config['EXCHANGES']['Exchanges'].split(',')
        exchanges = [e.strip() for e in exchanges]
        
        st.write(f"Currently configured exchanges: **{', '.join(exchanges)}**")
        
        # Display the status of exchange data
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the number of symbols and data points
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM ohlcv_data")
        symbol_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ohlcv_data")
        data_count = cursor.fetchone()[0]
        
        # Get the most recent data timestamp
        cursor.execute("SELECT MAX(timestamp) FROM ohlcv_data")
        latest_timestamp = cursor.fetchone()[0]
        
        # Get top symbols by data count
        cursor.execute("""
            SELECT symbol, COUNT(*) as count
            FROM ohlcv_data
            GROUP BY symbol
            ORDER BY count DESC
            LIMIT 10
        """)
        
        top_symbols = cursor.fetchall()
        conn.close()
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Symbols", symbol_count)
        
        with col2:
            st.metric("Total Data Points", data_count)
        
        with col3:
            if latest_timestamp:
                # Format the timestamp
                if isinstance(latest_timestamp, str):
                    latest_timestamp = datetime.datetime.strptime(latest_timestamp, '%Y-%m-%d %H:%M:%S')
                
                time_diff = datetime.datetime.now() - latest_timestamp
                hours_ago = time_diff.total_seconds() / 3600
                
                if hours_ago < 24:
                    status = "✅ Recent"
                elif hours_ago < 48:
                    status = "⚠️ Yesterday"
                else:
                    status = "❌ Outdated"
                
                st.metric("Latest Data", f"{latest_timestamp.strftime('%Y-%m-%d')}", 
                          delta=status, delta_color="off")
            else:
                st.metric("Latest Data", "No data")
        
        # Display top symbols
        if top_symbols:
            st.subheader("Top Cryptocurrencies by Data Points")
            
            # Prepare data for the chart
            symbol_data = {
                'Symbol': [s[0] for s in top_symbols],
                'Data Points': [s[1] for s in top_symbols]
            }
            
            df = pd.DataFrame(symbol_data)
            st.bar_chart(df.set_index('Symbol'))
        
        # Manual update section
        st.subheader("Update Exchange Data")
        
        if st.button("Update Data from Exchanges"):
            with st.spinner("Fetching data from exchanges..."):
                try:
                    update_exchange_data(config)
                    st.success("Exchange data updated successfully!")
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error updating exchange data: {str(e)}", exc_info=True)
                    st.error(f"Error updating exchange data: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error displaying exchange sources: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")

def show_news_sources():
    """Display news data sources"""
    st.markdown("""
    <h2 style="font-weight: 600; color: #00B0F0; margin-bottom: 1rem;">
        News Sources
    </h2>
    """, unsafe_allow_html=True)
    
    try:
        # Load current news configuration
        import configparser
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        # Display current news sources
        news_sources = config['NEWS']['Sources'].split(',')
        news_sources = [s.strip() for s in news_sources]
        
        st.write("Currently configured news sources:")
        for source in news_sources:
            st.write(f"- {source}")
        
        # Display the status of news data
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the number of news articles
        cursor.execute("SELECT COUNT(*) FROM news_data")
        news_count = cursor.fetchone()[0]
        
        # Get the most recent news timestamp
        cursor.execute("SELECT MAX(published_date) FROM news_data")
        latest_timestamp = cursor.fetchone()[0]
        
        # Get news sources distribution
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM news_data
            GROUP BY source
            ORDER BY count DESC
        """)
        
        sources_distribution = cursor.fetchall()
        
        # Get recent news
        cursor.execute("""
            SELECT title, published_date, source
            FROM news_data
            ORDER BY published_date DESC
            LIMIT 5
        """)
        
        recent_news = cursor.fetchall()
        conn.close()
        
        # Display statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total News Articles", news_count)
        
        with col2:
            if latest_timestamp:
                # Format the timestamp
                if isinstance(latest_timestamp, str):
                    latest_timestamp = datetime.datetime.strptime(latest_timestamp, '%Y-%m-%d %H:%M:%S')
                
                time_diff = datetime.datetime.now() - latest_timestamp
                hours_ago = time_diff.total_seconds() / 3600
                
                if hours_ago < 24:
                    status = "✅ Today"
                elif hours_ago < 48:
                    status = "⚠️ Yesterday"
                else:
                    status = "⚠️ " + latest_timestamp.strftime('%Y-%m-%d')
                
                st.metric("Latest Article", status)
            else:
                st.metric("Latest Article", "No data")
        
        # Display sources distribution
        if sources_distribution:
            st.subheader("News Sources Distribution")
            
            # Prepare data for the chart
            source_data = {
                'Source': [s[0] for s in sources_distribution],
                'Articles': [s[1] for s in sources_distribution]
            }
            
            source_df = pd.DataFrame(source_data)
            st.bar_chart(source_df.set_index('Source'))
        
        # Display recent news
        if recent_news:
            st.subheader("Recent News Articles")
            
            for title, date, source in recent_news:
                # Format the date
                if isinstance(date, str):
                    date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                formatted_date = date.strftime('%Y-%m-%d %H:%M')
                
                st.write(f"**{title}**")
                st.write(f"Source: {source} | Date: {formatted_date}")
                st.write("---")
        
        # Manual update section
        st.subheader("Update News Data")
        
        if st.button("Update News Data"):
            with st.spinner("Fetching news data..."):
                try:
                    update_news_data(config)
                    st.success("News data updated successfully!")
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error updating news data: {str(e)}", exc_info=True)
                    st.error(f"Error updating news data: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error displaying news sources: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")

def show_social_sources():
    """Display social media data sources"""
    st.markdown("""
    <h2 style="font-weight: 600; color: #00B0F0; margin-bottom: 1rem;">
        Social Media Sources
    </h2>
    """, unsafe_allow_html=True)
    
    try:
        # Load current social media configuration
        import configparser
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        # Display current platforms
        platforms = config['SOCIAL']['Platforms'].split(',')
        platforms = [p.strip() for p in platforms]
        
        st.write(f"Currently configured platforms: **{', '.join(platforms)}**")
        
        # Check Twitter API credentials
        twitter_api_configured = bool(
            "TWITTER_BEARER_TOKEN" in os.environ and os.environ["TWITTER_BEARER_TOKEN"]
        )
        
        if 'twitter' in platforms and not twitter_api_configured:
            st.warning("⚠️ Twitter API credentials are not properly configured. Please set the environment variables.")
        
        # Display the status of social media data
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the number of social posts
        cursor.execute("SELECT COUNT(*) FROM social_data")
        posts_count = cursor.fetchone()[0]
        
        # Get the most recent post timestamp
        cursor.execute("SELECT MAX(created_at) FROM social_data")
        latest_timestamp = cursor.fetchone()[0]
        
        # Get platform distribution
        cursor.execute("""
            SELECT platform, COUNT(*) as count
            FROM social_data
            GROUP BY platform
            ORDER BY count DESC
        """)
        
        platform_distribution = cursor.fetchall()
        
        # Get top queries
        cursor.execute("""
            SELECT query, COUNT(*) as count
            FROM social_data
            GROUP BY query
            ORDER BY count DESC
            LIMIT 10
        """)
        
        top_queries = cursor.fetchall()
        
        # Get recent posts
        cursor.execute("""
            SELECT text, created_at, platform, query
            FROM social_data
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        recent_posts = cursor.fetchall()
        conn.close()
        
        # Display statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Social Posts", posts_count)
        
        with col2:
            if latest_timestamp:
                # Format the timestamp
                if isinstance(latest_timestamp, str):
                    latest_timestamp = datetime.datetime.strptime(latest_timestamp, '%Y-%m-%d %H:%M:%S')
                
                time_diff = datetime.datetime.now() - latest_timestamp
                hours_ago = time_diff.total_seconds() / 3600
                
                if hours_ago < 24:
                    status = "✅ Today"
                elif hours_ago < 48:
                    status = "⚠️ Yesterday"
                else:
                    status = "⚠️ " + latest_timestamp.strftime('%Y-%m-%d')
                
                st.metric("Latest Post", status)
            else:
                st.metric("Latest Post", "No data")
        
        # Display platform distribution
        if platform_distribution:
            st.subheader("Platform Distribution")
            
            # Prepare data for the chart
            platform_data = {
                'Platform': [p[0] for p in platform_distribution],
                'Posts': [p[1] for p in platform_distribution]
            }
            
            platform_df = pd.DataFrame(platform_data)
            st.bar_chart(platform_df.set_index('Platform'))
        
        # Display top queries
        if top_queries:
            st.subheader("Top Search Queries")
            
            # Prepare data for the chart
            query_data = {
                'Query': [q[0] for q in top_queries],
                'Posts': [q[1] for q in top_queries]
            }
            
            query_df = pd.DataFrame(query_data)
            st.bar_chart(query_df.set_index('Query'))
        
        # Display recent posts
        if recent_posts:
            st.subheader("Recent Social Media Posts")
            
            for text, date, platform, query in recent_posts:
                # Format the date
                if isinstance(date, str):
                    date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                formatted_date = date.strftime('%Y-%m-%d %H:%M')
                
                st.write(f"**{text[:100]}{'...' if len(text) > 100 else ''}**")
                st.write(f"Platform: {platform} | Query: {query} | Date: {formatted_date}")
                st.write("---")
        
        # Manual update section
        st.subheader("Update Social Media Data")
        
        if st.button("Update Social Media Data"):
            with st.spinner("Fetching social media data..."):
                try:
                    update_social_data(config)
                    st.success("Social media data updated successfully!")
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error updating social media data: {str(e)}", exc_info=True)
                    st.error(f"Error updating social media data: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error displaying social media sources: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")

def show_custom_sources():
    """Display and manage custom data sources"""
    st.markdown("""
    <h2 style="font-weight: 600; color: #00B0F0; margin-bottom: 1rem;">
        Custom Data Sources
    </h2>
    """, unsafe_allow_html=True)
    
    try:
        # Get existing custom sources
        custom_sources = get_custom_sources()
        
        # Display existing sources
        if custom_sources:
            st.subheader("Existing Custom Sources")
            
            for i, source in enumerate(custom_sources):
                with st.expander(f"{source.name} ({source.source_type})"):
                    st.write(f"**Description:** {source.description}")
                    st.write(f"**Type:** {source.source_type}")
                    st.write(f"**Status:** {'Enabled' if source.enabled else 'Disabled'}")
                    
                    # Show source configuration
                    with st.expander("Source Configuration"):
                        st.code(json.dumps(source.config, indent=2))
                    
                    # Show latest data
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT data, collected_at FROM custom_data
                        WHERE source_id = ?
                        ORDER BY collected_at DESC
                        LIMIT 1
                    """, (source.source_id,))
                    
                    latest_data = cursor.fetchone()
                    conn.close()
                    
                    if latest_data:
                        data, collected_at = latest_data
                        
                        with st.expander("Latest Data"):
                            # Format the date
                            if isinstance(collected_at, str):
                                collected_at = datetime.datetime.strptime(collected_at, '%Y-%m-%d %H:%M:%S')
                            formatted_date = collected_at.strftime('%Y-%m-%d %H:%M:%S')
                            
                            st.write(f"**Collected at:** {formatted_date}")
                            
                            try:
                                # Try to parse as JSON
                                json_data = json.loads(data)
                                st.json(json_data)
                            except:
                                # Display as text
                                st.text(data[:1000] + "..." if len(data) > 1000 else data)
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button(f"Update Data", key=f"update_{source.source_id}"):
                            with st.spinner(f"Fetching data from {source.name}..."):
                                try:
                                    # Fetch raw data
                                    raw_data = source.fetch_data()
                                    
                                    # Process the data
                                    processed_data = source.process_data(raw_data)
                                    
                                    # Store the data
                                    source.store_data(processed_data)
                                    
                                    st.success(f"Data from {source.name} updated successfully!")
                                except Exception as e:
                                    logger.error(f"Error updating data from {source.name}: {str(e)}", exc_info=True)
                                    st.error(f"Error updating data: {str(e)}")
                    
                    with col2:
                        if st.button(f"Toggle Status", key=f"toggle_{source.source_id}"):
                            source.enabled = not source.enabled
                            if save_custom_source(source):
                                st.success(f"Source {source.name} {'enabled' if source.enabled else 'disabled'}")
                                st.rerun()
                    
                    with col3:
                        if st.button(f"Delete Source", key=f"delete_{source.source_id}"):
                            if delete_custom_source(source.source_id):
                                st.success(f"Source {source.name} deleted successfully")
                                st.rerun()
        else:
            st.info("No custom data sources configured yet.")
        
        # Add new source form
        st.subheader("Add New Custom Source")
        
        source_type = st.selectbox("Source Type", ["API", "CSV"])
        
        with st.form("new_source_form"):
            name = st.text_input("Source Name")
            description = st.text_area("Description")
            
            if source_type == "API":
                url = st.text_input("API URL")
                method = st.selectbox("HTTP Method", ["GET", "POST"])
                
                with st.expander("Headers (optional)"):
                    headers_str = st.text_area("Headers (JSON format)", "{}")
                
                with st.expander("Parameters (optional)"):
                    params_str = st.text_area("Parameters (JSON format)", "{}")
            
            elif source_type == "CSV":
                location = st.text_input("CSV URL or File Path")
                delimiter = st.text_input("Delimiter", ",")
                has_header = st.checkbox("Has Header", True)
                encoding = st.text_input("Encoding", "utf-8")
            
            submit_button = st.form_submit_button("Add Source")
            
            if submit_button:
                try:
                    source_id = str(uuid.uuid4())
                    
                    if not name:
                        st.error("Source name is required")
                    elif source_type == "API" and not url:
                        st.error("API URL is required")
                    elif source_type == "CSV" and not location:
                        st.error("CSV location is required")
                    else:
                        if source_type == "API":
                            try:
                                headers = json.loads(headers_str) if headers_str else {}
                                params = json.loads(params_str) if params_str else {}
                            except json.JSONDecodeError:
                                st.error("Headers or parameters are not valid JSON")
                                return
                            
                            source = ApiDataSource(
                                source_id=source_id,
                                name=name,
                                description=description,
                                url=url,
                                headers=headers,
                                params=params,
                                method=method
                            )
                        elif source_type == "CSV":
                            source = CsvDataSource(
                                source_id=source_id,
                                name=name,
                                description=description,
                                location=location,
                                delimiter=delimiter,
                                has_header=has_header,
                                encoding=encoding
                            )
                        
                        if save_custom_source(source):
                            st.success(f"Custom source {name} added successfully")
                            st.rerun()
                        else:
                            st.error("Failed to add custom source")
                except Exception as e:
                    logger.error(f"Error adding custom source: {str(e)}", exc_info=True)
                    st.error(f"An error occurred: {str(e)}")
        
        # Update all custom sources
        st.subheader("Update All Custom Sources")
        
        if st.button("Update All Custom Sources"):
            with st.spinner("Updating all custom sources..."):
                try:
                    update_custom_source_data()
                    st.success("All custom sources updated successfully!")
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error updating custom sources: {str(e)}", exc_info=True)
                    st.error(f"Error updating custom sources: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error displaying custom sources: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
