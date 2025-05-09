import feedparser
import pandas as pd
import datetime
import time
import re
import os
import random
from utils.logging_config import get_logger
from database.operations import get_db_connection
from data_collection.web_scraper import get_website_text_content

logger = get_logger(__name__)

def clean_html(html_text):
    """Remove HTML tags from text"""
    if not html_text:
        return ""
    clean_text = re.sub(r'<.*?>', '', html_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def fetch_rss_feed(url):
    """Fetch news from an RSS feed"""
    try:
        feed = feedparser.parse(url)
        
        if not feed.entries:
            logger.warning(f"No entries found in feed: {url}")
            return pd.DataFrame()
            
        entries = []
        for entry in feed.entries:
            # Extract relevant fields
            title = entry.get('title', '')
            
            # Handle different date formats
            published = entry.get('published', entry.get('pubDate', ''))
            if published:
                try:
                    # Try to parse the date in various formats
                    date_obj = datetime.datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %z')
                except ValueError:
                    try:
                        date_obj = datetime.datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %Z')
                    except ValueError:
                        try:
                            date_obj = datetime.datetime.strptime(published, '%Y-%m-%dT%H:%M:%S%z')
                        except ValueError:
                            date_obj = datetime.datetime.now()  # Default to current time if parsing fails
            else:
                date_obj = datetime.datetime.now()
                
            link = entry.get('link', '')
            description = clean_html(entry.get('description', entry.get('summary', '')))
            
            entries.append({
                'title': title,
                'published_date': date_obj,
                'link': link,
                'description': description,
                'source': url,
                'collected_at': datetime.datetime.now()
            })
        
        return pd.DataFrame(entries)
    except Exception as e:
        logger.error(f"Error fetching RSS feed {url}: {str(e)}", exc_info=True)
        return pd.DataFrame()

def store_news_data(df):
    """Store news data in the database"""
    if df.empty:
        return
    
    try:
        conn = get_db_connection()
        df.to_sql('news_data', conn, if_exists='append', index=False)
        conn.close()
        logger.info(f"Stored {len(df)} news articles")
    except Exception as e:
        logger.error(f"Failed to store news data: {str(e)}", exc_info=True)

def update_news_data(config):
    """Update news data from configured RSS sources"""
    try:
        rss_sources = config['NEWS']['Sources'].split(',')
        max_articles = int(config['NEWS']['MaxArticlesPerSource'])
        
        all_news = pd.DataFrame()
        
        for source_url in rss_sources:
            source_url = source_url.strip()
            logger.info(f"Fetching news from: {source_url}")
            
            try:
                # Fetch news
                news_df = fetch_rss_feed(source_url)
                
                if not news_df.empty:
                    # Limit the number of articles per source
                    news_df = news_df.head(max_articles)
                    all_news = pd.concat([all_news, news_df], ignore_index=True)
                
                # Be gentle with the sources
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error processing news from {source_url}: {str(e)}", exc_info=True)
                continue
        
        if not all_news.empty:
            # Find existing articles to avoid duplicates
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get list of all links in the new data
            links = all_news['link'].tolist()
            placeholders = ','.join(['?'] * len(links))
            
            cursor.execute(
                f"SELECT link FROM news_data WHERE link IN ({placeholders})",
                links
            )
            existing_links = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # Filter out existing articles
            new_articles = all_news[~all_news['link'].isin(existing_links)]
            
            if not new_articles.empty:
                logger.info(f"Storing {len(new_articles)} new articles")
                store_news_data(new_articles)
            else:
                logger.info("No new articles to store")
        else:
            logger.warning("No news articles collected from any source")
            
    except Exception as e:
        logger.error(f"Failed to update news data: {str(e)}", exc_info=True)
        raise

def get_recent_news(limit=50, days_back=7):
    """Get recent news articles from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate the date threshold
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        query = """
            SELECT title, published_date, link, description, source
            FROM news_data
            WHERE date(published_date) >= ?
            ORDER BY published_date DESC
            LIMIT ?
        """
        
        cursor.execute(query, (threshold_date, limit))
        results = cursor.fetchall()
        conn.close()
        
        news_list = []
        for row in results:
            title, published_date, link, description, source = row
            news_list.append({
                'title': title,
                'published_date': published_date,
                'link': link,
                'description': description,
                'source': source
            })
        
        return news_list
    except Exception as e:
        logger.error(f"Failed to get recent news: {str(e)}", exc_info=True)
        return []
