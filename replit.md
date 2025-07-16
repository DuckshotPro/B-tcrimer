# Cryptocurrency Analysis Platform

## Overview

This is a comprehensive cryptocurrency analysis platform built with Streamlit that provides real-time market data, sentiment analysis, technical indicators, and trading strategy backtesting. The application integrates multiple data sources including cryptocurrency exchanges, news feeds, and social media to provide actionable insights for cryptocurrency trading and investment decisions.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

- **Frontend**: Streamlit-based web interface with multiple pages for different functionalities
- **Backend**: Python-based data collection and analysis modules
- **Database**: Flexible database layer supporting both SQLite (development) and PostgreSQL (production)
- **Data Collection**: Multi-source data ingestion from exchanges, news, and social media
- **Analysis Engine**: Technical indicators, sentiment analysis, and backtesting capabilities

## Key Components

### Database Layer (`database/`)
- **SQLAlchemy Models**: Defines data structures for OHLCV data, news articles, social media posts, and technical indicators
- **Operations Module**: Handles database connections with automatic fallback from PostgreSQL to SQLite
- **Schema**: Supports cryptocurrency price data, news sentiment, social media sentiment, and custom data sources

### Data Collection (`data_collection/`)
- **Exchange Data**: Uses CCXT library to fetch OHLCV data from multiple cryptocurrency exchanges
- **News Data**: RSS feed parsing and web scraping using Trafilatura for cryptocurrency news
- **Social Data**: Twitter API integration for social media sentiment collection
- **Custom Sources**: Extensible framework for adding custom API and CSV data sources
- **Web Scraper**: General-purpose web content extraction for news articles

### Analysis Engine (`analysis/`)
- **Technical Indicators**: RSI, MACD, Moving Averages, and other technical analysis tools
- **Sentiment Analysis**: Google Cloud Natural Language API integration with fallback to basic sentiment
- **Backtesting**: Strategy testing framework with multiple built-in trading strategies

### User Interface (`pages/`)
- **Dashboard**: Main overview with price charts and market summaries
- **Data Sources**: Configuration and management of data collection sources
- **Technical Analysis**: Interactive technical indicator charts and signals
- **Sentiment**: Sentiment analysis visualization and trends
- **Alerts**: Price and indicator-based notification system
- **Backtesting**: Strategy testing interface with performance metrics
- **Logs**: System monitoring and debugging information

### Utilities (`utils/`)
- **Logging**: Centralized logging with file rotation and database logging
- **Email Alerts**: SMTP-based email notification system
- **SMS Alerts**: Twilio integration for SMS notifications

## Data Flow

1. **Data Collection**: Scheduled updates fetch data from exchanges, news feeds, and social media
2. **Data Processing**: Raw data is cleaned, normalized, and stored in the database
3. **Analysis**: Technical indicators and sentiment scores are calculated and cached
4. **Visualization**: Processed data is displayed through interactive Streamlit charts
5. **Alerts**: Monitoring system checks conditions and sends notifications
6. **Backtesting**: Historical data is used to test trading strategies

The application uses a session-based refresh mechanism to update data at configurable intervals while maintaining responsive user interaction.

## External Dependencies

### Required APIs
- **CCXT**: Cryptocurrency exchange data (multiple exchanges supported)
- **Google Cloud Natural Language API**: Advanced sentiment analysis (optional)
- **Twitter API v2**: Social media sentiment data (optional)
- **Twilio**: SMS alert notifications (optional)

### Python Libraries
- **Streamlit**: Web interface framework
- **SQLAlchemy**: Database ORM with PostgreSQL and SQLite support
- **Pandas/NumPy**: Data manipulation and analysis
- **Plotly**: Interactive charting and visualization
- **Feedparser**: RSS feed parsing for news data
- **Trafilatura**: Web content extraction
- **Tweepy**: Twitter API client
- **psycopg2**: PostgreSQL database adapter

### Configuration
The application uses a `config.ini` file for settings and environment variables for sensitive credentials. Database connection automatically detects and uses PostgreSQL if `DATABASE_URL` is available, otherwise falls back to SQLite.

## Deployment Strategy

The application is designed for flexible deployment:

- **Development**: Uses SQLite database with local file storage
- **Production**: Automatically detects and uses PostgreSQL via `DATABASE_URL` environment variable
- **Replit Ready**: Includes secret management integration and simplified dependency handling
- **Containerizable**: Modular structure supports Docker deployment
- **Scalable**: Database layer supports connection pooling and can be extended to support multiple database instances

The codebase includes comprehensive error handling, logging, and fallback mechanisms to ensure reliability across different deployment environments. The modular design allows for easy addition of new data sources, analysis methods, and visualization components.