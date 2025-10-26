"""
Simplified Embedding Service for GitLab ChatBot
Handles text chunking and embedding generation using Google Gemini
"""

import asyncio
import random
import time
from typing import List, Dict, Any
from datetime import datetime
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
from google.genai import types
from app.models.database import EmbeddingRecord
from app.services.database_service import DatabaseService
from app.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingService:
    """Simplified service for generating embeddings with rate limiting"""
    
    def __init__(self, database_service: DatabaseService):
        self.db_service = database_service
        self.client = None
        self.text_splitter = None
        self._initialized = False
        self._request_semaphore = None
        self._last_request_time = 0
    
    def _ensure_initialized(self):
        """Initialize components only when needed"""
        if self._initialized:
            return
            
        try:
            # Initialize Google Gemini client using settings
            if not settings.gemini_api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required")
            
            # Configure the Gemini client
            self.client = genai.Client(api_key=settings.gemini_api_key)
            
            # Initialize text splitter using settings
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
                separators=["\n\n", "\n", ".", "!", "?", " ", ""]
            )
            
            # Initialize rate limiting semaphore
            self._request_semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
            
            self._initialized = True
            logger.info("Embedding service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            raise
    
    async def _rate_limit_delay(self):
        """Ensure proper delay between API requests"""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < settings.api_delay:
            delay_needed = settings.api_delay - time_since_last_request
            logger.debug(f"Rate limiting: waiting {delay_needed:.2f} seconds")
            await asyncio.sleep(delay_needed)
        
        self._last_request_time = time.time()
    
    async def _exponential_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        base_delay = settings.retry_delay
        max_delay = 60.0  # Maximum delay of 60 seconds
        
        # Exponential backoff: base_delay * (2^attempt)
        delay = min(base_delay * (2 ** attempt), max_delay)
        
        # Add jitter (±25% random variation)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        final_delay = max(0.1, delay + jitter)
        
        logger.info(f"Exponential backoff: attempt {attempt + 1}, waiting {final_delay:.2f} seconds")
        return final_delay
    
    async def _make_api_request_with_retry(self, text: str) -> List[float]:
        """Make API request with retry logic and rate limiting"""
        for attempt in range(settings.max_retries + 1):
            try:
                # Rate limiting delay
                await self._rate_limit_delay()
                
                # Use semaphore to limit concurrent requests
                async with self._request_semaphore:
                    # Make the API request
                    def generate_embedding_sync():
                        result = self.client.models.embed_content(
                            model=settings.gemini_embedding_model,
                            contents=text,
                            config=types.EmbedContentConfig(output_dimensionality=settings.gemini_embedding_dimensions)
                        )
                        [embedding_obj] = result.embeddings
                        return embedding_obj.values
                    
                    embedding = await asyncio.to_thread(generate_embedding_sync)
                    return embedding
                    
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                    if attempt < settings.max_retries:
                        delay = await self._exponential_backoff_delay(attempt)
                        logger.warning(f"Rate limit hit (attempt {attempt + 1}/{settings.max_retries + 1}): {e}")
                        logger.info(f"Retrying after {delay:.2f} seconds...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {settings.max_retries} retries: {e}")
                        raise
                else:
                    # Non-rate-limit error, don't retry
                    logger.error(f"API request failed: {e}")
                    raise
        
        # This should never be reached, but just in case
        raise Exception("Max retries exceeded")
    
    async def generate_embeddings_for_all_content(self) -> Dict[str, Any]:
        """
        Generate embeddings for all content that doesn't already have embeddings
        
        Returns:
            Dictionary with processing results
        """
        try:
            # Initialize components when needed
            self._ensure_initialized()
            
            # Get all content records
            all_content = await self.db_service.get_all_content()
            if not all_content:
                return {"success": False, "error": "No content found in database"}
            
            processed_count = 0
            skipped_count = 0
            failed_count = 0
            
            logger.info(f"Starting embedding generation for {len(all_content)} content records")
            
            for content in all_content:
                try:
                    # Check if embeddings already exist for this content
                    existing_embeddings = await self.db_service.get_embeddings_by_content_id(content["id"])
                    if existing_embeddings:
                        skipped_count += 1
                        logger.info(f"Skipping content {content['id']} - embeddings already exist")
                        continue
                    
                    # Generate embeddings for this content
                    result = await self._generate_embeddings_for_content(content)
                    if result["success"]:
                        processed_count += 1
                        logger.info(f"Processed content {content['id']}: {result['message']}")
                    else:
                        failed_count += 1
                        logger.error(f"Failed to process content {content['id']}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error processing content {content['id']}: {e}")
                    continue
            
            return {
                "success": True,
                "total_content": len(all_content),
                "processed": processed_count,
                "skipped": skipped_count,
                "failed": failed_count,
                "message": f"Processed {processed_count}, skipped {skipped_count}, failed {failed_count} content records"
            }
            
        except Exception as e:
            logger.error(f"Error in batch embedding generation: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_embeddings_for_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate embeddings for a specific content record
        
        Args:
            content_data: Content record from database
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Get URL data for metadata
            url_data = await self.db_service.get_url_by_id(content_data["url_id"])
            if not url_data:
                return {"success": False, "error": f"URL data for content {content_data['id']} not found"}
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(content_data["content"])
            total_chunks = len(chunks)
            
            logger.info(f"Processing {total_chunks} chunks for content {content_data['id']}")
            
            # Generate embeddings for each chunk
            embedding_records = []
            for i, chunk in enumerate(chunks):
                try:
                    # Generate embedding
                    embedding = await self._generate_embedding(chunk)
                    
                    # Create metadata
                    metadata = {
                        "source": url_data["url"],
                        "title": content_data.get("title", ""),
                        "chunk_index": i,
                        "total_chunks": total_chunks,
                        "timestamp": datetime.now().isoformat(),
                        "text": chunk,
                        "content_id": content_data["id"],
                        "url_id": content_data["url_id"]
                    }
                    
                    # Create embedding record
                    embedding_record = EmbeddingRecord(
                        content_id=content_data["id"],
                        chunk_index=i,
                        total_chunks=total_chunks,
                        text=chunk,
                        embedding=embedding,
                        metadata=metadata
                    )
                    
                    embedding_records.append(embedding_record)
                    
                except Exception as e:
                    logger.error(f"Failed to generate embedding for chunk {i}: {e}")
                    continue
            
            # Save embeddings to database
            saved_count = 0
            for record in embedding_records:
                try:
                    await self.db_service.save_embedding(record)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Failed to save embedding: {e}")
                    continue
            
            return {
                "success": True,
                "content_id": content_data["id"],
                "total_chunks": total_chunks,
                "saved_embeddings": saved_count,
                "message": f"Successfully processed {saved_count}/{total_chunks} chunks"
            }
            
        except Exception as e:
            logger.error(f"Error generating embeddings for content {content_data['id']}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text chunk using gemini-embedding-001
        with rate limiting and retry logic
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            # Ensure components are initialized
            self._ensure_initialized()
            
            # Use the rate-limited API request method
            embedding = await self._make_api_request_with_retry(text)
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise