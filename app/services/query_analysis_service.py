"""
Query Analysis Service for Multi-Query Processing
Handles splitting complex queries into sub-questions and generating expanded queries
"""

import logging
import json
from typing import Dict, List, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from app.config.settings import settings
from app.models.schemas import QueryAnalysisResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryAnalysisService:
    """Service for analyzing and expanding user queries"""
    
    def __init__(self):
        self.llm = None
        self.parser = None
        self.prompt = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Initialize LangChain components"""
        if self._initialized:
            return
            
        try:
            if not settings.gemini_api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required")
            
            # Initialize LangChain LLM
            self.llm = ChatGoogleGenerativeAI(
                model=settings.query_analysis_model,
                google_api_key=settings.gemini_api_key,
                temperature=settings.query_analysis_temperature,
                max_output_tokens=settings.query_analysis_max_tokens
            )
            
            # Initialize Pydantic output parser
            self.parser = PydanticOutputParser(pydantic_object=QueryAnalysisResult)
            
            # Import the prompt from prompts folder
            from prompts.multi_query_prompt import MULTI_QUERY_PROMPT
            
            # Create prompt template using the prompt from prompts folder
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", MULTI_QUERY_PROMPT),
                ("human", "User question: {user_query}")
            ])
            
            self._initialized = True
            logger.info("Query analysis service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize query analysis service: {e}")
            raise
    
    async def analyze_query(self, user_query: str) -> Dict[str, Any]:
        """
        Analyze user query and split into sub-questions with expanded queries
        
        Args:
            user_query: The user's original question
            
        Returns:
            Dictionary containing main query and sub-questions with expanded queries
        """
        try:
            self._ensure_initialized()
            
            # Create the chain with structured output
            chain = self.prompt | self.llm | self.parser
            
            # Generate structured response
            result = chain.invoke({
                "user_query": user_query,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Print the raw LLM response for debugging in JSON format
            print("=" * 50)
            print("FIRST PROMPT CALL RESPONSE (Query Analysis):")
            print("=" * 50)
            print(json.dumps(result.model_dump(), indent=4, ensure_ascii=False))
            print("=" * 50)
            
            # Convert Pydantic model to dictionary
            result_dict = result.model_dump()
            logger.info(f"Successfully analyzed query: {len(result_dict.get('sub_questions', []))} sub-questions found")
            return result_dict
                
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            # Fallback: return original query as single sub-question
            return {
                "main_query": user_query,
                "sub_questions": [
                    {
                        "question": user_query,
                        "expanded_queries": [user_query]
                    }
                ]
            }
    
    def get_all_expanded_queries(self, analysis_result: Dict[str, Any]) -> List[str]:
        """
        Extract all expanded queries from the analysis result
        
        Args:
            analysis_result: Result from analyze_query method
            
        Returns:
            List of all expanded queries
        """
        all_queries = []
        
        for sub_question in analysis_result.get("sub_questions", []):
            expanded_queries = sub_question.get("expanded_queries", [])
            all_queries.extend(expanded_queries)
        
        # Remove duplicates while preserving order
        unique_queries = []
        seen = set()
        for query in all_queries:
            if query not in seen:
                unique_queries.append(query)
                seen.add(query)
        
        return unique_queries
