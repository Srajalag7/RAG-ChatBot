"""
Multi-Query Flow Service
Orchestrates the entire multi-query processing pipeline
"""

import logging
from typing import Dict, Any, List
from app.services.query_analysis_service import QueryAnalysisService
from app.services.retrieval_service import RetrievalService
from app.services.response_service import ResponseService
from app.services.embedding_service import EmbeddingService
from app.services.database_service import DatabaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiQueryFlowService:
    """Main service for orchestrating multi-query processing"""
    
    def __init__(self):
        # Initialize all required services
        self.database_service = DatabaseService()
        self.embedding_service = EmbeddingService(self.database_service)
        self.query_analysis_service = QueryAnalysisService()
        self.retrieval_service = RetrievalService(self.embedding_service, self.database_service)
        self.response_service = ResponseService()
    
    async def process_user_query(self, user_query: str, chat_history: str = "") -> Dict[str, Any]:
        """
        Process a user query through the complete multi-query pipeline
        
        Args:
            user_query: The user's question
            chat_history: Previous conversation history (optional)
            
        Returns:
            Dictionary containing the response and metadata
        """
        try:
            logger.info(f"Processing user query: {user_query}")
            
            # Step 1: Analyze the query and split into sub-questions
            logger.info("Step 1: Analyzing query and splitting into sub-questions...")
            analysis_result = await self.query_analysis_service.analyze_query(user_query, chat_history)
            
            # If analysis fails, the query_analysis_service already provides a fallback
            # that uses the original user_query as a single sub-question
            if not analysis_result or not analysis_result.get("sub_questions"):
                logger.warning("Query analysis failed, using fallback with original query")
                analysis_result = {
                    "main_query": user_query,
                    "sub_questions": [
                        {
                            "question": user_query,
                            "expanded_queries": [user_query]
                        }
                    ]
                }
            
            logger.info(f"Found {len(analysis_result['sub_questions'])} sub-questions")
            
            # Step 2: Get all expanded queries
            all_expanded_queries = self.query_analysis_service.get_all_expanded_queries(analysis_result)
            logger.info(f"Generated {len(all_expanded_queries)} expanded queries")
            
            # Step 3: Retrieve documents for all queries
            logger.info("Step 2: Retrieving and reranking documents...")
            retrieved_documents = await self.retrieval_service.retrieve_documents_for_multiple_queries(
                all_expanded_queries,
                user_query
            )
            
            if not retrieved_documents:
                return {
                    "success": False,
                    "error": "No relevant documents found",
                    "response": "I couldn't find any relevant information in the GitLab Handbook to answer your question. Please try rephrasing your question or asking about a different topic."
                }
            
            logger.info(f"Retrieved {len(retrieved_documents)} unique documents")
            
            # Step 4: Format context for LLM
            logger.info("Step 3: Formatting context for LLM...")
            formatted_context = self.response_service.format_context_with_sources(retrieved_documents)
            
            # Step 5: Generate final response
            logger.info("Step 4: Generating final response...")
            final_response = await self.response_service.generate_final_response(
                user_query, 
                formatted_context,
                chat_history
            )
            
            # Prepare response metadata
            response_metadata = {
                "sub_questions_count": len(analysis_result.get("sub_questions", [])),
                "expanded_queries_count": len(all_expanded_queries),
                "documents_retrieved": len(retrieved_documents),
                "documents_sources": list(set(doc.get("source", "") for doc in retrieved_documents)),
                "analysis_result": analysis_result
            }
            
            logger.info("Successfully processed user query")
            
            return {
                "success": True,
                "response": final_response,
                "metadata": response_metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing user query: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error while processing your question. Please try again."
            }

multi_query_flow_service = MultiQueryFlowService()
