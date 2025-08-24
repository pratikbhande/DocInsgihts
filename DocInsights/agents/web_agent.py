import logging
import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from .base_agent import BaseAgent
from utils.chat_memory import ChatMemory
from processors.web_processor import WebProcessor
from prompts.analysis_prompts import WEB_ANALYSIS_PROMPT, WEB_QUERY_PROMPT

class WebAgent(BaseAgent):
    """
    Agent for processing and analyzing web content
    """
    
    def __init__(self, gemini_client, generation_config=None):
        """
        Initialize the Web agent.
        
        Args:
            gemini_client: The initialized Gemini client
            generation_config: Optional configuration for generation
        """
        super().__init__(gemini_client, generation_config)
        self.processor = WebProcessor()
        self.web_contents = {}  # Store processed web contents
        self.content_chunks = {}  # Store content chunks for context
        logging.info("WebAgent initialized")
    
    def analyze_document(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """
        Analyze an HTML document or text file.
        
        Args:
            file_path: Path to the HTML file
            file_name: Original name of the document
            
        Returns:
            Dictionary containing analysis results
        """
        logging.info(f"Analyzing web document: {file_name}")
        
        try:
            # Process the file as a web document
            doc_info, doc_content, doc_chunks = self.processor.process_file(file_path)
            
            # Store document info
            self.web_contents[file_path] = {
                "file_name": file_name,
                "doc_info": doc_info,
                "doc_content": doc_content[:1000]  # Store a sample for context
            }
            
            # Store document chunks for retrieval
            self.content_chunks[file_path] = doc_chunks
            
            # Generate analysis of the document
            analysis_prompt = WEB_ANALYSIS_PROMPT.format(
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
            error_msg = f"Error analyzing web document {file_name}: {str(e)}"
            logging.error(error_msg)
            return {"error": error_msg}
    
    def process_query(self, query: str, chat_memory: ChatMemory) -> str:
        """
        Process a user query about web content, including fetching new URLs if needed.
        
        Args:
            query: The user's query string
            chat_memory: Chat memory object with conversation history
            
        Returns:
            The response string
        """
        logging.info(f"Processing web query: {query}")
        
        try:
            # Check if the query includes a URL
            url_match = re.search(r'https?://[^\s]+', query)
            
            # If a URL is found, process it
            if url_match:
                url = url_match.group(0)
                logging.info(f"URL found in query: {url}")
                
                # Process the URL
                doc_info, doc_content, doc_chunks = self.processor.process_url(url)
                
                # Store document info
                file_path = f"web_{hash(url)}"
                self.web_contents[file_path] = {
                    "file_name": url,
                    "doc_info": doc_info,
                    "doc_content": doc_content[:1000]  # Store a sample for context
                }
                
                # Store document chunks for retrieval
                self.content_chunks[file_path] = doc_chunks
                
                # Generate initial analysis
                analysis_prompt = WEB_ANALYSIS_PROMPT.format(
                    file_name=url,
                    doc_info=json.dumps(doc_info, indent=2),
                    doc_content=doc_content[:5000]  # Use a larger sample for analysis
                )
                
                initial_analysis = self.generate_response(analysis_prompt)
                
                # Now process the actual query
                relevant_chunks = self._retrieve_relevant_chunks(query, doc_chunks)
                
                # Build the query prompt
                query_prompt = WEB_QUERY_PROMPT.format(
                    query=query,
                    url=url,
                    doc_info=json.dumps(doc_info, indent=2),
                    relevant_chunks="\n".join(relevant_chunks),
                    initial_analysis=initial_analysis,
                    chat_history=""  # No relevant chat history yet for a new URL
                )
                
                # Generate response
                response = self.generate_response(query_prompt)
                return response
            
            # If no URL is found, use existing web content if available
            elif self.web_contents:
                # Use the most recently added web content
                file_path = list(self.web_contents.keys())[-1]
                url = self.web_contents[file_path]["file_name"]
                doc_info = self.web_contents[file_path]["doc_info"]
                doc_chunks = self.content_chunks[file_path]
                
                # Get chat history for context
                chat_history = chat_memory.get_formatted_history(max_messages=5)
                
                # Find relevant chunks based on the query
                relevant_chunks = self._retrieve_relevant_chunks(query, doc_chunks)
                
                # Build the query prompt
                query_prompt = WEB_QUERY_PROMPT.format(
                    query=query,
                    url=url,
                    doc_info=json.dumps(doc_info, indent=2),
                    relevant_chunks="\n".join(relevant_chunks),
                    initial_analysis="",  # No need for initial analysis
                    chat_history=chat_history
                )
                
                # Generate response
                response = self.generate_response(query_prompt)
                return response
            
            else:
                return "Please provide a URL to analyze, or upload a web document first."
                
        except Exception as e:
            error_msg = f"Error processing web query: {str(e)}"
            logging.error(error_msg)
            return f"I encountered an error while processing your query: {str(e)}"
    
    def _retrieve_relevant_chunks(self, query: str, doc_chunks: List[str], num_chunks: int = 5) -> List[str]:
        """
        Retrieve the most relevant content chunks for a query.
        
        Args:
            query: The user's query string
            doc_chunks: List of content chunks
            num_chunks: Number of chunks to retrieve
            
        Returns:
            List of relevant content chunks
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
