"""
Database configuration for both SQLite (local) and PostgreSQL (production)
Automatically detects environment and configures accordingly
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Optional

# Check if PostgreSQL is configured
DATABASE_URL = os.getenv('DATABASE_URL')

# Determine which database to use
USE_POSTGRESQL = DATABASE_URL is not None
DB_PATH = "radar.db"  # For SQLite fallback

if USE_POSTGRESQL:
    import psycopg2
    from psycopg2 import sql
    print("✅ PostgreSQL configured - using PostgreSQL")
else:
    print("⚠️  PostgreSQL not configured - using SQLite (local development only)")

def get_db_connection():
    """Get database connection based on configuration"""
    if USE_POSTGRESQL:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

@contextmanager
def get_db_context():
    """Context manager for database connections"""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initialize database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRESQL:
            # PostgreSQL syntax
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    phone TEXT PRIMARY KEY,
                    api_id INTEGER NOT NULL,
                    api_hash TEXT NOT NULL,
                    alert_group TEXT,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS keywords (
                    id SERIAL PRIMARY KEY,
                    keyword TEXT UNIQUE NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_logs (
                    id SERIAL PRIMARY KEY,
                    message_id INTEGER,
                    group_id INTEGER,
                    phone TEXT,
                    status TEXT,
                    classification TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_enabled ON accounts(enabled)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_logs_phone ON message_logs(phone)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_logs_created ON message_logs(created_at)')
            
        else:
            # SQLite syntax
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    phone TEXT PRIMARY KEY,
                    api_id INTEGER NOT NULL,
                    api_hash TEXT NOT NULL,
                    alert_group TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT UNIQUE NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER,
                    group_id INTEGER,
                    phone TEXT,
                    status TEXT,
                    classification TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_enabled ON accounts(enabled)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_logs_phone ON message_logs(phone)')
        
        conn.commit()
        print("✅ Database tables initialized successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error initializing database: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

def execute_query(query: str, params: tuple = None, fetch: bool = False):
    """Execute a query and optionally fetch results"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            if USE_POSTGRESQL:
                results = cursor.fetchall()
                # Convert to dict-like format for compatibility
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in results]
            else:
                return cursor.fetchall()
        else:
            conn.commit()
            return cursor.rowcount
    finally:
        cursor.close()
        conn.close()

def execute_query_one(query: str, params: tuple = None):
    """Execute a query and fetch one result"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        result = cursor.fetchone()
        if result and USE_POSTGRESQL:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        return result
    finally:
        cursor.close()
        conn.close()

# Database type indicator for logging
DB_TYPE = "PostgreSQL" if USE_POSTGRESQL else "SQLite"
