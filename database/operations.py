import os
import sqlite3
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from utils.logging_config import get_logger
from database.models import Base

logger = get_logger(__name__)

def get_db_path():
    """Get the database path from config"""
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['DEFAULT']['DatabasePath']

def get_db_connection():
    """Get a SQLite database connection"""
    try:
        # Check if we should use PostgreSQL or SQLite
        if 'DATABASE_URL' in os.environ:
            # We have a PostgreSQL connection string
            logger.info("Using PostgreSQL database")
            import psycopg2
            from psycopg2.extras import DictCursor
            
            conn = psycopg2.connect(
                os.environ.get('DATABASE_URL'),
                cursor_factory=DictCursor
            )
            return conn
        else:
            # Use SQLite as fallback
            logger.info("Using SQLite database")
            db_path = get_db_path()
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}", exc_info=True)
        raise

def get_sqlalchemy_engine():
    """Get a SQLAlchemy engine for the database"""
    try:
        # Check if we should use PostgreSQL or SQLite
        if 'DATABASE_URL' in os.environ:
            # We have a PostgreSQL connection string
            logger.info("Using PostgreSQL SQLAlchemy engine")
            engine = create_engine(
                os.environ.get('DATABASE_URL')
            )
            return engine
        else:
            # Use SQLite as fallback
            logger.info("Using SQLite SQLAlchemy engine")
            db_path = get_db_path()
            engine = create_engine(
                f"sqlite:///{db_path}", 
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
            return engine
    except Exception as e:
        logger.error(f"Failed to create SQLAlchemy engine: {str(e)}", exc_info=True)
        raise

def get_sqlalchemy_session():
    """Get a SQLAlchemy session"""
    try:
        engine = get_sqlalchemy_engine()
        Session = sessionmaker(bind=engine)
        return Session()
    except Exception as e:
        logger.error(f"Failed to create SQLAlchemy session: {str(e)}", exc_info=True)
        raise

def initialize_database():
    """Initialize the database with required tables"""
    try:
        # Create an SQLAlchemy engine
        engine = get_sqlalchemy_engine()
        
        # Create tables
        Base.metadata.create_all(engine)
        
        if 'DATABASE_URL' in os.environ:
            logger.info("Created PostgreSQL database tables")
        else:
            db_path = get_db_path()
            # Check if the database already exists
            db_exists = os.path.exists(db_path)
            
            if not db_exists:
                logger.info(f"Created new SQLite database at {db_path}")
            else:
                logger.info(f"Connected to existing SQLite database at {db_path}")
        
        # Create direct connection for additional setup if needed
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create indexes if using PostgreSQL 
        if 'DATABASE_URL' in os.environ:
            # For PostgreSQL - create indexes if not existing using PostgreSQL syntax
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timestamp 
                ON ohlcv_data (symbol, timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_published_date 
                ON news_data (published_date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_social_created_at 
                ON social_data (created_at)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sentiment_item_source 
                ON sentiment_data (item_id, source)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_technical_symbol_timestamp 
                ON technical_indicators (symbol, timestamp)
            """)
        else:
            # For SQLite - create indexes using SQLite syntax
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timestamp 
                ON ohlcv_data (symbol, timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_news_published_date 
                ON news_data (published_date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_social_created_at 
                ON social_data (created_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sentiment_item_source 
                ON sentiment_data (item_id, source)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_technical_symbol_timestamp 
                ON technical_indicators (symbol, timestamp)
            ''')
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise

def perform_database_maintenance():
    """Perform database maintenance operations"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Database-specific maintenance operations
        if 'DATABASE_URL' in os.environ:
            # PostgreSQL maintenance
            logger.info("Performing PostgreSQL database maintenance")
            
            # Run ANALYZE to optimize query planning
            cursor.execute("ANALYZE")
            
            # We don't use VACUUM with PostgreSQL as it's handled by autovacuum
            
        else:
            # SQLite maintenance
            logger.info("Performing SQLite database maintenance")
            
            # Run VACUUM to optimize database size
            cursor.execute("VACUUM")
            
            # Run ANALYZE to optimize query planning
            cursor.execute("ANALYZE")
            
            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            if integrity_result != "ok":
                logger.error(f"Database integrity check failed: {integrity_result}")
            else:
                logger.info("Database maintenance completed successfully")
        
        # Data cleanup operations - common for both databases
        # Keep 1 year of OHLCV data
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
        
        if 'DATABASE_URL' in os.environ:
            # PostgreSQL format
            cursor.execute(
                "DELETE FROM ohlcv_data WHERE timestamp::date < %s",
                (threshold_date,)
            )
        else:
            # SQLite format
            cursor.execute(
                "DELETE FROM ohlcv_data WHERE date(timestamp) < ?",
                (threshold_date,)
            )
            
        deleted_rows = cursor.rowcount
        if deleted_rows > 0:
            logger.info(f"Removed {deleted_rows} old OHLCV records")
            
        # Keep 3 months of news data
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime('%Y-%m-%d')
        
        if 'DATABASE_URL' in os.environ:
            # PostgreSQL format
            cursor.execute(
                "DELETE FROM news_data WHERE published_date::date < %s",
                (threshold_date,)
            )
        else:
            # SQLite format
            cursor.execute(
                "DELETE FROM news_data WHERE date(published_date) < ?",
                (threshold_date,)
            )
            
        deleted_rows = cursor.rowcount
        if deleted_rows > 0:
            logger.info(f"Removed {deleted_rows} old news records")
            
        # Keep 1 month of social data
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        
        if 'DATABASE_URL' in os.environ:
            # PostgreSQL format
            cursor.execute(
                "DELETE FROM social_data WHERE created_at::date < %s",
                (threshold_date,)
            )
        else:
            # SQLite format
            cursor.execute(
                "DELETE FROM social_data WHERE date(created_at) < ?",
                (threshold_date,)
            )
            
        deleted_rows = cursor.rowcount
        if deleted_rows > 0:
            logger.info(f"Removed {deleted_rows} old social media records")
            
        # Remove sentiment data for deleted items
        cursor.execute("""
            DELETE FROM sentiment_data 
            WHERE source = 'news' AND item_id NOT IN (SELECT id FROM news_data)
        """)
        deleted_rows = cursor.rowcount
        if deleted_rows > 0:
            logger.info(f"Removed {deleted_rows} orphaned news sentiment records")
            
        cursor.execute("""
            DELETE FROM sentiment_data 
            WHERE source = 'social' AND item_id NOT IN (SELECT id FROM social_data)
        """)
        deleted_rows = cursor.rowcount
        if deleted_rows > 0:
            logger.info(f"Removed {deleted_rows} orphaned social sentiment records")
            
        # Clean up old logs
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        
        if 'DATABASE_URL' in os.environ:
            # PostgreSQL format
            cursor.execute(
                "DELETE FROM logs WHERE timestamp::date < %s AND level != 'ERROR'",
                (threshold_date,)
            )
        else:
            # SQLite format
            cursor.execute(
                "DELETE FROM logs WHERE date(timestamp) < ? AND level != 'ERROR'",
                (threshold_date,)
            )
            
        deleted_rows = cursor.rowcount
        if deleted_rows > 0:
            logger.info(f"Removed {deleted_rows} old log records")
            
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Failed to perform database maintenance: {str(e)}", exc_info=True)
        return False
