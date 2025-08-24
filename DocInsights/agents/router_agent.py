import logging
import os
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from .excel_agent import ExcelAgent
from .pdf_agent import PdfAgent
from .web_agent import WebAgent
from .report_agent import ReportAgent
from utils.chat_memory import ChatMemory
from prompts.router_prompts import ROUTER_SYSTEM_PROMPT, DOCUMENT_ANALYSIS_PROMPT

class RouterAgent(BaseAgent):
    """
    Router agent that directs queries to appropriate specialized agents
    and coordinates the overall system flow.
    """
    
    def __init__(self, gemini_client, generation_config=None):
        """
        Initialize the router agent.
        
        Args:
            gemini_client: The initialized Gemini client
            generation_config: Optional configuration for generation
        """
        super().__init__(gemini_client, generation_config)
        
        # Initialize specialized agents
        self.excel_agent = ExcelAgent(gemini_client, generation_config)
        self.pdf_agent = PdfAgent(gemini_client, generation_config)
        self.web_agent = WebAgent(gemini_client, generation_config)
        self.report_agent = ReportAgent(gemini_client, generation_config)
        
        # Track loaded documents
        self.documents = {}
        logging.info("RouterAgent initialized with specialized agents")
    
    def process_document(self, file_path: str, file_name: str, file_type: str) -> str:
        """
        Process a new document and perform initial analysis.
        
        Args:
            file_path: Path to the document file
            file_name: Original name of the document
            file_type: MIME type of the document
            
        Returns:
            Initial analysis of the document
        """
        logging.info(f"Processing document: {file_name} ({file_type})")
        
        # Determine document type and route to appropriate agent
        agent = self._get_agent_for_file_type(file_type)
        
        if not agent:
            error_msg = f"Unsupported file type: {file_type}"
            logging.error(error_msg)
            return error_msg
        
        # Store document info
        doc_info = {
            "path": file_path,
            "name": file_name,
            "type": file_type,
            "agent": agent.__class__.__name__
        }
        self.documents[file_name] = doc_info
        
        # Run initial analysis by the specialized agent
        try:
            analysis_results = agent.analyze_document(file_path, file_name)
            
            # Generate a user-friendly summary of the document
            summary_prompt = DOCUMENT_ANALYSIS_PROMPT.format(
                file_name=file_name,
                file_type=file_type,
                analysis_results=analysis_results
            )
            
            summary = self.generate_response(summary_prompt)
            
            # Store analysis results in context
            self.update_context(f"analysis_{file_name}", analysis_results)
            self.update_context(f"summary_{file_name}", summary)
            
            return summary
        
        except Exception as e:
            error_msg = f"Error analyzing document {file_name}: {str(e)}"
            logging.error(error_msg)
            return error_msg
    
    def process_query(self, query: str, chat_memory: ChatMemory) -> str:
        """
        Process a user query and route to appropriate specialized agent.
        
        Args:
            query: The user's query string
            chat_memory: Chat memory object with conversation history
            
        Returns:
            The response string
        """
        logging.info(f"Processing query: {query}")
        
        # If no documents have been loaded yet
        if not self.documents:
            if "http" in query.lower() or "www." in query.lower():
                # Handle web URL
                return self.web_agent.process_query(query, chat_memory)
            else:
                return "Please upload a document first to analyze it. I can also analyze web content if you provide a URL."
        
        # Get chat history for context
        chat_history = chat_memory.get_formatted_history()
        
        # Determine the intent and which agent should handle it
        routing_prompt = f"""
        {ROUTER_SYSTEM_PROMPT}
        
        Available documents: {", ".join(self.documents.keys())}
        
        Chat history:
        {chat_history}
        
        User query: {query}
        
        Determine the intent of this query and which agent should handle it.
        """
        
        routing_decision = self.generate_response(routing_prompt)
        logging.info(f"Routing decision: {routing_decision}")
        
        # Extract agent type and action from the routing decision
        if "REPORT" in routing_decision.upper():
            # Generate a comprehensive report
            return self._generate_report(query, chat_memory)
        
        elif "EXCEL" in routing_decision.upper() or "CSV" in routing_decision.upper() or "SPREADSHEET" in routing_decision.upper():
            # Find the Excel document
            excel_docs = [doc for doc in self.documents.values() if doc["agent"] == "ExcelAgent"]
            if excel_docs:
                return self.excel_agent.process_query(query, chat_memory)
            else:
                return "I don't see any spreadsheet documents loaded. Please upload an Excel or CSV file first."
        
        elif "PDF" in routing_decision.upper() or "DOCUMENT" in routing_decision.upper():
            # Find the PDF document
            pdf_docs = [doc for doc in self.documents.values() if doc["agent"] == "PdfAgent"]
            if pdf_docs:
                return self.pdf_agent.process_query(query, chat_memory)
            else:
                return "I don't see any PDF documents loaded. Please upload a PDF file first."
        
        elif "WEB" in routing_decision.upper() or "URL" in routing_decision.upper():
            return self.web_agent.process_query(query, chat_memory)
        
        else:
            # Default case: determine the most recently added document
            if self.documents:
                latest_doc = list(self.documents.values())[-1]
                agent_name = latest_doc["agent"]
                
                if agent_name == "ExcelAgent":
                    return self.excel_agent.process_query(query, chat_memory)
                elif agent_name == "PdfAgent":
                    return self.pdf_agent.process_query(query, chat_memory)
                else:
                    return "I'm not sure how to process this query. Could you please clarify what you're asking about?"
            else:
                return "Please upload a document first to analyze it."
    
    def _generate_report(self, query: str, chat_memory: ChatMemory) -> str:
        """
        Generate a comprehensive report based on analyzed documents.
        
        Args:
            query: The user's query requesting a report
            chat_memory: Chat memory object with conversation history
            
        Returns:
            Response with report
        """
        # Gather all document analyses
        analyses = {}
        for doc_name, doc_info in self.documents.items():
            analysis_key = f"analysis_{doc_name}"
            if analysis_key in self.context:
                analyses[doc_name] = self.get_context(analysis_key)
        
        # Generate the report
        report = self.report_agent.generate_report(query, analyses, chat_memory)
        
        # Format response to include the report
        response = f"""
        I've generated a comprehensive report based on your documents and query.
        
        REPORT_START
        {report}
        REPORT_END
        
        You can view and export the full report in the Reports tab. Feel free to ask if you need any clarification or have additional questions about the report.
        """
        
        return response
    
    def _get_agent_for_file_type(self, file_type: str):
        """
        Get the appropriate agent for a file type.
        
        Args:
            file_type: MIME type of the file
            
        Returns:
            The appropriate agent instance
        """
        if "spreadsheet" in file_type or "csv" in file_type or "excel" in file_type or "xlsx" in file_type or "xls" in file_type:
            return self.excel_agent
        elif "pdf" in file_type:
            return self.pdf_agent
        elif "html" in file_type or "text" in file_type:
            return self.web_agent
        else:
            # Default to PDF agent for unknown file types as it can handle text-based content
            return self.pdf_agent