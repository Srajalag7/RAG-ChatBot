import json
import os
from pathlib import Path
from typing import Dict, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Scraper Configuration
    max_depth: int = Field(default=3, alias="MAX_DEPTH")
    max_content_length: int = Field(default=100000, alias="MAX_CONTENT_LENGTH")
    
    sites_config: str = Field(
        default='{"gitlab": [{"url": "https://handbook.gitlab.com/handbook/", "enabled": true}, {"url": "https://about.gitlab.com/direction/", "enabled": true}]}',
        alias="SITES_CONFIG"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    
    # Performance Configuration
    request_timeout: int = Field(default=30, alias="REQUEST_TIMEOUT")
    request_delay: float = Field(default=1.0, alias="REQUEST_DELAY")
    
    # Supabase Database Configuration
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", alias="SUPABASE_ANON_KEY")
    save_to_database: bool = Field(default=True, alias="SAVE_TO_DATABASE")
    
    # Gemini AI Configuration
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_embedding_model: str = Field(default="gemini-embedding-001", alias="GEMINI_EMBEDDING_MODEL")
    gemini_embedding_dimensions: int = Field(default=1536, alias="GEMINI_EMBEDDING_DIMENSIONS")
    
    # LLM Configuration for Query Analysis
    query_analysis_model: str = Field(default="gemini-2.5-flash", alias="QUERY_ANALYSIS_MODEL")
    query_analysis_temperature: float = Field(default=0.1, alias="QUERY_ANALYSIS_TEMPERATURE")
    query_analysis_max_tokens: int = Field(default=2048, alias="QUERY_ANALYSIS_MAX_TOKENS")
    
    # LLM Configuration for Final Response
    response_model: str = Field(default="gemini-2.5-flash", alias="RESPONSE_MODEL")
    response_temperature: float = Field(default=0.2, alias="RESPONSE_TEMPERATURE")
    response_max_tokens: int = Field(default=4096, alias="RESPONSE_MAX_TOKENS")
    
    # Document Retrieval Configuration
    documents_per_query: int = Field(default=5, alias="DOCUMENTS_PER_QUERY")
    max_total_documents: int = Field(default=15, alias="MAX_TOTAL_DOCUMENTS")
    
    # Embedding Configuration
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, alias="CHUNK_OVERLAP")
    
    # Rate Limiting Configuration
    api_delay: float = Field(default=1.0, alias="API_DELAY")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    retry_delay: float = Field(default=2.0, alias="RETRY_DELAY")
    max_concurrent_requests: int = Field(default=1, alias="MAX_CONCURRENT_REQUESTS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    def get_sites_config(self) -> Dict[str, List[Dict[str, any]]]:
        """Parse sites configuration from JSON string"""
        try:
            return json.loads(self.sites_config)
        except json.JSONDecodeError:
            return {}
    


# Global settings instance
settings = Settings()

