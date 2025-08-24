import logging
import os
import re
from typing import Dict, Any, List, Tuple
import json

class TextProcessor:
    """
    Processor for plain text files and generic text processing
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the Text processor.
        
        Args:
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logging.info("TextProcessor initialized")
    
    def process_file(self, file_path: str) -> Tuple[Dict[str, Any], str, List[str]]:
        """
        Process a text file and extract metadata, content, and chunked content.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Tuple containing (document_info, full_text, chunked_text)
        """
        logging.info(f"Processing text file: {file_path}")
        
        try:
            # Detect file type from extension
            file_extension = os.path.splitext(file_path)[1].lower()
            
            # Handle JSON files separately
            if file_extension == '.json':
                return self._process_json_file(file_path)
            
            # For all other text files, process as plain text
            with open(file_path, 'r', encoding='utf-8') as file:
                text_content = file.read()
            
            # Process the text content
            return self._process_text_content(text_content, file_path)
            
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    text_content = file.read()
                
                return self._process_text_content(text_content, file_path)
            except Exception as e:
                logging.error(f"Text processing failed with alternative encoding: {e}")
                raise
        except Exception as e:
            logging.error(f"Text processing failed: {e}")
            raise
    
    def _process_json_file(self, file_path: str) -> Tuple[Dict[str, Any], str, List[str]]:
        """
        Process a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Tuple containing (document_info, full_text, chunked_text)
        """
        try:
            # Read and parse JSON
            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
            
            # Convert to pretty-printed string
            text_content = json.dumps(json_data, indent=2)
            
            # Get structure info
            if isinstance(json_data, dict):
                structure_type = "object"
                keys = list(json_data.keys())
                top_level_items = len(keys)
            elif isinstance(json_data, list):
                structure_type = "array"
                top_level_items = len(json_data)
                keys = []
            else:
                structure_type = "primitive"
                top_level_items = 1
                keys = []
            
            # Create document info
            doc_info = {
                "file_type": "json",
                "file_path": file_path,
                "file_size_bytes": os.path.getsize(file_path),
                "structure_type": structure_type,
                "top_level_items": top_level_items,
                "keys": keys[:20] if len(keys) <= 20 else keys[:20] + ["..."]  # Limit keys list
            }
            
            # Create chunked text
            chunked_text = self._chunk_text(text_content)
            
            return doc_info, text_content, chunked_text
            
        except json.JSONDecodeError:
            logging.warning(f"Invalid JSON file: {file_path}, processing as plain text")
            return self.process_text_file(file_path)
        except Exception as e:
            logging.error(f"Error processing JSON file: {e}")
            raise
    
    def _process_text_content(self, text_content: str, source: str) -> Tuple[Dict[str, Any], str, List[str]]:
        """
        Process text content and extract metadata and chunked text.
        
        Args:
            text_content: The text content to process
            source: Source identifier (file path)
            
        Returns:
            Tuple containing (document_info, full_text, chunked_text)
        """
        # Create document info
        word_count = len(re.findall(r'\b\w+\b', text_content))
        line_count = text_content.count('\n') + 1
        
        doc_info = {
            "file_type": "text",
            "file_path": source,
            "file_size_bytes": os.path.getsize(source) if os.path.exists(source) else len(text_content),
            "word_count": word_count,
            "line_count": line_count,
            "char_count": len(text_content)
        }
        
        # Create chunked text
        chunked_text = self._chunk_text(text_content)
        
        return doc_info, text_content, chunked_text
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: The text to split into chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Calculate end position with overlap
            end = min(start + self.chunk_size, text_length)
            
            # Adjust chunk to end at a paragraph boundary if possible
            if end < text_length:
                # Look for paragraph ending within 200 characters of the end
                search_range = min(end + 200, text_length)
                paragraph_end = -1
                
                for match in re.finditer(r'\n\s*\n', text[end:search_range]):
                    paragraph_end = end + match.end()
                    break
                
                if paragraph_end != -1:
                    end = paragraph_end
            
            # Add the chunk
            chunks.append(text[start:end].strip())
            
            # Move to next chunk position, accounting for overlap
            start = end - self.chunk_overlap if end < text_length else text_length
            
            # Ensure progress is made
            if start >= end:
                start = end
        
        return chunks
