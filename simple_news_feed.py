#!/usr/bin/env python3
"""Simple news feed collection"""
import feedparser
import psycopg2
import os
from datetime import datetime

def collect_crypto_news():
    """Collect cryptocurrency news from RSS feeds"""
    try:
        # Connect to database
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cursor = conn.cursor()
        
        # RSS feeds for cryptocurrency news
        feeds = [
            ('https://cointelegraph.com/rss', 'CoinTelegraph'),
            ('https://cryptonews.com/news/feed/', 'CryptoNews'),
            ('https://decrypt.co/feed', 'Decrypt'),
        ]
        
        for feed_url, source in feeds:
            try:
                print(f"Fetching news from {source}...")
                feed = feedparser.parse(feed_url)
                
                if not feed.entries:
                    print(f"No entries found for {source}")
                    continue
                    
                for entry in feed.entries[:10]:  # Limit to 10 articles per feed
                    title = entry.title
                    link = entry.link
                    published = entry.published if hasattr(entry, 'published') else datetime.now()
                    
                    # Parse published date
                    try:
                        if isinstance(published, str):
                            pub_date = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %z')
                        else:
                            pub_date = datetime.now()
                    except:
                        pub_date = datetime.now()
                    
                    # Insert news article
                    insert_query = """
                    INSERT INTO news_data (title, link, published_date, source, collected_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (link) DO NOTHING
                    """
                    
                    cursor.execute(insert_query, (
                        title, link, pub_date, source, datetime.now()
                    ))
                
                conn.commit()
                print(f"✓ Added news from {source}")
                
            except Exception as e:
                print(f"✗ Error fetching {source}: {e}")
                continue
        
        cursor.close()
        conn.close()
        print("✓ News collection complete")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    collect_crypto_news()