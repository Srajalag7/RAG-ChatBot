"""
Simplified Embedding Controller for GitLab ChatBot API
Single endpoint to generate embeddings for all content
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.services.database_service import database_service
from app.services.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/embeddings", tags=["embeddings"])

# Initialize embedding service
embedding_service = EmbeddingService(database_service)


@router.post("/generate")
async def generate_embeddings() -> Dict[str, Any]:
    """
    Generate embeddings for all content in the database that doesn't already have embeddings
    
    Returns:
        Dictionary with processing results
    """
    try:
        # Check if database is connected
        if not database_service.is_connected():
            raise HTTPException(
                status_code=500, 
                detail="Database not connected. Please check your Supabase configuration."
            )
        
        # Generate embeddings for all content
        result = await embedding_service.generate_embeddings_for_all_content()
        
        if result["success"]:
            return {
                "success": True,
                "message": "Embedding generation completed successfully",
                "data": {
                    "total_content": result["total_content"],
                    "processed": result["processed"],
                    "skipped": result["skipped"],
                    "failed": result["failed"]
                }
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Unknown error occurred")
            )
            
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))