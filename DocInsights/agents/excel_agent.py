import logging
import os
import json
import tempfile
import traceback
from typing import Dict, Any, List, Optional, Tuple
from .base_agent import BaseAgent
from utils.chat_memory import ChatMemory
from utils.code_executor import execute_python_code
from processors.excel_processor import ExcelProcessor
from prompts.analysis_prompts import EXCEL_ANALYSIS_PROMPT, EXCEL_QUERY_PROMPT, EXCEL_CODE_GENERATION_PROMPT

class ExcelAgent(BaseAgent):
    """
    Agent for processing and analyzing Excel files
    """
    
    def __init__(self, gemini_client, generation_config=None):
        """
        Initialize the Excel agent.
        
        Args:
            gemini_client: The initialized Gemini client
            generation_config: Optional configuration for generation
        """
        super().__init__(gemini_client, generation_config)
        self.processor = ExcelProcessor()
        self.current_file = None
        self.file_metadata = {}
        self.data_samples = {}
        logging.info("ExcelAgent initialized")
    
    def analyze_document(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """
        Analyze an Excel document and extract key information.
        
        Args:
            file_path: Path to the Excel file
            file_name: Original name of the document
            
        Returns:
            Dictionary containing analysis results
        """
        logging.info(f"Analyzing Excel document: {file_name}")
        self.current_file = file_path
        
        try:
            # Process the Excel file to extract metadata and samples
            metadata, data_samples = self.processor.process_file(file_path)
            
            self.file_metadata[file_path] = metadata
            self.data_samples[file_path] = data_samples
            
            # Generate a Python code snippet for initial data exploration
            exploration_code = self._generate_exploration_code(file_path, metadata)
            
            # Execute the code to get initial insights
            code_execution_result = execute_python_code(exploration_code, file_path)
            
            # Format analysis results
            analysis_results = {
                "file_name": file_name,
                "file_path": file_path,
                "metadata": metadata,
                "sample_data": data_samples,
                "exploration_code": exploration_code,
                "exploration_results": code_execution_result
            }
            
            self.update_context(f"analysis_{file_name}", analysis_results)
            return analysis_results
            
        except Exception as e:
            error_msg = f"Error analyzing Excel document {file_name}: {str(e)}"
            logging.error(error_msg)
            logging.error(f"Exception traceback: {traceback.format_exc()}")
            return {"error": error_msg}
    
    def process_query(self, query: str, chat_memory: ChatMemory) -> str:
        """
        Process a user query about an Excel document.
        
        Args:
            query: The user's query string
            chat_memory: Chat memory object with conversation history
            
        Returns:
            The response string
        """
        logging.info(f"Processing Excel query: {query}")
        
        if not self.current_file:
            return "No Excel file has been loaded. Please upload a spreadsheet first."
        
        try:
            # Get file info
            file_path = self.current_file
            file_name = os.path.basename(file_path)
            metadata = self.file_metadata.get(file_path, {})
            data_samples = self.data_samples.get(file_path, {})
            
            # Get chat history for context
            chat_history = chat_memory.get_formatted_history(max_messages=5)
            
            # Check if query specifically asks for visualization
            visualization_keywords = ["visualize", "visualization", "chart", "graph", "plot", "figure", "diagram"]
            if any(keyword in query.lower() for keyword in visualization_keywords) or "show me" in query.lower():
                # Generate visualization code directly
                return self._handle_visualization_query(query, file_path, metadata, data_samples, chat_history)
            
            # Determine if we need to generate code for this query
            code_generation_prompt = EXCEL_CODE_GENERATION_PROMPT.format(
                query=query,
                file_metadata=json.dumps(metadata, indent=2),
                data_samples=json.dumps(data_samples, indent=2),
                chat_history=chat_history
            )
            
            needs_code_response = self.generate_response(code_generation_prompt)
            
            if "YES" in needs_code_response.upper():
                # Generate Python code to answer the query
                code_prompt = f"""
                Generate Python code to analyze the Excel file and answer this query: "{query}"
                
                File metadata:
                {json.dumps(metadata, indent=2)}
                
                Sample data:
                {json.dumps(data_samples, indent=2)}
                
                The file is available at: {file_path}
                
                Generate complete, runnable Python code that:
                1. Loads the data using pandas
                2. Performs the necessary analysis
                3. Creates appropriate visualizations if needed
                4. Returns a comprehensive answer
                
                Only return the Python code without any markdown formatting like ```python or ```. 
                Just provide the plain Python code.
                """
                
                generated_code = self.generate_response(code_prompt)
                
                # Execute the generated code
                execution_result = execute_python_code(generated_code, file_path)
                
                # Format the final response with both the code and its results
                query_prompt = EXCEL_QUERY_PROMPT.format(
                    query=query,
                    file_metadata=json.dumps(metadata, indent=2),
                    chat_history=chat_history,
                    generated_code=generated_code,
                    code_execution_result=execution_result
                )
                
                final_response = self.generate_response(query_prompt)
                
                # Save the generated code and results in context for future reference
                self.update_context(f"last_code_{file_name}", generated_code)
                self.update_context(f"last_result_{file_name}", execution_result)
                
                return final_response
            
            else:
                # Direct query without code generation
                query_prompt = EXCEL_QUERY_PROMPT.format(
                    query=query,
                    file_metadata=json.dumps(metadata, indent=2),
                    chat_history=chat_history,
                    generated_code="",
                    code_execution_result=""
                )
                
                return self.generate_response(query_prompt)
                
        except Exception as e:
            error_msg = f"Error processing Excel query: {str(e)}"
            logging.error(error_msg)
            logging.error(f"Exception traceback: {traceback.format_exc()}")
            return f"I encountered an error while processing your query: {str(e)}"
            
    def _handle_visualization_query(self, query: str, file_path: str, metadata: Dict[str, Any], 
                                 data_samples: Dict[str, Any], chat_history: str) -> str:
        """
        Handle a query that specifically asks for visualization.
        
        Args:
            query: The user's query string
            file_path: Path to the data file
            metadata: Metadata about the file
            data_samples: Sample data from the file
            chat_history: Chat history for context
            
        Returns:
            Response with visualization results
        """
        try:
            # Extract column information from metadata
            columns = []
            column_types = {}
            
            if "columns" in metadata:
                columns = metadata["columns"]
                
                # Try to infer column types
                if "dtypes" in metadata:
                    for col, dtype in metadata["dtypes"].items():
                        if "float" in str(dtype) or "int" in str(dtype) or "number" in str(dtype):
                            column_types[col] = "numeric"
                        elif "date" in str(dtype) or "time" in str(dtype):
                            column_types[col] = "datetime"
                        else:
                            column_types[col] = "categorical"
            
            # If we have sheets info
            elif "sheets_info" in metadata:
                for sheet_name, sheet_info in metadata["sheets_info"].items():
                    if "columns" in sheet_info:
                        columns = sheet_info["columns"]
                        
                        # Try to infer column types
                        if "dtypes" in sheet_info:
                            for col, dtype in sheet_info["dtypes"].items():
                                if "float" in str(dtype) or "int" in str(dtype) or "number" in str(dtype):
                                    column_types[col] = "numeric"
                                elif "date" in str(dtype) or "time" in str(dtype):
                                    column_types[col] = "datetime"
                                else:
                                    column_types[col] = "categorical"
                        
                        break  # Just use the first sheet for now
            
            # Generate a visualization prompt
            viz_prompt = f"""
            Generate Python code to create a visualization for this query: "{query}"
            
            File: {file_path}
            
            Columns available: {columns}
            Column types: {column_types}
            
            Generate code that:
            1. Loads the data properly
            2. Creates a clear, informative visualization based on the query
            3. Uses proper titles, labels, and styling
            4. Saves the visualization to a file
            5. Prints a description of what the visualization shows
            
            Return only Python code, no explanations or formatting.
            """
            
            # Generate the visualization code
            viz_code = self.generate_response(viz_prompt)
            
            # Execute the code
            execution_result = execute_python_code(viz_code, file_path)
            
            # Extract any image paths from the execution result
            image_paths = []
            import re
            patterns = [
                r'saved (?:to )?([\w\._/-]+\.(?:png|jpg|jpeg|svg|pdf))',
                r'saved (?:as )?([\w\._/-]+\.(?:png|jpg|jpeg|svg|pdf))',
                r'saved ([\w\._/-]+\.(?:png|jpg|jpeg|svg|pdf))'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, execution_result, re.IGNORECASE)
                for match in matches:
                    # Clean up the path
                    path = match.strip()
                    # Check if it's a relative or absolute path
                    if not os.path.isabs(path):
                        path = os.path.abspath(path)
                    if os.path.exists(path):
                        image_paths.append(path)
            
            # Also check the current directory for newly created images
            try:
                import os
                import time
                current_dir = os.getcwd()
                for file in os.listdir(current_dir):
                    if file.endswith(('.png', '.jpg', '.jpeg', '.svg', '.pdf')):
                        file_path = os.path.join(current_dir, file)
                        file_mtime = os.path.getmtime(file_path)
                        if time.time() - file_mtime < 60:  # Created in the last minute
                            image_paths.append(file_path)
            except Exception as e:
                logging.warning(f"Error checking for image files: {e}")
            
            # Format the response
            response = f"Based on your request for visualization of the data, I've created the following:\n\n"
            
            # Add execution results
            if execution_result:
                # Clean up the output
                clean_result = execution_result.replace("File loaded as Excel", "").replace("File loaded as CSV", "")
                clean_result = re.sub(r"Data loaded successfully with shape:.*\n", "", clean_result)
                response += f"{clean_result}\n\n"
            
            # Add image references if found
            if image_paths:
                response += "The visualization has been generated and saved to the following file(s):\n"
                for path in image_paths:
                    response += f"- {os.path.basename(path)}\n"
            else:
                response += "I attempted to create a visualization but couldn't generate any image files. "
                response += "Please see the output above for any error messages or insights."
            
            return response
            
        except Exception as e:
            error_msg = f"Error creating visualization: {str(e)}"
            logging.error(error_msg)
            logging.error(f"Exception traceback: {traceback.format_exc()}")
            return f"I encountered an error while trying to create a visualization: {str(e)}"
            
    def _generate_exploration_code(self, file_path: str, metadata: Dict[str, Any]) -> str:
        """
        Generate Python code for initial data exploration.
        
        Args:
            file_path: Path to the Excel file
            metadata: Metadata about the Excel file
            
        Returns:
            Python code string for exploration
        """
        prompt = EXCEL_ANALYSIS_PROMPT.format(
            file_path=file_path,
            metadata=json.dumps(metadata, indent=2)
        )
        
        exploration_code = self.generate_response(prompt)
        
        # Ensure the code is formatted correctly
        if not exploration_code.strip().startswith("import"):
            exploration_code = self._generate_default_exploration_code(file_path)
        
        return exploration_code