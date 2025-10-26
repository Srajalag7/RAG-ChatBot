"""
Retrieval Service with Cohere Reranking
Handles document retrieval and reranking for multi-query processing
"""

import logging
from typing import List, Dict, Any, Optional

from app.services.embedding_service import EmbeddingService
from app.services.database_service import DatabaseService
from app.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for document retrieval"""
    
    def __init__(self, embedding_service: EmbeddingService, database_service: DatabaseService):
        self.embedding_service = embedding_service
        self.database_service = database_service
        self._initialized = False
    
    def _ensure_initialized(self):
        """Initialize retrieval service"""
        if self._initialized:
            return
            
        try:
            self._initialized = True
            logger.info("Retrieval service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize retrieval service: {e}")
            raise
    
    async def retrieve_documents_for_query(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Retrieve documents for a single query using vector similarity search
        
        Args:
            query: The search query
            limit: Maximum number of documents to return
            
        Returns:
            List of relevant documents with metadata
        """
        try:
            # Generate embedding for the query
            query_embedding = await self.embedding_service._generate_embedding(query)
            
            # Search for similar embeddings in database
            similar_embeddings = await self.database_service.search_similar_embeddings(
                query_embedding, 
                limit=limit
            )
            
            if not similar_embeddings:
                logger.warning(f"No similar embeddings found for query: {query}")
                return []
            
            # Convert to our format
            result_docs = []
            for embedding_data in similar_embeddings:
                result_docs.append({
                    "text": embedding_data.get("text", ""),
                    "metadata": embedding_data.get("metadata", {}),
                    "source": embedding_data.get("metadata", {}).get("source", ""),
                    "title": embedding_data.get("metadata", {}).get("title", ""),
                    "chunk_index": embedding_data.get("chunk_index", 0)
                })
            
            logger.info(f"Retrieved {len(result_docs)} documents for query: {query}")
            return result_docs
            
        except Exception as e:
            logger.error(f"Error retrieving documents for query '{query}': {e}")
            return []
    
    async def retrieve_documents_for_multiple_queries(self, queries: List[str], user_query: str = "") -> List[Dict[str, Any]]:
        """
        Retrieve documents for multiple queries and combine results
        
        Args:
            queries: List of search queries
            user_query: Original user query (unused, kept for compatibility)
            
        Returns:
            Top documents (max_total_documents) from all queries
        """
        try:
            self._ensure_initialized()
            
            # Step 1: Collect all documents from all queries
            all_documents = []
            
            for query in queries:
                # Get documents per query using settings
                docs = await self.retrieve_documents_for_query(query, settings.documents_per_query)
                all_documents.extend(docs)
            
            if not all_documents:
                logger.warning("No documents found for any query")
                return []
            
            # Step 2: Remove duplicates based on content
            unique_docs = []
            seen_texts = set()
            
            for doc in all_documents:
                text = doc.get("text", "")
                if text not in seen_texts:
                    unique_docs.append(doc)
                    seen_texts.add(text)
            
            # Step 3: Return top documents (limit by settings)
            result_docs = unique_docs[:settings.max_total_documents]
            
            logger.info(f"Retrieved {len(result_docs)} documents (max {settings.max_total_documents}) from {len(queries)} queries")
            return result_docs
            
        except Exception as e:
            logger.error(f"Error retrieving documents for multiple queries: {e}")
            return []
    
