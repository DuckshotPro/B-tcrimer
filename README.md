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

---

## Automated Cloud Deployment (Railway)

This project is configured for fully automated deployment to Railway, a modern platform for deploying applications. With the provided setup, a `git push` to the `main` branch will automatically update your production environment.

### Prerequisites

Before you begin, ensure you have:

1.  **A GitHub Account**: Your project must be hosted on GitHub.
2.  **A Railway Account**: Sign up at [railway.app](https://railway.app/).
3.  **Railway CLI (Optional, but Recommended for Local Testing)**:
    ```bash
    npm i -g @railway/cli
    ```
4.  **Alembic Installed Locally**:
    ```bash
    pip install alembic psycopg2-binary
    ```

### Deployment Steps

Follow these steps to deploy your application to Railway:

#### 1. Initial Project Setup (One-Time)

a.  **Commit and Push**: Ensure all your local changes (including the `railway.json`, `Procfile`, `.github/workflows/deploy.yml`, and updated `requirements.txt`) are committed and pushed to the `main` branch of your GitHub repository.

b.  **Create Railway Project**:
    *   Go to your Railway dashboard and click "New Project".
    *   Select "Deploy from GitHub Repo" and choose your `b-tcrimer` repository.
    *   Railway will automatically detect the `railway.json` and set up your services (API and PostgreSQL database).

c.  **Configure Environment Variables**:
    *   In your Railway project settings, navigate to the "Variables" tab.
    *   Add the following environment variables. **These are crucial for your application and database to function correctly.**
        *   `DATABASE_URL`: This will be automatically generated by Railway for your PostgreSQL service. You can find it in the "Connect" tab of your PostgreSQL service.
        *   `API_KEY`: A secret key for your application's API. Generate a strong, random key.
        *   `POSTGRES_USER`: (From Railway's PostgreSQL service)
        *   `POSTGRES_PASSWORD`: (From Railway's PostgreSQL service)
        *   `POSTGRES_DB`: (From Railway's PostgreSQL service)
    *   **GitHub Secrets**: For the GitHub Actions workflow to deploy, you need to add your Railway API token as a secret in your GitHub repository.
        *   Go to your GitHub repository -> Settings -> Secrets and variables -> Actions -> New repository secret.
        *   Name: `RAILWAY_TOKEN`
        *   Value: Your Railway API token (you can generate one in your Railway account settings under "Tokens").

#### 2. Database Migrations (Alembic)

This project uses Alembic for database migrations to manage schema changes.

a.  **Initialize Alembic Locally**:
    *   Navigate to the `b-tcrimer-api` directory in your local terminal:
        ```bash
        cd b-tcrimer/b-tcrimer-api
        ```
    *   Initialize Alembic:
        ```bash
        alembic init migrations
        ```
        This creates a `migrations` directory and an `alembic.ini` file.

b.  **Configure `alembic.ini`**:
    *   Open `b-tcrimer-api/alembic.ini`.
    *   Under the `[alembic]` section, set `script_location = migrations`.
    *   Set `sqlalchemy.url` to your local development database (e.g., `sqlite:///./sql_app.db` or a local PostgreSQL connection string). This is for local development only; Railway will use the `DATABASE_URL` environment variable.

c.  **Configure `migrations/env.py`**:
    *   Open `b-tcrimer-api/migrations/env.py`.
    *   Import your SQLAlchemy `Base` (or `MetaData`) object from your application's `database.py`. For example:
        ```python
        from b_tcrimer_api.database import Base # Adjust this import based on your actual path
        # ...
        target_metadata = Base.metadata
        ```
    *   Ensure the `run_migrations_online` function is configured to pick up the `DATABASE_URL` from environment variables for production deployments. The provided `railway.json` will handle this automatically.

d.  **Create Initial Migration**:
    *   From the `b-tcrimer-api` directory, generate your first migration script:
        ```bash
        alembic revision --autogenerate -m "Initial database setup"
        ```
        Review the generated script in `migrations/versions/` to ensure it correctly reflects your database schema.

e.  **Apply Initial Migration Locally**:
    *   Apply the migration to your local database:
        ```bash
        alembic upgrade head
        ```

#### 3. Continuous Deployment

Once the initial setup is complete and your `RAILWAY_TOKEN` is configured in GitHub Secrets, every `git push` to the `main` branch of your GitHub repository will automatically:

1.  Trigger the GitHub Actions workflow (`.github/workflows/deploy.yml`).
2.  Install the Railway CLI.
3.  Deploy your application to Railway.
4.  Railway will then run the `releaseCommand` (`alembic upgrade head`) to apply any pending database migrations before starting the new application instance.

### Monitoring and Logging

*   **Health Checks**: The application exposes a `/health` endpoint that Railway uses for health checks.
*   **Logs**: Railway automatically collects and displays all logs written to `stdout` by your application. You can view these in your Railway project dashboard.
*   **Error Alerting**: For advanced error alerting, consider integrating a service like Sentry into your application.

### Scaling and Security

*   **Auto-scaling**: The `railway.json` is configured with `minReplicas` and `maxReplicas` for basic auto-scaling. You can adjust these values based on your traffic needs.
*   **SSL Certificates**: Railway automatically provides SSL certificates for your application.
*   **Custom Domains**: You can easily configure custom domains for your application within the Railway dashboard.

### Database Backups

*   Railway's PostgreSQL service includes automated daily backups. You can manage and restore these backups directly from your Railway project dashboard.

This comprehensive setup ensures a smooth and automated deployment experience for your crypto trading API service.
