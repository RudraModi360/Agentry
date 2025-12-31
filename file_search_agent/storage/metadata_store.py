"""
Metadata Store - SQLite-based storage for document metadata.
Enables fast filtering, statistics, and document management.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, asdict


@dataclass
class DocumentRecord:
    """A record of an indexed document."""
    id: str
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    content_hash: str
    chunk_count: int
    indexed_at: datetime
    modified_at: Optional[datetime] = None
    title: Optional[str] = None
    author: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MetadataStore:
    """SQLite-based metadata storage for indexed documents."""
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    @property
    def document_count(self) -> int:
        """Get total document count."""
        with self._get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    
    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    file_path TEXT UNIQUE NOT NULL,
                    file_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    indexed_at TEXT NOT NULL,
                    modified_at TEXT,
                    title TEXT,
                    author TEXT,
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_file_path ON documents(file_path);
                CREATE INDEX IF NOT EXISTS idx_file_type ON documents(file_type);
                CREATE INDEX IF NOT EXISTS idx_content_hash ON documents(content_hash);
                
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    start_char INTEGER,
                    end_char INTEGER,
                    page_number INTEGER,
                    section TEXT,
                    metadata TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                );
                
                CREATE INDEX IF NOT EXISTS idx_document_id ON chunks(document_id);
                
                CREATE TABLE IF NOT EXISTS index_stats (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper handling."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def add_document(self, doc: DocumentRecord, chunk_ids: List[str]) -> None:
        """Add a document record with its chunk references."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO documents 
                (id, file_path, file_name, file_type, file_size, content_hash,
                 chunk_count, indexed_at, modified_at, title, author, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc.id,
                doc.file_path,
                doc.file_name,
                doc.file_type,
                doc.file_size,
                doc.content_hash,
                doc.chunk_count,
                doc.indexed_at.isoformat(),
                doc.modified_at.isoformat() if doc.modified_at else None,
                doc.title,
                doc.author,
                json.dumps(doc.metadata) if doc.metadata else None
            ))
    
    def get_document(self, file_path: str) -> Optional[DocumentRecord]:
        """Get a document by file path."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE file_path = ?",
                (file_path,)
            ).fetchone()
            
            if row:
                return self._row_to_document(row)
            return None
    
    def get_document_by_id(self, doc_id: str) -> Optional[DocumentRecord]:
        """Get a document by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?",
                (doc_id,)
            ).fetchone()
            
            if row:
                return self._row_to_document(row)
            return None
    
    def document_exists(self, file_path: str, content_hash: str) -> bool:
        """Check if document with same hash already exists."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT content_hash FROM documents WHERE file_path = ?",
                (file_path,)
            ).fetchone()
            
            return row is not None and row["content_hash"] == content_hash
    
    def delete_document(self, file_path: str) -> Optional[str]:
        """Delete a document and return its ID for vector cleanup."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT id FROM documents WHERE file_path = ?",
                (file_path,)
            ).fetchone()
            
            if row:
                doc_id = row["id"]
                conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
                conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                return doc_id
            return None
    
    def list_documents(
        self,
        file_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DocumentRecord]:
        """List indexed documents with optional filtering."""
        query = "SELECT * FROM documents"
        params = []
        
        if file_type:
            query += " WHERE file_type = ?"
            params.append(file_type)
        
        query += " ORDER BY indexed_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_document(row) for row in rows]
    
    def search_documents(
        self,
        query: str,
        file_types: Optional[List[str]] = None
    ) -> List[DocumentRecord]:
        """Search documents by filename or title."""
        with self._get_connection() as conn:
            sql = """
                SELECT * FROM documents 
                WHERE (file_name LIKE ? OR title LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%"]
            
            if file_types:
                placeholders = ",".join("?" * len(file_types))
                sql += f" AND file_type IN ({placeholders})"
                params.extend(file_types)
            
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_document(row) for row in rows]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get indexing statistics."""
        with self._get_connection() as conn:
            stats = {}
            
            # Total documents
            stats["total_documents"] = conn.execute(
                "SELECT COUNT(*) FROM documents"
            ).fetchone()[0]
            
            # Total chunks
            stats["total_chunks"] = conn.execute(
                "SELECT SUM(chunk_count) FROM documents"
            ).fetchone()[0] or 0
            
            # Documents by type
            rows = conn.execute("""
                SELECT file_type, COUNT(*) as count, SUM(file_size) as size
                FROM documents GROUP BY file_type
            """).fetchall()
            stats["by_type"] = {
                row["file_type"]: {
                    "count": row["count"],
                    "size": row["size"]
                }
                for row in rows
            }
            
            # Total size
            stats["total_size"] = conn.execute(
                "SELECT SUM(file_size) FROM documents"
            ).fetchone()[0] or 0
            
            # Last indexed
            row = conn.execute(
                "SELECT MAX(indexed_at) FROM documents"
            ).fetchone()
            stats["last_indexed"] = row[0] if row[0] else None
            
            return stats
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents as dictionaries."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM documents").fetchall()
            return [dict(row) for row in rows]
    
    def get_chunk_ids(self, file_path: str) -> List[str]:
        """Get all chunk IDs for a document."""
        with self._get_connection() as conn:
            doc = conn.execute(
                "SELECT id FROM documents WHERE file_path = ?",
                (file_path,)
            ).fetchone()
            
            if not doc:
                return []
            
            rows = conn.execute(
                "SELECT id FROM chunks WHERE document_id = ?",
                (doc["id"],)
            ).fetchall()
            return [row["id"] for row in rows]
    
    def get_file_type_counts(self) -> Dict[str, int]:
        """Get count of documents by file type."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT file_type, COUNT(*) as count FROM documents GROUP BY file_type"
            ).fetchall()
            return {row["file_type"]: row["count"] for row in rows}
    
    def remove_document(self, file_path: str) -> bool:
        """Remove a document from the store."""
        return self.delete_document(file_path) is not None
    
    def clear_all(self):
        """Clear all data from the store."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM chunks")
            conn.execute("DELETE FROM documents")
    
    def add_document(
        self,
        file_path: str,
        file_name: str,
        file_type: str,
        file_size: int,
        content_hash: str,
        file_hash: str,
        chunk_count: int,
        title: str = None,
        author: str = None,
        page_count: int = None,
        indexed_at: datetime = None
    ) -> str:
        """Add a document to the store and return its ID."""
        import uuid
        doc_id = str(uuid.uuid4())
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO documents 
                (id, file_path, file_name, file_type, file_size, content_hash,
                 chunk_count, indexed_at, title, author, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                file_path,
                file_name,
                file_type,
                file_size,
                content_hash,
                chunk_count,
                (indexed_at or datetime.now()).isoformat(),
                title,
                author,
                json.dumps({"file_hash": file_hash, "page_count": page_count})
            ))
        
        return doc_id
    
    def _row_to_document(self, row: sqlite3.Row) -> DocumentRecord:
        """Convert a database row to DocumentRecord."""
        return DocumentRecord(
            id=row["id"],
            file_path=row["file_path"],
            file_name=row["file_name"],
            file_type=row["file_type"],
            file_size=row["file_size"],
            content_hash=row["content_hash"],
            chunk_count=row["chunk_count"],
            indexed_at=datetime.fromisoformat(row["indexed_at"]),
            modified_at=datetime.fromisoformat(row["modified_at"]) if row["modified_at"] else None,
            title=row["title"],
            author=row["author"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None
        )
