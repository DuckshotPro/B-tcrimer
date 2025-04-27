import os
import logging
import datetime
import sqlite3
import sys
from logging.handlers import RotatingFileHandler

# Global logger configuration
LOGGER_NAME = "crypto_analysis"
LOG_DIRECTORY = "logs"
LOG_FILENAME = "crypto_analysis.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

# Create log directory if it doesn't exist
if not os.path.exists(LOG_DIRECTORY):
    os.makedirs(LOG_DIRECTORY)

# Configure the root logger
def setup_logging():
    """Setup application-wide logging configuration"""
    # Get root logger
    root_logger = logging.getLogger()
    
    # Clear existing handlers
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # Set the root logger level
    root_logger.setLevel(logging.DEBUG)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Create file handler
    log_path = os.path.join(LOG_DIRECTORY, LOG_FILENAME)
    file_handler = RotatingFileHandler(
        log_path, 
        maxBytes=MAX_LOG_SIZE, 
        backupCount=BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Create DB handler
    db_handler = DatabaseLogHandler()
    db_handler.setLevel(logging.INFO)
    root_logger.addHandler(db_handler)
    
    return root_logger

# Get a module-specific logger
def get_logger(name):
    """Get a logger for a specific module"""
    return logging.getLogger(name)

# Custom log handler to store logs in the database
class DatabaseLogHandler(logging.Handler):
    """Handler that writes log messages to a SQLite database"""
    
    def __init__(self):
        logging.Handler.__init__(self)
        
    def emit(self, record):
        """Write the log record to the database"""
        try:
            from database.operations import get_db_path
            
            # Format the message
            msg = self.format(record)
            
            # Get timestamp
            timestamp = datetime.datetime.fromtimestamp(record.created)
            
            # Get database path
            try:
                db_path = get_db_path()
            except:
                # If config not loaded yet, use default
                db_path = "crypto_analysis.db"
            
            # Check if database file exists
            if not os.path.exists(db_path):
                return
                
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if logs table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='logs'
            """)
            
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE TABLE logs (
                        id INTEGER PRIMARY KEY,
                        timestamp DATETIME NOT NULL,
                        level VARCHAR(10) NOT NULL,
                        module VARCHAR(50) NOT NULL,
                        message TEXT NOT NULL,
                        details TEXT
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_logs_timestamp ON logs (timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_logs_level ON logs (level)
                """)
                
                conn.commit()
            
            # Insert the log record
            cursor.execute(
                """
                INSERT INTO logs (timestamp, level, module, message, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    record.levelname,
                    record.name,
                    record.getMessage(),
                    str(record.exc_info) if record.exc_info else None
                )
            )
            
            conn.commit()
            conn.close()
        except Exception:
            # Don't crash if logging fails
            pass

def get_recent_logs(level=None, limit=100):
    """Get recent logs from the database"""
    try:
        from database.operations import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if level:
            query = """
                SELECT timestamp, level, module, message, details
                FROM logs
                WHERE level = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            cursor.execute(query, (level, limit))
        else:
            query = """
                SELECT timestamp, level, module, message, details
                FROM logs
                ORDER BY timestamp DESC
                LIMIT ?
            """
            cursor.execute(query, (limit,))
            
        logs = cursor.fetchall()
        conn.close()
        
        result = []
        for log in logs:
            timestamp, level, module, message, details = log
            result.append({
                'timestamp': timestamp,
                'level': level,
                'module': module,
                'message': message,
                'details': details
            })
            
        return result
    except Exception as e:
        print(f"Error retrieving logs: {e}")
        return []

def get_error_logs(limit=50):
    """Get recent error logs from the database"""
    return get_recent_logs(level="ERROR", limit=limit)

def get_log_statistics(days=7):
    """Get statistics about logs over the past days"""
    try:
        from database.operations import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate the date threshold
        threshold_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Get counts by level
        query = """
            SELECT level, COUNT(*) as count
            FROM logs
            WHERE date(timestamp) >= ?
            GROUP BY level
            ORDER BY count DESC
        """
        
        cursor.execute(query, (threshold_date,))
        level_counts = cursor.fetchall()
        
        # Get counts by day and level
        query = """
            SELECT date(timestamp) as day, level, COUNT(*) as count
            FROM logs
            WHERE date(timestamp) >= ?
            GROUP BY day, level
            ORDER BY day, level
        """
        
        cursor.execute(query, (threshold_date,))
        daily_counts = cursor.fetchall()
        
        # Get most recent errors
        query = """
            SELECT timestamp, module, message
            FROM logs
            WHERE level = 'ERROR' AND date(timestamp) >= ?
            ORDER BY timestamp DESC
            LIMIT 5
        """
        
        cursor.execute(query, (threshold_date,))
        recent_errors = cursor.fetchall()
        
        conn.close()
        
        # Format results
        level_stats = {}
        for level, count in level_counts:
            level_stats[level] = count
            
        daily_stats = {}
        for day, level, count in daily_counts:
            if day not in daily_stats:
                daily_stats[day] = {}
            daily_stats[day][level] = count
            
        error_list = []
        for timestamp, module, message in recent_errors:
            error_list.append({
                'timestamp': timestamp,
                'module': module,
                'message': message
            })
            
        return {
            'level_counts': level_stats,
            'daily_counts': daily_stats,
            'recent_errors': error_list
        }
    except Exception as e:
        print(f"Error retrieving log statistics: {e}")
        return {
            'level_counts': {},
            'daily_counts': {},
            'recent_errors': []
        }
