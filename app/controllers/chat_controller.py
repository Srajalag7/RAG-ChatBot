"""
Chat Controller
Handles API endpoints for chat and conversation management
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.schemas import (
    ChatCreateRequest, ChatResponse, ChatListResponse, 
    ConversationRequest, ConversationResponse, ChatDetailResponse
)
from app.services.chat_service import chat_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/", response_model=ChatResponse)
async def create_chat(request: ChatCreateRequest):
    """
    Create a new chat session
    
    Args:
        request: ChatCreateRequest containing the chat title
        
    Returns:
        ChatResponse with the created chat details
    """
    try:
        if not request.title or not request.title.strip():
            raise HTTPException(
                status_code=400,
                detail="Chat title cannot be empty"
            )
        
        logger.info(f"Creating new chat: {request.title}")
        
        chat = await chat_service.create_chat(request)
        return chat
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/", response_model=ChatListResponse)
async def get_chats(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=50, description="Items per page")
):
    """
    Get all chat sessions with pagination
    
    Args:
        page: Page number (default: 1)
        per_page: Items per page (default: 10, max: 50)
        
    Returns:
        ChatListResponse with paginated chat list
    """
    try:
        logger.info(f"Fetching chats - page: {page}, per_page: {per_page}")
        
        chats = await chat_service.get_chats(page=page, per_page=per_page)
        return chats
        
    except Exception as e:
        logger.error(f"Error fetching chats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{chat_id}", response_model=ChatDetailResponse)
async def get_chat(chat_id: int):
    """
    Get a specific chat with its conversations
    
    Args:
        chat_id: ID of the chat to retrieve
        
    Returns:
        ChatDetailResponse with chat details and conversations
    """
    try:
        logger.info(f"Fetching chat: {chat_id}")
        
        chat = await chat_service.get_chat(chat_id)
        return chat
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail="Chat not found"
            )
        logger.error(f"Error fetching chat {chat_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{chat_id}/messages", response_model=ConversationResponse)
async def send_message(chat_id: int, request: ConversationRequest):
    """
    Send a message in a chat and get bot response
    
    Args:
        chat_id: ID of the chat
        request: ConversationRequest containing the user message
        
    Returns:
        ConversationResponse with the conversation details
    """
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )
        
        logger.info(f"Sending message to chat {chat_id}: {request.query}")
        
        conversation = await chat_service.send_message(chat_id, request)
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail="Chat not found"
            )
        elif "maximum" in str(e).lower() and "conversations" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        logger.error(f"Error sending message to chat {chat_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{chat_id}")
async def delete_chat(chat_id: int):
    """
    Delete a chat and all its conversations
    
    Args:
        chat_id: ID of the chat to delete
        
    Returns:
        204 No Content on success
    """
    try:
        logger.info(f"Deleting chat: {chat_id}")
        
        success = await chat_service.delete_chat(chat_id)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete chat"
            )
        
        return {"message": "Chat deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail="Chat not found"
            )
        logger.error(f"Error deleting chat {chat_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )