import os
import pandas as pd
import numpy as np
import datetime
import json
from google.cloud import language_v1
from utils.logging_config import get_logger
from database.operations import get_db_connection

logger = get_logger(__name__)

def initialize_google_nlp():
    """Initialize Google Natural Language API client"""
    try:
        # Check if credentials file is set in environment
        if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
            logger.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
            return None
        
        client = language_v1.LanguageServiceClient()
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Google NLP client: {str(e)}", exc_info=True)
        return None

def analyze_text_sentiment_google(text, client=None):
    """Analyze text sentiment using Google Natural Language API"""
    if not text or len(text.strip()) == 0:
        return {'score': 0, 'magnitude': 0, 'provider': 'google_nlp'}
    
    try:
        if client is None:
            client = initialize_google_nlp()
            
        if client is None:
            return {'score': 0, 'magnitude': 0, 'provider': 'google_nlp'}
            
        document = language_v1.Document(
            content=text,
            type_=language_v1.Document.Type.PLAIN_TEXT
        )
        
        sentiment = client.analyze_sentiment(request={'document': document}).document_sentiment
        
        return {
            'score': sentiment.score,
            'magnitude': sentiment.magnitude,
            'provider': 'google_nlp'
        }
    except Exception as e:
        logger.error(f"Failed to analyze sentiment with Google NLP: {str(e)}", exc_info=True)
        return {'score': 0, 'magnitude': 0, 'provider': 'google_nlp'}

def analyze_text_sentiment_basic(text):
    """Basic sentiment analysis using keyword matching"""
    if not text or len(text.strip()) == 0:
        return {'score': 0, 'magnitude': 0, 'provider': 'basic'}
    
    positive_keywords = [
        'bullish', 'surge', 'soar', 'gain', 'rise', 'rally', 'increase', 'positive', 
        'profit', 'success', 'grow', 'boom', 'advantage', 'potential', 'opportunity',
        'happy', 'good', 'great', 'excellent', 'amazing', 'wonderful', 'best', 'strong',
        'breakthrough', 'innovative', 'progress', 'improvement', 'advance', 'leading'
    ]
    
    negative_keywords = [
        'bearish', 'crash', 'plunge', 'fall', 'drop', 'decline', 'decrease', 'negative',
        'loss', 'failure', 'shrink', 'bust', 'disadvantage', 'risk', 'threat', 'problem',
        'sad', 'bad', 'terrible', 'awful', 'horrible', 'worst', 'weak', 'poor', 'concern',
        'trouble', 'issue', 'fear', 'worry', 'uncertainty', 'doubt', 'volatile', 'bearish'
    ]
    
    text_lower = text.lower()
    
    positive_count = sum(1 for word in positive_keywords if word in text_lower)
    negative_count = sum(1 for word in negative_keywords if word in text_lower)
    
    total_count = positive_count + negative_count
    
    if total_count == 0:
        return {'score': 0, 'magnitude': 0, 'provider': 'basic'}
    
    score = (positive_count - negative_count) / total_count
    magnitude = total_count / 20  # Normalize to 0-1 range, assuming max 20 matches
    
    return {
        'score': min(max(score, -1), 1),  # Constrain to [-1, 1]
        'magnitude': min(magnitude, 1),  # Constrain to [0, 1]
        'provider': 'basic'
    }

def analyze_sentiment(text, provider='basic'):
    """Analyze sentiment for a given text"""
    if provider == 'google_nlp':
        client = initialize_google_nlp()
        if client:
            return analyze_text_sentiment_google(text, client)
        else:
            logger.warning("Falling back to basic sentiment analysis")
            return analyze_text_sentiment_basic(text)
    else:
        return analyze_text_sentiment_basic(text)

def analyze_news_sentiment(days_back=7, limit=100, provider='basic'):
    """Analyze sentiment for recent news articles"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate the date threshold
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        import os
        # Check if content column exists in the news_data table
        if 'DATABASE_URL' in os.environ:
            # PostgreSQL
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'news_data'
            """)
            columns = [column[0] for column in cursor.fetchall()]
        else:
            # SQLite
            cursor.execute("PRAGMA table_info(news_data)")
            columns = [column[1] for column in cursor.fetchall()]
            
        has_content_column = 'content' in columns
        
        # Check if we're using PostgreSQL or SQLite
        if 'DATABASE_URL' in os.environ:
            # PostgreSQL
            # Get news articles that haven't been analyzed yet
            if has_content_column:
                query = """
                    SELECT n.id, n.title, n.description, n.published_date, n.content
                    FROM news_data n
                    LEFT JOIN sentiment_data s ON n.id = s.item_id AND s.source = 'news'
                    WHERE s.id IS NULL AND date(n.published_date) >= %s
                    ORDER BY n.published_date DESC
                    LIMIT %s
                """
            else:
                query = """
                    SELECT n.id, n.title, n.description, n.published_date
                    FROM news_data n
                    LEFT JOIN sentiment_data s ON n.id = s.item_id AND s.source = 'news'
                    WHERE s.id IS NULL AND date(n.published_date) >= %s
                    ORDER BY n.published_date DESC
                    LIMIT %s
                """
        else:
            # SQLite
            # Get news articles that haven't been analyzed yet
            if has_content_column:
                query = """
                    SELECT n.id, n.title, n.description, n.published_date, n.content
                    FROM news_data n
                    LEFT JOIN sentiment_data s ON n.id = s.item_id AND s.source = 'news'
                    WHERE s.id IS NULL AND date(n.published_date) >= ?
                    ORDER BY n.published_date DESC
                    LIMIT ?
                """
            else:
                query = """
                    SELECT n.id, n.title, n.description, n.published_date
                    FROM news_data n
                    LEFT JOIN sentiment_data s ON n.id = s.item_id AND s.source = 'news'
                    WHERE s.id IS NULL AND date(n.published_date) >= ?
                    ORDER BY n.published_date DESC
                    LIMIT ?
                """
        
        cursor.execute(query, (threshold_date, limit))
        news_articles = cursor.fetchall()
        
        if not news_articles:
            logger.info("No new news articles to analyze for sentiment")
            conn.close()
            return 0
            
        client = None
        if provider == 'google_nlp':
            client = initialize_google_nlp()
            if not client:
                provider = 'basic'
                logger.warning("Falling back to basic sentiment analysis for news")
                
        count = 0
        for article in news_articles:
            # Check if we have content column
            if len(article) > 4:
                article_id, title, description, published_date, content = article
                
                # Use full content if available, otherwise fallback to title and description
                if content and len(content.strip()) > 0:
                    logger.info(f"Using full content for sentiment analysis of article: {title}")
                    text = content
                else:
                    text = f"{title} {description}" if description else title
            else:
                article_id, title, description, published_date = article
                # Combine title and description for analysis
                text = f"{title} {description}" if description else title
            
            # Analyze sentiment
            if provider == 'google_nlp' and client:
                sentiment = analyze_text_sentiment_google(text, client)
            else:
                sentiment = analyze_text_sentiment_basic(text)
                
            # Store sentiment results
            import os
            if 'DATABASE_URL' in os.environ:
                # PostgreSQL
                cursor.execute(
                    """
                    INSERT INTO sentiment_data (item_id, source, score, magnitude, provider, analyzed_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        article_id,
                        'news',
                        sentiment['score'],
                        sentiment['magnitude'],
                        sentiment['provider'],
                        datetime.datetime.now()
                    )
                )
            else:
                # SQLite
                cursor.execute(
                    """
                    INSERT INTO sentiment_data (item_id, source, score, magnitude, provider, analyzed_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        article_id,
                        'news',
                        sentiment['score'],
                        sentiment['magnitude'],
                        sentiment['provider'],
                        datetime.datetime.now()
                    )
                )
            count += 1
            
        conn.commit()
        conn.close()
        
        logger.info(f"Analyzed sentiment for {count} news articles")
        return count
    except Exception as e:
        logger.error(f"Failed to analyze news sentiment: {str(e)}", exc_info=True)
        return 0

def analyze_social_sentiment(days_back=3, limit=200, provider='basic'):
    """Analyze sentiment for recent social media posts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate the date threshold
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Get social posts that haven't been analyzed yet
        # Check if we're using PostgreSQL or SQLite
        import os
        if 'DATABASE_URL' in os.environ:
            # PostgreSQL
            query = """
                SELECT s.id, s.text, s.created_at
                FROM social_data s
                LEFT JOIN sentiment_data sd ON s.id = sd.item_id AND sd.source = 'social'
                WHERE sd.id IS NULL AND date(s.created_at) >= %s
                ORDER BY s.created_at DESC
                LIMIT %s
            """
        else:
            # SQLite
            query = """
                SELECT s.id, s.text, s.created_at
                FROM social_data s
                LEFT JOIN sentiment_data sd ON s.id = sd.item_id AND sd.source = 'social'
                WHERE sd.id IS NULL AND date(s.created_at) >= ?
                ORDER BY s.created_at DESC
                LIMIT ?
            """
        
        cursor.execute(query, (threshold_date, limit))
        social_posts = cursor.fetchall()
        
        if not social_posts:
            logger.info("No new social media posts to analyze for sentiment")
            conn.close()
            return 0
            
        client = None
        if provider == 'google_nlp':
            client = initialize_google_nlp()
            if not client:
                provider = 'basic'
                logger.warning("Falling back to basic sentiment analysis for social media")
                
        count = 0
        for post in social_posts:
            post_id, text, created_at = post
            
            # Analyze sentiment
            if provider == 'google_nlp' and client:
                sentiment = analyze_text_sentiment_google(text, client)
            else:
                sentiment = analyze_text_sentiment_basic(text)
                
            # Store sentiment results
            import os
            if 'DATABASE_URL' in os.environ:
                # PostgreSQL
                cursor.execute(
                    """
                    INSERT INTO sentiment_data (item_id, source, score, magnitude, provider, analyzed_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        post_id,
                        'social',
                        sentiment['score'],
                        sentiment['magnitude'],
                        sentiment['provider'],
                        datetime.datetime.now()
                    )
                )
            else:
                # SQLite
                cursor.execute(
                    """
                    INSERT INTO sentiment_data (item_id, source, score, magnitude, provider, analyzed_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        post_id,
                        'social',
                        sentiment['score'],
                        sentiment['magnitude'],
                        sentiment['provider'],
                        datetime.datetime.now()
                    )
                )
            count += 1
            
        conn.commit()
        conn.close()
        
        logger.info(f"Analyzed sentiment for {count} social media posts")
        return count
    except Exception as e:
        logger.error(f"Failed to analyze social sentiment: {str(e)}", exc_info=True)
        return 0

def get_sentiment_trends(days_back=30, interval='day'):
    """Get sentiment trends over time for both news and social media"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate the date threshold
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Define date grouping based on interval
        if interval == 'hour':
            date_group = "strftime('%Y-%m-%d %H', analyzed_at)"
        elif interval == 'day':
            date_group = "date(analyzed_at)"
        elif interval == 'week':
            date_group = "strftime('%Y-%W', analyzed_at)"  # Year-Week format
        elif interval == 'month':
            date_group = "strftime('%Y-%m', analyzed_at)"  # Year-Month format
        else:
            date_group = "date(analyzed_at)"  # Default to day
        
        import os
        # Check if using PostgreSQL
        if 'DATABASE_URL' in os.environ:
            # Get aggregated sentiment for news with PostgreSQL
            query_news = f"""
                SELECT {date_group} as period, 
                       AVG(score) as avg_score, 
                       AVG(magnitude) as avg_magnitude,
                       COUNT(*) as count
                FROM sentiment_data
                WHERE source = 'news' AND date(analyzed_at) >= %s
                GROUP BY period
                ORDER BY period
            """
            
            # Get aggregated sentiment for social media with PostgreSQL
            query_social = f"""
                SELECT {date_group} as period, 
                       AVG(score) as avg_score, 
                       AVG(magnitude) as avg_magnitude,
                       COUNT(*) as count
                FROM sentiment_data
                WHERE source = 'social' AND date(analyzed_at) >= %s
                GROUP BY period
                ORDER BY period
            """
        else:
            # Get aggregated sentiment for news with SQLite
            query_news = f"""
                SELECT {date_group} as period, 
                       AVG(score) as avg_score, 
                       AVG(magnitude) as avg_magnitude,
                       COUNT(*) as count
                FROM sentiment_data
                WHERE source = 'news' AND date(analyzed_at) >= ?
                GROUP BY period
                ORDER BY period
            """
            
            # Get aggregated sentiment for social media with SQLite
            query_social = f"""
                SELECT {date_group} as period, 
                       AVG(score) as avg_score, 
                       AVG(magnitude) as avg_magnitude,
                       COUNT(*) as count
                FROM sentiment_data
                WHERE source = 'social' AND date(analyzed_at) >= ?
                GROUP BY period
                ORDER BY period
            """
        
        cursor.execute(query_news, (threshold_date,))
        news_trends = cursor.fetchall()
        
        cursor.execute(query_social, (threshold_date,))
        social_trends = cursor.fetchall()
        
        conn.close()
        
        # Format results
        news_data = []
        for period, avg_score, avg_magnitude, count in news_trends:
            news_data.append({
                'period': period,
                'avg_score': avg_score,
                'avg_magnitude': avg_magnitude,
                'count': count
            })
            
        social_data = []
        for period, avg_score, avg_magnitude, count in social_trends:
            social_data.append({
                'period': period,
                'avg_score': avg_score,
                'avg_magnitude': avg_magnitude,
                'count': count
            })
            
        return {
            'news': news_data,
            'social': social_data
        }
    except Exception as e:
        logger.error(f"Failed to get sentiment trends: {str(e)}", exc_info=True)
        return {'news': [], 'social': []}

def get_cryptocurrency_sentiment(symbol, days_back=30):
    """Get sentiment specifically for a cryptocurrency by filtering for mentions in text"""
    try:
        # Extract the base symbol (e.g., BTC from BTC/USDT)
        if '/' in symbol:
            base_symbol = symbol.split('/')[0]
        else:
            base_symbol = symbol
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate the date threshold
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        import os
        
        # Check if using PostgreSQL or SQLite
        if 'DATABASE_URL' in os.environ:
            # PostgreSQL
            # Get news sentiment for articles mentioning the cryptocurrency
            query_news = """
                SELECT n.id, n.title, n.published_date, s.score, s.magnitude
                FROM news_data n
                JOIN sentiment_data s ON n.id = s.item_id AND s.source = 'news'
                WHERE (n.title LIKE %s OR n.description LIKE %s) 
                    AND date(n.published_date) >= %s
                ORDER BY n.published_date DESC
            """
            
            # Get social sentiment for posts mentioning the cryptocurrency
            query_social = """
                SELECT s.id, s.text, s.created_at, sd.score, sd.magnitude
                FROM social_data s
                JOIN sentiment_data sd ON s.id = sd.item_id AND sd.source = 'social'
                WHERE (s.text LIKE %s OR s.query = %s) 
                    AND date(s.created_at) >= %s
                ORDER BY s.created_at DESC
            """
        else:
            # SQLite
            # Get news sentiment for articles mentioning the cryptocurrency
            query_news = """
                SELECT n.id, n.title, n.published_date, s.score, s.magnitude
                FROM news_data n
                JOIN sentiment_data s ON n.id = s.item_id AND s.source = 'news'
                WHERE (n.title LIKE ? OR n.description LIKE ?) 
                    AND date(n.published_date) >= ?
                ORDER BY n.published_date DESC
            """
            
            # Get social sentiment for posts mentioning the cryptocurrency
            query_social = """
                SELECT s.id, s.text, s.created_at, sd.score, sd.magnitude
                FROM social_data s
                JOIN sentiment_data sd ON s.id = sd.item_id AND sd.source = 'social'
                WHERE (s.text LIKE ? OR s.query = ?) 
                    AND date(s.created_at) >= ?
                ORDER BY s.created_at DESC
            """
        
        search_pattern = f"%{base_symbol}%"
        
        cursor.execute(query_news, (search_pattern, search_pattern, threshold_date))
        news_items = cursor.fetchall()
        
        cursor.execute(query_social, (search_pattern, base_symbol, threshold_date))
        social_items = cursor.fetchall()
        
        conn.close()
        
        # Process results
        news_data = []
        for item_id, title, date, score, magnitude in news_items:
            news_data.append({
                'id': item_id,
                'title': title,
                'date': date,
                'score': score,
                'magnitude': magnitude
            })
            
        social_data = []
        for item_id, text, date, score, magnitude in social_items:
            social_data.append({
                'id': item_id,
                'text': text,
                'date': date,
                'score': score,
                'magnitude': magnitude
            })
        
        # Calculate average sentiment
        avg_news_sentiment = np.mean([item['score'] for item in news_data]) if news_data else 0
        avg_social_sentiment = np.mean([item['score'] for item in social_data]) if social_data else 0
        
        # Calculate overall sentiment (weighted average)
        total_items = len(news_data) + len(social_data)
        if total_items > 0:
            overall_sentiment = (avg_news_sentiment * len(news_data) + avg_social_sentiment * len(social_data)) / total_items
        else:
            overall_sentiment = 0
            
        return {
            'symbol': symbol,
            'news_count': len(news_data),
            'social_count': len(social_data),
            'avg_news_sentiment': avg_news_sentiment,
            'avg_social_sentiment': avg_social_sentiment,
            'overall_sentiment': overall_sentiment,
            'news_items': news_data[:20],  # Limit the number of items returned
            'social_items': social_data[:20]  # Limit the number of items returned
        }
    except Exception as e:
        logger.error(f"Failed to get cryptocurrency sentiment for {symbol}: {str(e)}", exc_info=True)
        return {
            'symbol': symbol,
            'news_count': 0,
            'social_count': 0,
            'avg_news_sentiment': 0,
            'avg_social_sentiment': 0,
            'overall_sentiment': 0,
            'news_items': [],
            'social_items': []
        }

def run_sentiment_analysis(config):
    """Run sentiment analysis for both news and social media"""
    try:
        if not config.getboolean('SENTIMENT', 'Enabled'):
            logger.info("Sentiment analysis is disabled in config")
            return
            
        provider = config['SENTIMENT']['Provider']
        
        # Analyze news sentiment
        news_count = analyze_news_sentiment(provider=provider)
        
        # Analyze social sentiment
        social_count = analyze_social_sentiment(provider=provider)
        
        logger.info(f"Sentiment analysis completed: analyzed {news_count} news articles and {social_count} social posts")
    except Exception as e:
        logger.error(f"Failed to run sentiment analysis: {str(e)}", exc_info=True)
