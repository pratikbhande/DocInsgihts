import logging
import os
import json
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from utils.chat_memory import ChatMemory
from processors.pdf_processor import PdfProcessor
from prompts.analysis_prompts import PDF_ANALYSIS_PROMPT, PDF_QUERY_PROMPT

class PdfAgent(BaseAgent):
    """
    Agent for processing and analyzing PDF documents
    """
    
    def __init__(self, gemini_client, generation_config=None):
        """
        Initialize the PDF agent.
        
        Args:
            gemini_client: The initialized Gemini client
            generation_config: Optional configuration for generation
        """
        super().__init__(gemini_client, generation_config)
        self.processor = PdfProcessor()
        self.documents = {}  # Store processed documents
        self.document_chunks = {}  # Store document chunks for context
        logging.info("PdfAgent initialized")
    
    def analyze_document(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """
        Analyze a PDF document and extract key information.
        
        Args:
            file_path: Path to the PDF file
            file_name: Original name of the document
            
        Returns:
            Dictionary containing analysis results
        """
        logging.info(f"Analyzing PDF document: {file_name}")
        
        try:
            # Process the PDF file
            doc_info, doc_content, doc_chunks = self.processor.process_file(file_path)
            
            # Store document info
            self.documents[file_path] = {
                "file_name": file_name,
                "doc_info": doc_info,
                "doc_content": doc_content[:1000]  # Store a sample for context
            }
            
            # Store document chunks for retrieval
            self.document_chunks[file_path] = doc_chunks
            
            # Generate analysis of the document
            analysis_prompt = PDF_ANALYSIS_PROMPT.format(
                file_name=file_name,
                doc_info=json.dumps(doc_info, indent=2),
                doc_content=doc_content[:5000]  # Use a larger sample for analysis
            )
            
            analysis = self.generate_response(analysis_prompt)
            
            # Format analysis results
            analysis_results = {
                "file_name": file_name,
                "file_path": file_path,
                "doc_info": doc_info,
                "content_sample": doc_content[:1000],
                "analysis": analysis
            }
            
            return analysis_results
            
        except Exception as e:
            error_msg = f"Error analyzing PDF document {file_name}: {str(e)}"
            logging.error(error_msg)
            return {"error": error_msg}
    
    def process_query(self, query: str, chat_memory: ChatMemory) -> str:
        """
        Process a user query about a PDF document.
        
        Args:
            query: The user's query string
            chat_memory: Chat memory object with conversation history
            
        Returns:
            The response string
        """
        logging.info(f"Processing PDF query: {query}")
        
        if not self.documents:
            return "No PDF documents have been loaded. Please upload a PDF file first."
        
        try:
            # Determine which document to use (default to most recent)
            file_path = list(self.documents.keys())[-1]
            doc_info = self.documents[file_path]["doc_info"]
            doc_chunks = self.document_chunks[file_path]
            
            # Get chat history for context
            chat_history = chat_memory.get_formatted_history(max_messages=5)
            
            # Find relevant chunks based on the query
            relevant_chunks = self._retrieve_relevant_chunks(query, doc_chunks)
            
            # Build the query prompt
            query_prompt = PDF_QUERY_PROMPT.format(
                query=query,
                doc_info=json.dumps(doc_info, indent=2),
                relevant_chunks="\n".join(relevant_chunks),
                chat_history=chat_history
            )
            
            # Generate response
            response = self.generate_response(query_prompt)
            return response
                
        except Exception as e:
            error_msg = f"Error processing PDF query: {str(e)}"
            logging.error(error_msg)
            return f"I encountered an error while processing your query: {str(e)}"
    
    def _retrieve_relevant_chunks(self, query: str, doc_chunks: List[str], num_chunks: int = 5) -> List[str]:
        """
        Retrieve the most relevant document chunks for a query.
        
        Args:
            query: The user's query string
            doc_chunks: List of document chunks
            num_chunks: Number of chunks to retrieve
            
        Returns:
            List of relevant document chunks
        """
        # If few chunks, return all
        if len(doc_chunks) <= num_chunks:
            return doc_chunks
        
        # Simple keyword-based relevance scoring
        chunks_with_scores = []
        query_terms = set(query.lower().split())
        
        for chunk in doc_chunks:
            chunk_lower = chunk.lower()
            score = sum(1 for term in query_terms if term in chunk_lower)
            chunks_with_scores.append((chunk, score))
        
        # Sort by relevance score (descending)
        chunks_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top chunks
        top_chunks = [chunk for chunk, _ in chunks_with_scores[:num_chunks]]
        
        # If no chunks matched, return some default chunks
        if not top_chunks or all(score == 0 for _, score in chunks_with_scores[:num_chunks]):
            return doc_chunks[:num_chunks]
        
        return top_chunks
