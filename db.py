"""
Database initialization and management module for Telegram Radar
Handles SQLite database schema creation and connection management
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

DB_PATH = "radar.db"

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db_context():
    """Context manager for database connections"""
    conn = get_db()
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
    conn = get_db()
    cursor = conn.cursor()
    
    # Create accounts table
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
    
    # Create keywords table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Create settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Create message logs table for tracking processed messages
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
    
    conn.commit()
    conn.close()

# Account Management Functions
def add_account(phone: str, api_id: int, api_hash: str, alert_group: Optional[str] = None) -> bool:
    """Add a new Telegram account"""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO accounts (phone, api_id, api_hash, alert_group, enabled)
                VALUES (?, ?, ?, ?, 1)
            ''', (phone, api_id, api_hash, alert_group))
        return True
    except sqlite3.IntegrityError:
        return False

def get_accounts() -> List[Dict[str, Any]]:
    """Get all accounts"""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts')
        return [dict(row) for row in cursor.fetchall()]

def get_enabled_accounts() -> List[Dict[str, Any]]:
    """Get only enabled accounts"""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE enabled = 1')
        return [dict(row) for row in cursor.fetchall()]

def delete_account(phone: str) -> bool:
    """Delete an account"""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM accounts WHERE phone = ?', (phone,))
        return True
    except Exception:
        return False

def toggle_account(phone: str, enabled: bool) -> bool:
    """Enable or disable an account"""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE accounts SET enabled = ? WHERE phone = ?', (enabled, phone))
        return True
    except Exception:
        return False

# Keywords Management Functions
def add_keyword(keyword: str) -> bool:
    """Add a keyword"""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO keywords (keyword) VALUES (?)', (keyword.strip(),))
        return True
    except sqlite3.IntegrityError:
        return False

def get_keywords() -> List[str]:
    """Get all keywords"""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT keyword FROM keywords ORDER BY keyword')
        return [row['keyword'] for row in cursor.fetchall()]

def delete_keyword(keyword: str) -> bool:
    """Delete a keyword"""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM keywords WHERE keyword = ?', (keyword.strip(),))
        return True
    except Exception:
        return False

def bulk_add_keywords(keywords: List[str]) -> int:
    """Add multiple keywords at once"""
    added = 0
    with get_db_context() as conn:
        cursor = conn.cursor()
        for keyword in keywords:
            try:
                cursor.execute('INSERT INTO keywords (keyword) VALUES (?)', (keyword.strip(),))
                added += 1
            except sqlite3.IntegrityError:
                continue
    return added

def clear_keywords() -> bool:
    """Clear all keywords"""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM keywords')
        return True
    except Exception:
        return False

# Settings Management Functions
def set_setting(key: str, value: str) -> bool:
    """Set a setting"""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            ''', (key, value))
        return True
    except Exception:
        return False

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a setting"""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row['value'] if row else default

def get_all_settings() -> Dict[str, str]:
    """Get all settings"""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM settings')
        return {row['key']: row['value'] for row in cursor.fetchall()}

# Message Logging Functions
def log_message(message_id: int, group_id: int, phone: str, status: str, 
                classification: Optional[str] = None, confidence: Optional[float] = None) -> bool:
    """Log a processed message"""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO message_logs (message_id, group_id, phone, status, classification, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (message_id, group_id, phone, status, classification, confidence))
        return True
    except Exception:
        return False
