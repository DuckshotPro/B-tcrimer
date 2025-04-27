import pandas as pd
import requests
import json
import csv
import datetime
import os
import sqlite3
import io
from utils.logging_config import get_logger
from database.operations import get_db_connection

logger = get_logger(__name__)

class CustomDataSource:
    """Base class for custom data sources"""
    def __init__(self, source_id, name, description, source_type, config):
        self.source_id = source_id
        self.name = name
        self.description = description
        self.source_type = source_type
        self.config = config
        self.enabled = True
        
    def fetch_data(self):
        """Fetch data from the source - to be implemented by subclasses"""
        raise NotImplementedError()
        
    def process_data(self, raw_data):
        """Process raw data - to be implemented by subclasses"""
        raise NotImplementedError()
        
    def store_data(self, data):
        """Store the processed data"""
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            logger.warning(f"No data to store for source {self.name}")
            return
            
        try:
            conn = get_db_connection()
            
            # Store the data in custom_data table
            if isinstance(data, pd.DataFrame):
                # Convert DataFrame to json for storage
                json_data = data.to_json(orient='records')
                
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO custom_data (source_id, data, collected_at)
                    VALUES (?, ?, ?)
                    """,
                    (self.source_id, json_data, datetime.datetime.now())
                )
            elif isinstance(data, dict) or isinstance(data, list):
                # Store dict or list as JSON
                json_data = json.dumps(data)
                
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO custom_data (source_id, data, collected_at)
                    VALUES (?, ?, ?)
                    """,
                    (self.source_id, json_data, datetime.datetime.now())
                )
            else:
                # Store other data types as string
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO custom_data (source_id, data, collected_at)
                    VALUES (?, ?, ?)
                    """,
                    (self.source_id, str(data), datetime.datetime.now())
                )
                
            conn.commit()
            conn.close()
            logger.info(f"Stored custom data for source {self.name}")
        except Exception as e:
            logger.error(f"Failed to store custom data for source {self.name}: {str(e)}", exc_info=True)

class ApiDataSource(CustomDataSource):
    """Custom data source for REST APIs"""
    def __init__(self, source_id, name, description, url, headers=None, params=None, method="GET"):
        super().__init__(source_id, name, description, "API", {
            "url": url,
            "headers": headers or {},
            "params": params or {},
            "method": method
        })
        
    def fetch_data(self):
        """Fetch data from the REST API"""
        try:
            method = self.config.get("method", "GET").upper()
            url = self.config.get("url", "")
            headers = self.config.get("headers", {})
            params = self.config.get("params", {})
            
            if not url:
                logger.error(f"URL not provided for API source {self.name}")
                return None
                
            logger.info(f"Fetching data from API: {url}")
            
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=params, timeout=30)
            else:
                logger.error(f"Unsupported method {method} for API source {self.name}")
                return None
                
            response.raise_for_status()
            
            # Try to parse as JSON
            try:
                return response.json()
            except ValueError:
                # Return text if not JSON
                return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for API source {self.name}: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Failed to fetch data from API source {self.name}: {str(e)}", exc_info=True)
            return None
            
    def process_data(self, raw_data):
        """Process the raw API response"""
        if raw_data is None:
            return None
            
        try:
            # If already a dict or list, return as-is
            if isinstance(raw_data, dict) or isinstance(raw_data, list):
                return raw_data
                
            # Try to parse string as JSON
            if isinstance(raw_data, str):
                try:
                    return json.loads(raw_data)
                except json.JSONDecodeError:
                    # Return as-is if not valid JSON
                    return raw_data
                    
            return raw_data
        except Exception as e:
            logger.error(f"Failed to process data from API source {self.name}: {str(e)}", exc_info=True)
            return None

class CsvDataSource(CustomDataSource):
    """Custom data source for CSV files or URLs"""
    def __init__(self, source_id, name, description, location, delimiter=",", has_header=True, encoding="utf-8"):
        super().__init__(source_id, name, description, "CSV", {
            "location": location,
            "delimiter": delimiter,
            "has_header": has_header,
            "encoding": encoding
        })
        
    def fetch_data(self):
        """Fetch data from the CSV source"""
        try:
            location = self.config.get("location", "")
            encoding = self.config.get("encoding", "utf-8")
            
            if not location:
                logger.error(f"Location not provided for CSV source {self.name}")
                return None
                
            logger.info(f"Fetching data from CSV source: {location}")
            
            # Check if location is a URL
            if location.startswith("http://") or location.startswith("https://"):
                response = requests.get(location, timeout=30)
                response.raise_for_status()
                content = response.content.decode(encoding)
                return io.StringIO(content)
            else:
                # Assume it's a local file path
                if not os.path.exists(location):
                    logger.error(f"CSV file not found: {location}")
                    return None
                    
                return open(location, 'r', encoding=encoding)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for CSV source {self.name}: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Failed to fetch data from CSV source {self.name}: {str(e)}", exc_info=True)
            return None
            
    def process_data(self, raw_data):
        """Process the raw CSV data"""
        if raw_data is None:
            return None
            
        try:
            delimiter = self.config.get("delimiter", ",")
            has_header = self.config.get("has_header", True)
            
            # Parse CSV
            if has_header:
                df = pd.read_csv(raw_data, delimiter=delimiter)
            else:
                df = pd.read_csv(raw_data, delimiter=delimiter, header=None)
                
            return df
        except Exception as e:
            logger.error(f"Failed to process data from CSV source {self.name}: {str(e)}", exc_info=True)
            return None
        finally:
            # Close the file if it's a file object
            if hasattr(raw_data, 'close'):
                raw_data.close()

def save_custom_source(source):
    """Save or update a custom data source in the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if source already exists
        cursor.execute(
            "SELECT id FROM custom_sources WHERE id = ?",
            (source.source_id,)
        )
        exists = cursor.fetchone()
        
        if exists:
            # Update existing source
            cursor.execute(
                """
                UPDATE custom_sources
                SET name = ?, description = ?, type = ?, config = ?, enabled = ?
                WHERE id = ?
                """,
                (
                    source.name,
                    source.description,
                    source.source_type,
                    json.dumps(source.config),
                    1 if source.enabled else 0,
                    source.source_id
                )
            )
        else:
            # Insert new source
            cursor.execute(
                """
                INSERT INTO custom_sources (id, name, description, type, config, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    source.source_id,
                    source.name,
                    source.description,
                    source.source_type,
                    json.dumps(source.config),
                    1 if source.enabled else 0
                )
            )
            
        conn.commit()
        conn.close()
        logger.info(f"Saved custom data source: {source.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save custom data source {source.name}: {str(e)}", exc_info=True)
        return False

def delete_custom_source(source_id):
    """Delete a custom data source from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete the source
        cursor.execute(
            "DELETE FROM custom_sources WHERE id = ?",
            (source_id,)
        )
        
        # Delete associated data
        cursor.execute(
            "DELETE FROM custom_data WHERE source_id = ?",
            (source_id,)
        )
        
        conn.commit()
        conn.close()
        logger.info(f"Deleted custom data source with ID: {source_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete custom data source {source_id}: {str(e)}", exc_info=True)
        return False

def get_custom_sources():
    """Get all custom data sources from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, name, description, type, config, enabled FROM custom_sources"
        )
        
        sources = []
        for row in cursor.fetchall():
            source_id, name, description, source_type, config_str, enabled = row
            
            try:
                config = json.loads(config_str)
            except json.JSONDecodeError:
                config = {}
                
            if source_type == "API":
                source = ApiDataSource(
                    source_id=source_id,
                    name=name,
                    description=description,
                    url=config.get("url", ""),
                    headers=config.get("headers", {}),
                    params=config.get("params", {}),
                    method=config.get("method", "GET")
                )
            elif source_type == "CSV":
                source = CsvDataSource(
                    source_id=source_id,
                    name=name,
                    description=description,
                    location=config.get("location", ""),
                    delimiter=config.get("delimiter", ","),
                    has_header=config.get("has_header", True),
                    encoding=config.get("encoding", "utf-8")
                )
            else:
                # Skip unknown source types
                continue
                
            source.enabled = bool(enabled)
            sources.append(source)
            
        conn.close()
        return sources
    except Exception as e:
        logger.error(f"Failed to get custom data sources: {str(e)}", exc_info=True)
        return []

def update_custom_source_data():
    """Update data from all enabled custom sources"""
    try:
        sources = get_custom_sources()
        
        for source in sources:
            if not source.enabled:
                continue
                
            try:
                logger.info(f"Updating data from custom source: {source.name}")
                
                # Fetch raw data
                raw_data = source.fetch_data()
                
                # Process the data
                processed_data = source.process_data(raw_data)
                
                # Store the data
                source.store_data(processed_data)
                
                logger.info(f"Successfully updated data from custom source: {source.name}")
            except Exception as e:
                logger.error(f"Failed to update data from custom source {source.name}: {str(e)}", exc_info=True)
                continue
    except Exception as e:
        logger.error(f"Failed to update custom source data: {str(e)}", exc_info=True)
