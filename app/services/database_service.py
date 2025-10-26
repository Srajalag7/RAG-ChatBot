import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from supabase import create_client, Client
from supabase.client import ClientOptions

from app.config.settings import settings
from app.models.database import EmbeddingRecord


class DatabaseService:
    """Minimal database service for storing scraped data"""
    
    def __init__(self):
        self.settings = settings
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client"""
        if not self.settings.save_to_database:
            return
        
        if not self.settings.supabase_url or not self.settings.supabase_anon_key:
            print("Warning: Supabase configuration missing. Database operations disabled.")
            return
        
        try:
            self.client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_anon_key
            )
            print("Supabase client initialized successfully")
        except Exception as e:
            print(f"Error initializing Supabase client: {str(e)}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.client is not None
    
    async def save_url_with_content(self, site_name: str, url: str, depth: int, 
                                  content: str, title: str = None) -> bool:
        """Save or update a single URL with its content immediately"""
        if not self.is_connected():
            return False
        
        try:
            # Get or create site
            site_id = await self._get_or_create_site(site_name)
            if not site_id:
                return False
            
            # Check if URL already exists
            existing_url = self.client.table("scraped_urls")\
                .select("id")\
                .eq("site_id", site_id)\
                .eq("url", url)\
                .execute()
            
            if existing_url.data:
                # Update existing URL
                url_id = existing_url.data[0]["id"]
                url_data = {
                    "depth": depth,
                    "title": title,
                    "discovered_at": datetime.now().isoformat()
                }
                
                self.client.table("scraped_urls")\
                    .update(url_data)\
                    .eq("id", url_id)\
                    .execute()
            else:
                # Insert new URL
                url_data = {
                    "site_id": site_id,
                    "url": url,
                    "depth": depth,
                    "title": title,
                    "discovered_at": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat()
                }
                
                url_result = self.client.table("scraped_urls")\
                    .insert(url_data)\
                    .execute()
                
                url_id = url_result.data[0]["id"]
            
            # Handle content - update if exists, insert if new
            if content and len(content.strip()) > 0:
                # Check if content already exists for this URL
                existing_content = self.client.table("page_content")\
                    .select("id")\
                    .eq("url_id", url_id)\
                    .execute()
                
                content_data = {
                    "content": content[:self.settings.max_content_length],
                    "content_length": len(content),
                    "title": title,
                    "scraped_at": datetime.now().isoformat()
                }
                
                if existing_content.data:
                    # Update existing content
                    self.client.table("page_content")\
                        .update(content_data)\
                        .eq("url_id", url_id)\
                        .execute()
                else:
                    # Insert new content
                    content_data["url_id"] = url_id
                    content_data["created_at"] = datetime.now().isoformat()
                    
                    self.client.table("page_content")\
                        .insert(content_data)\
                        .execute()
            
            return True
            
        except Exception as e:
            print(f"Error saving URL {url}: {str(e)}")
            return False
    
    async def _get_or_create_site(self, site_name: str) -> Optional[int]:
        """Get or create site and return site_id"""
        try:
            # Check if site exists
            existing = self.client.table("sites")\
                .select("id")\
                .eq("name", site_name)\
                .execute()
            
            if existing.data:
                return existing.data[0]["id"]
            
            # Create new site
            site_data = {
                "name": site_name,
                "base_urls": [],
                "max_depth": self.settings.max_depth,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.client.table("sites")\
                .insert(site_data)\
                .execute()
            
            return result.data[0]["id"]
            
        except Exception as e:
            print(f"Error getting/creating site {site_name}: {str(e)}")
            return None
    
    async def get_url_by_id(self, url_id: int) -> Optional[Dict[str, Any]]:
        """Get URL record by ID"""
        if not self.is_connected():
            return None
        
        try:
            result = self.client.table("scraped_urls")\
                .select("*")\
                .eq("id", url_id)\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"Error getting URL {url_id}: {str(e)}")
            return None
    
    async def get_all_content(self) -> List[Dict[str, Any]]:
        """Get all content records"""
        if not self.is_connected():
            return []
        
        try:
            result = self.client.table("page_content")\
                .select("*")\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting all content: {str(e)}")
            return []
    
    async def get_embeddings_by_content_id(self, content_id: int) -> List[Dict[str, Any]]:
        """Get all embeddings for a specific content ID"""
        if not self.is_connected():
            return []
        
        try:
            result = self.client.table("embeddings")\
                .select("*")\
                .eq("content_id", content_id)\
                .order("chunk_index")\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting embeddings for content {content_id}: {str(e)}")
            return []
    
    async def save_embedding(self, embedding_record: EmbeddingRecord) -> bool:
        """Save embedding record to database with VECTOR type"""
        if not self.is_connected():
            return False
        
        try:
            # Convert embedding list to string format for VECTOR type
            embedding_str = "[" + ",".join(map(str, embedding_record.embedding)) + "]"
            
            embedding_data = {
                "content_id": embedding_record.content_id,
                "chunk_index": embedding_record.chunk_index,
                "total_chunks": embedding_record.total_chunks,
                "text": embedding_record.text,
                "embedding": embedding_str,  # VECTOR type expects string format
                "metadata": embedding_record.metadata,
                "created_at": datetime.now().isoformat()
            }
            
            result = self.client.table("embeddings")\
                .insert(embedding_data)\
                .execute()
            
            return True
            
        except Exception as e:
            print(f"Error saving embedding: {str(e)}")
            return False
    
    async def search_similar_embeddings(self, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar embeddings using vector similarity with pgvector"""
        if not self.is_connected():
            return []
        
        try:
            # Convert query embedding to string format for VECTOR type
            query_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # Use raw SQL for vector similarity search
            # This uses the cosine distance operator from pgvector
            result = self.client.rpc(
                "search_similar_embeddings",
                {
                    "query_embedding": query_str,
                    "match_limit": limit
                }
            ).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error searching similar embeddings: {str(e)}")
            # Fallback to basic search if vector search fails
            try:
                result = self.client.table("embeddings")\
                    .select("*")\
                    .limit(limit)\
                    .execute()
                
                return result.data if result.data else []
            except Exception as fallback_e:
                print(f"Error in fallback search: {str(fallback_e)}")
                return []


# Global database service instance
database_service = DatabaseService()