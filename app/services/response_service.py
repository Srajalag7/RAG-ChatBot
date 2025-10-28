"""
Response Service for Final LLM Response Generation
Handles generating final responses using retrieved context
"""

import logging
import json
import asyncio
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from app.config.settings import settings
from app.models.schemas import FinalResponseResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResponseService:
    """Service for generating final LLM responses"""
    
    def __init__(self):
        self.llm = None
        self.parser = None
        self.prompt = None
        self._initialized = False
        self.max_retries = 3
        self.base_delay = 1.0
    
    def _ensure_initialized(self):
        """Initialize LangChain components"""
        if self._initialized:
            return
            
        try:
            if not settings.gemini_api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required")
            
            # Initialize LangChain LLM
            self.llm = ChatGoogleGenerativeAI(
                model=settings.response_model,
                google_api_key=settings.gemini_api_key,
                temperature=settings.response_temperature,
                response_mime_type="application/json",
                max_output_tokens=settings.response_max_tokens
            )
            
            # Initialize Pydantic output parser
            self.parser = PydanticOutputParser(pydantic_object=FinalResponseResult)
            
            # Import the prompt from prompts folder
            from prompts.multi_query_prompt import FINAL_RESPONSE_PROMPT
            
            # Create prompt template using the prompt from prompts folder
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", FINAL_RESPONSE_PROMPT),
                ("human", "Context: {context}\n\nQuestion: {question}\n\nChat History: {chat_history}")
            ])
            
            self._initialized = True
            logger.info("Response service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize response service: {e}")
            raise
    
    async def _retry_llm_call(self, input_data: Dict[str, Any], attempt: int = 1) -> Any:
        """
        Retry LLM call with exponential backoff
        
        Args:
            input_data: Data to pass to the LLM
            attempt: Current attempt number
            
        Returns:
            LLM response
            
        Raises:
            Exception: If all retries fail
        """
        try:
            # Create the chain with structured output
            chain = self.prompt | self.llm | self.parser
            
            # Generate structured response
            result = chain.invoke(input_data)
            return result
            
        except Exception as e:
            if attempt >= self.max_retries:
                logger.error(f"LLM call failed after {self.max_retries} attempts: {e}")
                raise
            
            # Calculate delay with exponential backoff
            delay = self.base_delay * (2 ** (attempt - 1))
            logger.warning(f"LLM call failed (attempt {attempt}/{self.max_retries}): {e}. Retrying in {delay}s...")
            
            # Wait before retry
            await asyncio.sleep(delay)
            
            # Recursive retry
            return await self._retry_llm_call(input_data, attempt + 1)
    
    async def generate_final_response(self, user_query: str, context: str, chat_history: str = "") -> str:
        """
        Generate final response using retrieved context
        
        Args:
            user_query: The original user query
            context: Formatted context from retrieved documents
            chat_history: Previous conversation history (optional)
            
        Returns:
            Generated response string
        """
        try:
            self._ensure_initialized()
            
            # Prepare input data for LLM call
            input_data = {
                "context": context,
                "question": user_query,
                "chat_history": chat_history,
                "format_instructions": self.parser.get_format_instructions()
            }
            
            # Generate structured response with retry logic
            result = await self._retry_llm_call(input_data)

            # Print the raw LLM response for debugging in JSON format
            print("=" * 50)
            print("SECOND PROMPT CALL RESPONSE (Final Response):")
            print("=" * 50)
            print(json.dumps(result.model_dump(), indent=4, ensure_ascii=False))
            print("=" * 50)
            
            # Return the response text from the structured result
            return result.response
            
        except Exception as e:
            logger.error(f"Error generating final response: {e}")
            return f"I apologize, but I encountered an error while generating a response. Please try again."
    
    def format_context_with_sources(self, documents: List[Dict[str, Any]]) -> str:
        """
        Format documents as context with proper source attribution
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Formatted context string with sources
        """
        if not documents:
            return "No relevant context found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.get("source", "Unknown source")
            title = doc.get("title", "No title")
            text = doc.get("text", "")
               
            context_part = f"[Source {i}] {source}\nTitle: {title}\nContent: {text}\n"
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
