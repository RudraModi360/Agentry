"""
Vercel Blob storage for media files (CLOUD MODE).
Provides CDN-backed storage with direct frontend access.
"""
import os
import uuid
import httpx
from typing import List, Optional, BinaryIO
from datetime import datetime

from .base import MediaStorageBase, MediaData

# Lazy import supabase for metadata storage
_supabase_client = None


def _get_supabase():
    """Get Supabase client for metadata storage."""
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if url and key:
            _supabase_client = create_client(url, key)
    return _supabase_client


class VercelBlobStorage(MediaStorageBase):
    """
    Vercel Blob storage for cloud deployment.
    Files stored in Vercel CDN, metadata in Supabase.
    """
    
    BASE_URL = "https://blob.vercel-storage.com"
    
    def __init__(self):
        self.token = os.getenv("BLOB_READ_WRITE_TOKEN")
        if not self.token:
            raise ValueError("BLOB_READ_WRITE_TOKEN must be set in CLOUD MODE")
        self.supabase = _get_supabase()
    
    async def upload(self, filename: str, file: BinaryIO,
                    content_type: str, user_id: str) -> MediaData:
        """Upload a media file to Vercel Blob."""
        # Generate unique path with user namespace
        ext = os.path.splitext(filename)[1]
        unique_name = f"{uuid.uuid4().hex}{ext}"
        blob_path = f"{user_id}/{unique_name}"
        
        # Read file content
        content = file.read()
        
        # Upload to Vercel Blob
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.BASE_URL}/{blob_path}",
                content=content,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": content_type,
                    "x-api-version": "7",
                    "x-content-type": content_type,
                }
            )
            
            if response.status_code not in (200, 201):
                raise Exception(f"Blob upload failed: {response.status_code} - {response.text}")
            
            blob_data = response.json()
        
        url = blob_data.get("url", f"https://blob.vercel-storage.com/{blob_path}")
        now = datetime.now()
        
        # Store metadata in Supabase
        media_id = str(uuid.uuid4())
        if self.supabase:
            try:
                result = self.supabase.table("user_media").insert({
                    "id": media_id,
                    "user_id": user_id,
                    "filename": filename,
                    "blob_url": url,
                    "blob_pathname": blob_data.get("pathname", blob_path),
                    "content_type": content_type,
                    "size_bytes": len(content),
                }).execute()
                
                if result.data:
                    media_id = result.data[0].get("id", media_id)
            except Exception as e:
                print(f"[BlobStorage] Failed to save metadata: {e}")
        
        return MediaData(
            id=media_id,
            user_id=user_id,
            filename=filename,
            url=url,
            content_type=content_type,
            created_at=now
        )
    
    async def delete(self, media_id: str, user_id: str) -> bool:
        """Delete a media file from Vercel Blob."""
        # Get blob URL from Supabase
        blob_url = None
        if self.supabase:
            try:
                result = self.supabase.table("user_media") \
                    .select("blob_url, user_id") \
                    .eq("id", media_id) \
                    .single() \
                    .execute()
                
                if result.data:
                    # Verify ownership
                    if str(result.data.get("user_id")) != str(user_id):
                        return False
                    blob_url = result.data.get("blob_url")
            except Exception as e:
                print(f"[BlobStorage] Failed to get metadata: {e}")
                return False
        
        if not blob_url:
            return False
        
        # Delete from Vercel Blob
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    "DELETE",
                    f"{self.BASE_URL}/delete",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json",
                    },
                    json={"urls": [blob_url]}
                )
                
                if response.status_code not in (200, 204):
                    print(f"[BlobStorage] Delete failed: {response.status_code}")
        except Exception as e:
            print(f"[BlobStorage] Delete error: {e}")
        
        # Delete metadata from Supabase
        if self.supabase:
            try:
                self.supabase.table("user_media") \
                    .delete() \
                    .eq("id", media_id) \
                    .execute()
            except Exception as e:
                print(f"[BlobStorage] Failed to delete metadata: {e}")
        
        return True
    
    async def get_user_media(self, user_id: str, limit: int = 50) -> List[MediaData]:
        """Get all media files for a user."""
        if not self.supabase:
            return []
        
        try:
            result = self.supabase.table("user_media") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            return [
                MediaData(
                    id=row["id"],
                    user_id=user_id,
                    filename=row.get("filename", ""),
                    url=row.get("blob_url", ""),
                    content_type=row.get("content_type", ""),
                    created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None
                )
                for row in result.data
            ]
        except Exception as e:
            print(f"[BlobStorage] Failed to get user media: {e}")
            return []
    
    async def get_media(self, media_id: str) -> Optional[MediaData]:
        """Get a specific media file by ID."""
        if not self.supabase:
            return None
        
        try:
            result = self.supabase.table("user_media") \
                .select("*") \
                .eq("id", media_id) \
                .single() \
                .execute()
            
            if not result.data:
                return None
            
            row = result.data
            return MediaData(
                id=row["id"],
                user_id=row.get("user_id", ""),
                filename=row.get("filename", ""),
                url=row.get("blob_url", ""),
                content_type=row.get("content_type", ""),
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None
            )
        except Exception as e:
            print(f"[BlobStorage] Failed to get media: {e}")
            return None
