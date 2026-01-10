"""
Database initialization and connection management.
Optimized with connection pooling and proper indexing.
"""
import sqlite3
from backend.config import DB_PATH
from backend.core.db_pool import DatabasePool, get_connection

__all__ = ["init_db", "get_db_connection", "DB_PATH"]


def get_db_connection() -> sqlite3.Connection:
    """Get a pooled database connection with row factory."""
    return get_connection()


def init_db():
    """Initialize the users database with required tables and indexes."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Enable WAL mode for better concurrent performance
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # User tokens (sessions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # Provider API Keys (Stored separately per provider)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_api_keys (
            user_id INTEGER,
            provider TEXT NOT NULL,
            api_key_encrypted TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, provider),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Active User Settings (Current selection)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_active_settings (
            user_id INTEGER PRIMARY KEY,
            provider TEXT NOT NULL,
            mode TEXT,
            model TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # User Media
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            content_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # MCP Configuration
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_mcp_config (
            user_id INTEGER PRIMARY KEY,
            config_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Granular Tools Disabling
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_disabled_tools (
            user_id INTEGER PRIMARY KEY,
            disabled_tools_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Agent Configuration
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_agent_config (
            user_id INTEGER PRIMARY KEY,
            agent_type TEXT DEFAULT 'default',
            mode TEXT,
            project_id TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # Check if 'endpoint' column exists in user_api_keys, if not add it
    try:
        cursor.execute("SELECT endpoint FROM user_api_keys LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE user_api_keys ADD COLUMN endpoint TEXT")

    # Check if 'tools_enabled' column exists in user_active_settings, if not add it
    try:
        cursor.execute("SELECT tools_enabled FROM user_active_settings LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE user_active_settings ADD COLUMN tools_enabled INTEGER DEFAULT 1")

    # Check if 'model_type' column exists in user_active_settings, if not add it
    try:
        cursor.execute("SELECT model_type FROM user_active_settings LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE user_active_settings ADD COLUMN model_type TEXT")

    # Create indexes for faster lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_tokens_user ON user_tokens(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_tokens_expires ON user_tokens(expires_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_media_user ON user_media(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")

    # Check if 'email' column exists in users
    try:
        cursor.execute("SELECT email FROM users LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")

    # SMTP Configuration (Single row enforced)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS smtp_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            host TEXT NOT NULL,
            port INTEGER NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            from_email TEXT,
            use_tls INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Password Resets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            email TEXT NOT NULL,
            token TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (email, token)
        )
    """)

    conn.commit()
    conn.close()
