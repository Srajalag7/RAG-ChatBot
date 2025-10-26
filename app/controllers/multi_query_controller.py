"""
Multi-Query Controller
Handles API endpoints for multi-query processing
"""

import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse
from app.services.multi_query_flow_service import MultiQueryFlowService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/multi-query", tags=["multi-query"])

# Initialize flow service
flow_service = MultiQueryFlowService()


@router.post("/process", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a user query through the multi-query pipeline
    
    Args:
        request: QueryRequest containing the user query and optional chat history
        
    Returns:
        QueryResponse with the generated response and metadata
    """
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="User query cannot be empty"
            )
        
        logger.info(f"Processing query: {request.query}")
        
        # Process the query through the flow
        result = await flow_service.process_user_query(request.query.strip(), request.chat_history)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Unknown error occurred")
            )
        
        return QueryResponse(
            success=True,
            query=request.query,
            response=result.get("response", ""),
            metadata=result.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process_query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
