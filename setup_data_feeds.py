#!/usr/bin/env python3
"""Setup RSS feeds and social media data collection"""
import sys
import os
sys.path.append('.')

from data_collection.news_data import update_news_data
from data_collection.social_data import update_social_data
from utils.logging_config import get_logger
import configparser

logger = get_logger(__name__)

def setup_feeds():
    """Set up RSS feeds and social media data collection"""
    try:
        # Read configuration
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        print("Setting up RSS feeds and social media data collection...")
        
        # Update news data from RSS feeds
        print("Fetching cryptocurrency news from RSS feeds...")
        try:
            update_news_data(config)
            print("✓ News data collection complete")
        except Exception as e:
            print(f"✗ News data collection failed: {e}")
        
        # Update social media data (if Twitter credentials available)
        print("Fetching social media data...")
        try:
            update_social_data(config)
            print("✓ Social media data collection complete")
        except Exception as e:
            print(f"✗ Social media data collection failed: {e}")
            print("Note: Social media requires Twitter API credentials")
        
        print("✓ Data feeds setup complete")
        
    except Exception as e:
        print(f"Error setting up feeds: {e}")

if __name__ == "__main__":
    setup_feeds()