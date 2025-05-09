import trafilatura
import requests
import time
import datetime
import pandas as pd
from utils.logging_config import get_logger
from database.operations import get_db_connection

logger = get_logger(__name__)

def get_website_text_content(url: str, retries=3, backoff_factor=2.0) -> str:
    """
    Extract the main text content from a website using Trafilatura.
    
    Args:
        url: The URL of the website to scrape
        retries: Number of times to retry in case of failure
        backoff_factor: Factor to increase the delay between retries
        
    Returns:
        String containing the main text content of the website
    """
    try:
        logger.info(f"Fetching content from: {url}")
        
        # Set custom headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # Implement retry logic with exponential backoff
        delay = 1
        for attempt in range(retries):
            try:
                # Use requests to get the webpage with custom headers
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                html_content = response.text
                
                # Pass the HTML content to trafilatura for extraction
                downloaded = html_content
                
                if downloaded:
                    # Extract the main content
                    text = trafilatura.extract(downloaded, include_comments=False, 
                                             include_tables=True)
                    
                    if text:
                        logger.info(f"Successfully extracted content from {url}")
                        return text
                    else:
                        logger.warning(f"Trafilatura couldn't extract content from {url}")
                        # If trafilatura extraction fails, try with a basic fallback
                        return extract_fallback(downloaded)
                else:
                    logger.warning(f"Failed to download content from {url} on attempt {attempt+1}")
                    
                # Exponential backoff with jitter
                time.sleep(delay * (1 + 0.1 * (attempt + 1)))
                delay *= backoff_factor
                    
            except Exception as e:
                logger.error(f"Error on attempt {attempt+1} for {url}: {str(e)}")
                time.sleep(delay * (1 + 0.1 * (attempt + 1)))
                delay *= backoff_factor
                
        logger.error(f"Failed to extract content after {retries} attempts from {url}")
        return ""
        
    except Exception as e:
        logger.error(f"Unexpected error scraping {url}: {str(e)}", exc_info=True)
        return ""
        
def extract_fallback(html_content):
    """Basic fallback extraction method when Trafilatura fails"""
    try:
        # Use trafilatura's fallback method
        return trafilatura.extract(html_content, fallback=True, include_comments=False)
    except Exception as e:
        logger.error(f"Fallback extraction failed: {str(e)}")
        return ""

def store_scraped_content(url, content, source_name="custom_scraper"):
    """Store scraped content in the database for later use"""
    try:
        if not content:
            logger.warning(f"No content to store for URL: {url}")
            return False
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if we already have this URL
        cursor.execute(
            "SELECT id FROM custom_data WHERE data LIKE ?",
            [f'%{url}%']
        )
        existing = cursor.fetchone()
        
        now = datetime.datetime.now()
        data = {
            'url': url,
            'content': content,
            'scraped_at': now.isoformat(),
            'source': source_name
        }
        
        if existing:
            logger.info(f"URL {url} already exists in database, updating content")
            # Update approach depends on how custom_data is structured
            cursor.execute(
                "UPDATE custom_data SET data = ?, collected_at = ? WHERE id = ?",
                [
                    pd.Series(data).to_json(),
                    now,
                    existing[0]
                ]
            )
        else:
            # Create a new source ID
            source_id = f"scraper_{int(time.time())}"
            
            cursor.execute(
                "INSERT INTO custom_data (source_id, data, collected_at) VALUES (?, ?, ?)",
                [
                    source_id,
                    pd.Series(data).to_json(),
                    now
                ]
            )
            
        conn.commit()
        conn.close()
        logger.info(f"Successfully stored content from {url}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store scraped content from {url}: {str(e)}", exc_info=True)
        return False

def scrape_multiple_urls(urls, store=True, source_name="batch_scraper"):
    """
    Scrape multiple URLs with proper rate limiting and error handling
    
    Args:
        urls: List of URLs to scrape
        store: Whether to store the results in the database
        source_name: Name to use when storing scraped content
        
    Returns:
        Dictionary mapping URLs to their extracted content
    """
    results = {}
    
    for url in urls:
        try:
            # Be respectful with rate limiting
            time.sleep(2)  # 2 second delay between requests
            
            content = get_website_text_content(url)
            results[url] = content
            
            if store and content:
                store_scraped_content(url, content, source_name)
                
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {str(e)}", exc_info=True)
            results[url] = ""
            
    return results

def scrape_cryptocurrency_news(crypto_name, limit=5):
    """
    Scrape news specifically about a cryptocurrency
    
    Args:
        crypto_name: Name of the cryptocurrency (e.g., "Bitcoin", "Ethereum")
        limit: Maximum number of articles to scrape
        
    Returns:
        List of dictionaries containing scraped articles
    """
    try:
        # First, get recent news about this cryptocurrency from our database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT link 
            FROM news_data 
            WHERE (title LIKE ? OR description LIKE ?) 
            AND published_date > ?
            ORDER BY published_date DESC
            LIMIT ?
        """
        
        # Search terms with wildcards
        search_term = f"%{crypto_name}%"
        week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        
        cursor.execute(query, (search_term, search_term, week_ago, limit))
        articles = cursor.fetchall()
        conn.close()
        
        if not articles:
            logger.warning(f"No recent articles found for {crypto_name}")
            return []
            
        # Extract URLs
        urls = [article[0] for article in articles]
        
        # Scrape content from these URLs
        scraped_content = scrape_multiple_urls(urls, store=True, source_name=f"{crypto_name}_news")
        
        # Format results
        results = []
        for url, content in scraped_content.items():
            if content:
                results.append({
                    'url': url,
                    'content': content,
                    'cryptocurrency': crypto_name,
                    'scraped_at': datetime.datetime.now().isoformat()
                })
                
        return results
        
    except Exception as e:
        logger.error(f"Failed to scrape cryptocurrency news for {crypto_name}: {str(e)}", exc_info=True)
        return []