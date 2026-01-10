"""
Database connection pooling for improved performance.
Uses thread-local connections to avoid connection overhead per request.
"""
import sqlite3
import threading
from typing import Optional
from contextlib import contextmanager
from backend.config import DB_PATH

__all__ = ["get_connection", "connection_context", "DatabasePool"]


class DatabasePool:
    """Thread-safe database connection pool using thread-local storage."""
    
    _local = threading.local()
    _lock = threading.Lock()
    
    @classmethod
    def get_connection(cls, db_path: str = None) -> sqlite3.Connection:
        """
        Get a database connection from the pool.
        Uses thread-local storage for thread safety.
        Reuses connections within the same thread.
        """
        path = db_path or DB_PATH
        
        # Check if we have an existing connection for this thread
        if not hasattr(cls._local, 'connections'):
            cls._local.connections = {}
        
        if path not in cls._local.connections:
            conn = sqlite3.connect(path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent performance
            conn.execute("PRAGMA journal_mode=WAL")
            # Optimize for speed
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
            conn.execute("PRAGMA temp_store=MEMORY")
            cls._local.connections[path] = conn
        
        return cls._local.connections[path]
    
    @classmethod
    @contextmanager
    def connection(cls, db_path: str = None):
        """Context manager for database connections with automatic commit/rollback."""
        conn = cls.get_connection(db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    @classmethod
    def close_all(cls):
        """Close all connections in the current thread."""
        if hasattr(cls._local, 'connections'):
            for conn in cls._local.connections.values():
                try:
                    conn.close()
                except:
                    pass
            cls._local.connections = {}


# Convenience functions
def get_connection(db_path: str = None) -> sqlite3.Connection:
    """Get a pooled database connection."""
    return DatabasePool.get_connection(db_path)


@contextmanager
def connection_context(db_path: str = None):
    """Context manager for database operations."""
    with DatabasePool.connection(db_path) as conn:
        yield conn
