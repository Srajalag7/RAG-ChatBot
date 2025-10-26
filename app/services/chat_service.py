from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.models.database import ChatRecord, ConversationRecord
from app.models.schemas import (
    ChatCreateRequest, ChatResponse, ChatListResponse, 
    ConversationRequest, ConversationResponse, ChatDetailResponse
)
from app.services.database_service import database_service
from app.services.multi_query_flow_service import multi_query_flow_service


class ChatService:
    """Service for handling chat and conversation operations"""
    
    def __init__(self):
        self.db = database_service
    
    async def create_chat(self, request: ChatCreateRequest) -> ChatResponse:
        """Create a new chat session"""
        if not self.db.is_connected():
            raise Exception("Database not connected")
        
        try:
            chat_data = {
                "title": request.title,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.db.client.table("chats").insert(chat_data).execute()
            
            if result.data and len(result.data) > 0:
                chat = result.data[0]
                return ChatResponse(
                    id=chat["id"],
                    title=chat["title"],
                    created_at=chat["created_at"],
                    updated_at=chat["updated_at"]
                )
            else:
                raise Exception("Failed to create chat")
                
        except Exception as e:
            raise Exception(f"Error creating chat: {str(e)}")
    
    async def get_chats(self, page: int = 1, per_page: int = 10) -> ChatListResponse:
        """Get all chat sessions with pagination"""
        if not self.db.is_connected():
            raise Exception("Database not connected")
        
        try:
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Get total count
            count_result = self.db.client.table("chats").select("id", count="exact").execute()
            total = count_result.count if count_result.count else 0
            
            # Get chats with pagination
            result = self.db.client.table("chats")\
                .select("*")\
                .order("updated_at", desc=True)\
                .range(offset, offset + per_page - 1)\
                .execute()
            
            chats = []
            for chat in result.data:
                chats.append(ChatResponse(
                    id=chat["id"],
                    title=chat["title"],
                    created_at=chat["created_at"],
                    updated_at=chat["updated_at"]
                ))
            
            total_pages = (total + per_page - 1) // per_page
            
            return ChatListResponse(
                chats=chats,
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages
            )
            
        except Exception as e:
            raise Exception(f"Error fetching chats: {str(e)}")
    
    async def get_chat(self, chat_id: int) -> ChatDetailResponse:
        """Get a specific chat with its conversations"""
        if not self.db.is_connected():
            raise Exception("Database not connected")
        
        try:
            # Get chat details
            chat_result = self.db.client.table("chats")\
                .select("*")\
                .eq("id", chat_id)\
                .execute()
            
            if not chat_result.data or len(chat_result.data) == 0:
                raise Exception("Chat not found")
            
            chat = chat_result.data[0]
            
            # Get conversations
            conversations_result = self.db.client.table("conversations")\
                .select("*")\
                .eq("chat_id", chat_id)\
                .order("conversation_order")\
                .execute()
            
            conversations = []
            for conv in conversations_result.data:
                conversations.append(ConversationResponse(
                    id=conv["id"],
                    chat_id=conv["chat_id"],
                    user_query=conv["user_query"],
                    bot_response=conv["bot_response"],
                    conversation_order=conv["conversation_order"],
                    created_at=conv["created_at"]
                ))
            
            return ChatDetailResponse(
                id=chat["id"],
                title=chat["title"],
                created_at=chat["created_at"],
                updated_at=chat["updated_at"],
                conversations=conversations,
                total_conversations=len(conversations)
            )
            
        except Exception as e:
            raise Exception(f"Error fetching chat: {str(e)}")
    
    async def send_message(self, chat_id: int, request: ConversationRequest) -> ConversationResponse:
        """Send a message in a chat and get bot response"""
        if not self.db.is_connected():
            raise Exception("Database not connected")
        
        try:
            # Check if chat exists
            chat_result = self.db.client.table("chats")\
                .select("id")\
                .eq("id", chat_id)\
                .execute()
            
            if not chat_result.data or len(chat_result.data) == 0:
                raise Exception("Chat not found")
            
            # Get current conversation count
            count_result = self.db.client.table("conversations")\
                .select("id", count="exact")\
                .eq("chat_id", chat_id)\
                .execute()
            
            current_count = count_result.count if count_result.count else 0
            
            # Check if we've reached the limit of 10 conversations
            if current_count >= 10:
                raise Exception("Maximum of 10 conversations per chat reached")
            
            # Get chat history for context
            history_result = self.db.client.table("conversations")\
                .select("user_query", "bot_response")\
                .eq("chat_id", chat_id)\
                .order("conversation_order")\
                .execute()
            
            # Build chat history string
            chat_history = ""
            for conv in history_result.data:
                chat_history += f"User: {conv['user_query']}\nBot: {conv['bot_response']}\n\n"
            
            # Get bot response using the multi-query flow service
            response = await multi_query_flow_service.process_user_query(
                user_query=request.query,
                chat_history=chat_history
            )
            
            # Save the conversation
            conversation_data = {
                "chat_id": chat_id,
                "user_query": request.query,
                "bot_response": response.get("response", "Sorry, I couldn't generate a response."),
                "conversation_order": current_count + 1,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            conversation_result = self.db.client.table("conversations")\
                .insert(conversation_data)\
                .execute()
            
            # Update chat's updated_at timestamp
            self.db.client.table("chats")\
                .update({"updated_at": datetime.now(timezone.utc).isoformat()})\
                .eq("id", chat_id)\
                .execute()
            
            if conversation_result.data and len(conversation_result.data) > 0:
                conv = conversation_result.data[0]
                return ConversationResponse(
                    id=conv["id"],
                    chat_id=conv["chat_id"],
                    user_query=conv["user_query"],
                    bot_response=conv["bot_response"],
                    conversation_order=conv["conversation_order"],
                    created_at=conv["created_at"]
                )
            else:
                raise Exception("Failed to save conversation")
                
        except Exception as e:
            raise Exception(f"Error sending message: {str(e)}")
    
    async def delete_chat(self, chat_id: int) -> bool:
        """Delete a chat and all its conversations"""
        if not self.db.is_connected():
            raise Exception("Database not connected")
        
        try:
            # Delete conversations first (foreign key constraint)
            self.db.client.table("conversations")\
                .delete()\
                .eq("chat_id", chat_id)\
                .execute()
            
            # Delete chat
            self.db.client.table("chats")\
                .delete()\
                .eq("id", chat_id)\
                .execute()
            
            return True
            
        except Exception as e:
            raise Exception(f"Error deleting chat: {str(e)}")


# Create singleton instance
chat_service = ChatService()