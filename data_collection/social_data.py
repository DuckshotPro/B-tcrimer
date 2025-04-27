import tweepy
import pandas as pd
import datetime
import time
import re
from utils.logging_config import get_logger
from database.operations import get_db_connection
import os

logger = get_logger(__name__)

def get_twitter_api():
    """Get Twitter API client using environment variables"""
    try:
        # Twitter API credentials from environment variables
        consumer_key = os.getenv("TWITTER_CONSUMER_KEY", "")
        consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET", "")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN", "")
        
        # Check if credentials are available
        if not bearer_token:
            logger.warning("Twitter bearer token not found in environment variables")
            return None
            
        # Initialize tweepy client
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )
        
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Twitter API: {str(e)}", exc_info=True)
        return None

def clean_tweet(text):
    """Clean tweet text by removing URLs, mentions, hashtags, and special characters"""
    if not text:
        return ""
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Remove mentions
    text = re.sub(r'@\S+', '', text)
    # Remove hashtags (optional)
    # text = re.sub(r'#\S+', '', text)
    # Remove special characters and extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fetch_twitter_data(query, max_results=100):
    """Fetch tweets based on a search query"""
    try:
        client = get_twitter_api()
        if not client:
            logger.warning("Twitter API client not available")
            return pd.DataFrame()
        
        # Search tweets
        tweets = client.search_recent_tweets(
            query=query,
            max_results=max_results,
            tweet_fields=['created_at', 'public_metrics', 'author_id', 'lang']
        )
        
        if not tweets.data:
            logger.warning(f"No tweets found for query: {query}")
            return pd.DataFrame()
            
        tweet_data = []
        for tweet in tweets.data:
            # Extract tweet data
            tweet_data.append({
                'id': tweet.id,
                'text': clean_tweet(tweet.text),
                'created_at': tweet.created_at,
                'retweet_count': tweet.public_metrics['retweet_count'] if hasattr(tweet, 'public_metrics') else 0,
                'like_count': tweet.public_metrics['like_count'] if hasattr(tweet, 'public_metrics') else 0,
                'reply_count': tweet.public_metrics['reply_count'] if hasattr(tweet, 'public_metrics') else 0,
                'author_id': tweet.author_id,
                'lang': tweet.lang,
                'query': query,
                'platform': 'twitter',
                'collected_at': datetime.datetime.now()
            })
        
        return pd.DataFrame(tweet_data)
    except Exception as e:
        logger.error(f"Error fetching Twitter data for query '{query}': {str(e)}", exc_info=True)
        return pd.DataFrame()

def store_social_data(df):
    """Store social media data in the database"""
    if df.empty:
        return
    
    try:
        conn = get_db_connection()
        df.to_sql('social_data', conn, if_exists='append', index=False)
        conn.close()
        logger.info(f"Stored {len(df)} social media posts")
    except Exception as e:
        logger.error(f"Failed to store social media data: {str(e)}", exc_info=True)

def update_social_data(config):
    """Update social media data from configured platforms"""
    try:
        platforms = config['SOCIAL']['Platforms'].split(',')
        max_posts = int(config['SOCIAL']['MaxPostsPerQuery'])
        
        # Get top cryptocurrencies to use as search queries
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT symbol FROM ohlcv_data
            ORDER BY (
                SELECT MAX(timestamp) FROM ohlcv_data as t2 
                WHERE t2.symbol = ohlcv_data.symbol
            ) DESC
            LIMIT 20
        """)
        top_cryptos = cursor.fetchall()
        conn.close()
        
        # Create search queries for each cryptocurrency
        search_queries = []
        for crypto in top_cryptos:
            symbol = crypto[0].split('/')[0]  # Extract base currency from symbol like BTC/USDT
            search_queries.append(symbol)
            search_queries.append(f"#{symbol}")
            
        # Add general crypto terms
        general_terms = ["crypto", "cryptocurrency", "blockchain", "bitcoin", "ethereum"]
        search_queries.extend(general_terms)
        
        # Deduplicate queries
        search_queries = list(set(search_queries))
        
        all_social_data = pd.DataFrame()
        
        for platform in platforms:
            platform = platform.strip().lower()
            logger.info(f"Collecting social media data from platform: {platform}")
            
            if platform == 'twitter':
                for query in search_queries:
                    try:
                        logger.info(f"Fetching Twitter data for query: {query}")
                        tweets_df = fetch_twitter_data(query, max_results=max_posts)
                        
                        if not tweets_df.empty:
                            all_social_data = pd.concat([all_social_data, tweets_df], ignore_index=True)
                            
                        # Be gentle with the API
                        time.sleep(2)
                    except Exception as e:
                        logger.error(f"Error processing Twitter query '{query}': {str(e)}", exc_info=True)
                        continue
            else:
                logger.warning(f"Unsupported social media platform: {platform}")
                
        if not all_social_data.empty:
            # Find existing posts to avoid duplicates
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get list of all post IDs in the new data
            post_ids = all_social_data['id'].astype(str).tolist()
            placeholders = ','.join(['?'] * len(post_ids))
            
            cursor.execute(
                f"SELECT id FROM social_data WHERE id IN ({placeholders})",
                post_ids
            )
            existing_ids = [str(row[0]) for row in cursor.fetchall()]
            conn.close()
            
            # Filter out existing posts
            new_posts = all_social_data[~all_social_data['id'].astype(str).isin(existing_ids)]
            
            if not new_posts.empty:
                logger.info(f"Storing {len(new_posts)} new social media posts")
                store_social_data(new_posts)
            else:
                logger.info("No new social media posts to store")
        else:
            logger.warning("No social media data collected from any platform")
            
    except Exception as e:
        logger.error(f"Failed to update social media data: {str(e)}", exc_info=True)
        raise

def get_recent_social_posts(limit=50, days_back=3):
    """Get recent social media posts from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate the date threshold
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        query = """
            SELECT id, text, created_at, retweet_count, like_count, reply_count, query, platform
            FROM social_data
            WHERE date(created_at) >= ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        
        cursor.execute(query, (threshold_date, limit))
        results = cursor.fetchall()
        conn.close()
        
        posts_list = []
        for row in results:
            id, text, created_at, retweet_count, like_count, reply_count, query, platform = row
            posts_list.append({
                'id': id,
                'text': text,
                'created_at': created_at,
                'retweet_count': retweet_count,
                'like_count': like_count,
                'reply_count': reply_count,
                'query': query,
                'platform': platform
            })
        
        return posts_list
    except Exception as e:
        logger.error(f"Failed to get recent social posts: {str(e)}", exc_info=True)
        return []
