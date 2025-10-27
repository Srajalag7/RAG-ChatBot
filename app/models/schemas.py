from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SiteConfig(BaseModel):
    """Configuration for a single website URL"""
    url: str
    enabled: bool = True


class ScrapeRequest(BaseModel):
    """Request model for scraping a site"""
    site_name: str = Field(..., description="Name of the site to scrape")
    max_depth: Optional[int] = Field(None, description="Override default max depth")


class ScrapeResponse(BaseModel):
    """Response model for scraping operation"""
    site_name: str
    urls_count: int
    file_path: str
    scraped_at: str
    message: str


class ScrapeStatus(BaseModel):
    """Status of scraping operation"""
    site_name: str
    status: str
    urls_found: int
    message: Optional[str] = None


class UrlData(BaseModel):
    """Model for storing URL information"""
    url: str
    discovered_at: str
    depth: int
    content: Optional[str] = None
    content_length: Optional[int] = None
    title: Optional[str] = None
    status_code: Optional[int] = None


class ScrapedDataOutput(BaseModel):
    """Model for scraped data output"""
    site_name: str
    base_urls: List[str]
    max_depth: int
    total_urls: int
    total_content_pages: int
    scraped_at: str
    urls: List[UrlData]


class ContentFile(BaseModel):
    """Model for individual content file"""
    url: str
    title: Optional[str]
    content: str
    content_length: int
    scraped_at: str
    depth: int


class AvailableSitesResponse(BaseModel):
    """Response model for available sites"""
    sites: Dict[str, List[SiteConfig]]


# Multi-Query Models
class QueryRequest(BaseModel):
    """Request model for multi-query processing"""
    query: str = Field(..., description="The user's question")
    chat_history: str = Field(default="", description="Previous conversation history (optional)")


class QueryResponse(BaseModel):
    """Response model for multi-query processing"""
    success: bool
    query: str
    response: str
    metadata: Dict[str, Any] = {}


# Pydantic Models for Structured LLM Responses
class SubQuestion(BaseModel):
    """Model for individual sub-question"""
    question: str = Field(..., description="The sub-question text")
    expanded_queries: List[str] = Field(..., description="List of expanded queries for this sub-question")


class QueryAnalysisResult(BaseModel):
    """Structured result for query analysis"""
    main_query: str = Field(..., description="The original user query")
    sub_questions: List[SubQuestion] = Field(..., description="List of sub-questions with expanded queries")


class FinalResponseResult(BaseModel):
    """Structured result for final response"""
    response: str = Field(..., description="The generated response")
    confidence: float = Field(default=1.0, description="Confidence score for the response")
    sources_used: int = Field(default=0, description="Number of sources used in the response")


# Chat Models
class ChatCreateRequest(BaseModel):
    """Request model for creating a new chat"""
    title: str = Field(..., description="Title for the new chat")


class ChatResponse(BaseModel):
    """Response model for chat operations"""
    id: int
    title: str
    created_at: str
    updated_at: str


class ChatListResponse(BaseModel):
    """Response model for listing chats"""
    chats: List[ChatResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class ConversationRequest(BaseModel):
    """Request model for sending a message in a chat"""
    query: str = Field(..., description="The user's message")


class ConversationResponse(BaseModel):
    """Response model for a conversation"""
    id: int
    chat_id: int
    user_query: str
    bot_response: str
    conversation_order: int
    created_at: str
    sources: Optional[List[str]] = Field(default=None, description="List of source URLs used in the response")


class ChatDetailResponse(BaseModel):
    """Response model for chat details with conversations"""
    id: int
    title: str
    created_at: str
    updated_at: str
    conversations: List[ConversationResponse]
    total_conversations: int


