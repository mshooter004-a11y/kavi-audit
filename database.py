# database.py
"""
Database layer for KaviAudit using SQLite.
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, db_path: str = "kaviaudit.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """Initialize the database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create licenses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS licenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create audit_runs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT,
                    total_records INTEGER,
                    flagged_records INTEGER
                )
            ''')
            
            # Create records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_run_id INTEGER,
                    row_data TEXT,
                    hash_value TEXT,
                    FOREIGN KEY (audit_run_id) REFERENCES audit_runs (id)
                )
            ''')
            
            # Create exceptions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exceptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id INTEGER,
                    exception_type TEXT,
                    severity INTEGER,
                    description TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (record_id) REFERENCES records (id)
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def save_record(self, audit_run_id: int, row_data: str, hash_value: str) -> int:
        """Save a record to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO records (audit_run_id, row_data, hash_value) VALUES (?, ?, ?)",
                (audit_run_id, row_data, hash_value)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_exceptions(self, audit_run_id: Optional[int] = None) -> List[Tuple]:
        """Retrieve exceptions from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if audit_run_id:
                cursor.execute('''
                    SELECT e.id, e.record_id, e.exception_type, e.severity, 
                           e.description, e.timestamp, r.row_data
                    FROM exceptions e
                    JOIN records r ON e.record_id = r.id
                    WHERE r.audit_run_id = ?
                    ORDER BY e.timestamp DESC
                ''', (audit_run_id,))
            else:
                cursor.execute('''
                    SELECT e.id, e.record_id, e.exception_type, e.severity, 
                           e.description, e.timestamp, r.row_data
                    FROM exceptions e
                    JOIN records r ON e.record_id = r.id
                    ORDER BY e.timestamp DESC
                ''')
            return cursor.fetchall()
    
    def clear_all(self):
        """Clear all data from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM exceptions")
            cursor.execute("DELETE FROM records")
            cursor.execute("DELETE FROM audit_runs")
            cursor.execute("DELETE FROM licenses")
            conn.commit()
            logger.info("Database cleared successfully")