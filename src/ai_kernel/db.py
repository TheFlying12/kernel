import sqlite3
import os
import json
import time
import hashlib
from datetime import datetime

DB_PATH = os.path.expanduser("~/.ai_terminal/brain.db")

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cwd TEXT,
        shell TEXT
    )
    ''')
    
    # History table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        user_query TEXT,
        generated_command TEXT,
        inverse_command TEXT,
        exit_code INTEGER,
        command_output TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(session_id) REFERENCES sessions(id)
    )
    ''')
    
    # Cache table (Semantic Cache - MVP uses text match for now, but ready for vectors)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_hash TEXT,
        context_hash TEXT,
        query_text TEXT,
        response_text TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        hit_count INTEGER DEFAULT 0,
        UNIQUE(query_hash, context_hash)
    )
    ''')
    
    # Migration: Add columns if they don't exist (for existing DBs)
    try:
        cursor.execute('ALTER TABLE history ADD COLUMN exit_code INTEGER')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('ALTER TABLE history ADD COLUMN command_output TEXT')
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

def create_session(cwd, shell):
    """Creates a new session and returns its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sessions (cwd, shell) VALUES (?, ?)', (cwd, shell))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_latest_session_id():
    """Retrieves the ID of the most recent session, or creates one if none exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM sessions ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    if row:
        return row['id']
    return create_session(os.getcwd(), os.environ.get("SHELL", "unknown"))

def add_history(session_id, user_query, generated_command, inverse_command=None, exit_code=None, command_output=None):
    """Adds a command interaction to history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history (session_id, user_query, generated_command, inverse_command, exit_code, command_output)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session_id, user_query, generated_command, inverse_command, exit_code, command_output))
    conn.commit()
    conn.close()

def get_recent_history(limit=5):
    """Retrieves the most recent history items."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_query, generated_command, inverse_command, exit_code, command_output 
        FROM history 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    # Return in reverse order (oldest first) for context
    return [{"command": row['user_query'], "output": row['generated_command'], "inverse": row['inverse_command'], "exit_code": row['exit_code'], "stdout": row['command_output']} for row in reversed(rows)]

def get_context_hash(cwd, shell, os_name):
    """Generates a hash for the current environment context."""
    # We include OS, Shell, and CWD in the context
    # This ensures "ls" in /home is different from "ls" in /tmp
    raw = f"{cwd}|{shell}|{os_name}"
    return hashlib.sha256(raw.encode()).hexdigest()

def get_query_hash(query):
    """Generates a hash for the user query."""
    return hashlib.sha256(query.strip().lower().encode()).hexdigest()

def check_cache(query, cwd, shell, os_name):
    """
    Checks the cache for a similar query.
    For MVP, we are using Exact Match on the hash.
    In the future, we will fetch all for context_hash and do semantic comparison.
    """
    context_hash = get_context_hash(cwd, shell, os_name)
    query_hash = get_query_hash(query)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Try Exact Match first (Fastest)
    cursor.execute('''
        SELECT response_text, hit_count FROM cache 
        WHERE query_hash = ? AND context_hash = ?
    ''', (query_hash, context_hash))
    
    row = cursor.fetchone()
    if row:
        # Update hit count
        new_count = row['hit_count'] + 1
        cursor.execute('UPDATE cache SET hit_count = ? WHERE query_hash = ? AND context_hash = ?', 
                       (new_count, query_hash, context_hash))
        conn.commit()
        conn.close()
        return row['response_text']
        
    # 2. Semantic Match (Placeholder for future implementation)
    # We would fetch all queries for this context and run difflib/embeddings here.
    
    conn.close()
    return None

def cache_response(query, cwd, shell, os_name, response):
    """Caches a successful response."""
    context_hash = get_context_hash(cwd, shell, os_name)
    query_hash = get_query_hash(query)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO cache (query_hash, context_hash, query_text, response_text)
            VALUES (?, ?, ?, ?)
        ''', (query_hash, context_hash, query.strip(), response))
        conn.commit()
    except Exception as e:
        print(f"Cache write failed: {e}")
    finally:
        conn.close()
