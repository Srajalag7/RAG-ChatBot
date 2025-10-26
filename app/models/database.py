from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SiteRecord(BaseModel):
    """Database model for sites"""
    id: Optional[int] = None
    name: str
    base_urls: list[str]
    max_depth: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UrlRecord(BaseModel):
    """Database model for scraped URLs"""
    id: Optional[int] = None
    site_id: int
    url: str
    depth: int
    title: Optional[str] = None
    status_code: Optional[int] = None
    discovered_at: datetime
    created_at: Optional[datetime] = None


class ContentRecord(BaseModel):
    """Database model for page content"""
    id: Optional[int] = None
    url_id: int
    content: str
    content_length: int
    title: Optional[str] = None
    scraped_at: datetime
    created_at: Optional[datetime] = None


class ScrapingSession(BaseModel):
    """Database model for scraping sessions"""
    id: Optional[int] = None
    site_id: int
    total_urls: int
    total_content_pages: int
    max_depth: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "in_progress"  # in_progress, completed, failed


class EmbeddingRecord(BaseModel):
    """Database model for embeddings"""
    id: Optional[int] = None
    content_id: int
    chunk_index: int
    total_chunks: int
    text: str
    embedding: Optional[list[float]] = None  # Will be stored as vector in DB
    metadata: dict
    created_at: Optional[datetime] = None


class ChatRecord(BaseModel):
    """Database model for chat sessions"""
    id: Optional[int] = None
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConversationRecord(BaseModel):
    """Database model for individual conversations within a chat"""
    id: Optional[int] = None
    chat_id: int
    user_query: str
    bot_response: str
    conversation_order: int  # Order within the chat (1-10)
    created_at: Optional[datetime] = None


class DatabaseResponse(BaseModel):
    """Generic database response model"""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None
