import logging
import os
import io
import re
from typing import Dict, Any, List, Tuple
import PyPDF2
import pdfplumber
import numpy as np

class PdfProcessor:
    """
    Processor for PDF documents using PDFPlumber and PyPDF2
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the PDF processor.
        
        Args:
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logging.info("PdfProcessor initialized")
    
    def process_file(self, file_path: str) -> Tuple[Dict[str, Any], str, List[str]]:
        """
        Process a PDF file and extract metadata, content, and chunked content.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple containing (document_info, full_text, chunked_text)
        """
        logging.info(f"Processing PDF file: {file_path}")
        
        try:
            # Try with PDFPlumber (better text extraction)
            return self._process_with_pdfplumber(file_path)
        except Exception as e:
            logging.warning(f"PDFPlumber processing failed: {e}, falling back to PyPDF2")
            
            # Fallback to PyPDF2
            try:
                return self._process_with_pypdf2(file_path)
            except Exception as e2:
                logging.error(f"PDF processing failed with both methods: {e2}")
                raise
    
    def _process_with_pdfplumber(self, file_path: str) -> Tuple[Dict[str, Any], str, List[str]]:
        """
        Process a PDF file using PDFPlumber (better for text extraction).
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple containing (document_info, full_text, chunked_text)
        """
        # Open the PDF file
        with pdfplumber.open(file_path) as pdf:
            # Extract metadata
            metadata = pdf.metadata
            
            # Prepare document info
            doc_info = {
                "title": metadata.get("Title", ""),
                "author": metadata.get("Author", ""),
                "subject": metadata.get("Subject", ""),
                "creator": metadata.get("Creator", ""),
                "producer": metadata.get("Producer", ""),
                "num_pages": len(pdf.pages),
                "file_path": file_path,
                "file_size_bytes": os.path.getsize(file_path)
            }
            
            # Extract text content
            full_text = ""
            page_texts = []
            
            for page_num, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text() or ""
                    page_texts.append(text)
                    full_text += text + "\n\n"
                    
                    # Add page info
                    word_count = len(re.findall(r'\b\w+\b', text))
                    doc_info[f"page_{page_num+1}_word_count"] = word_count
                except Exception as e:
                    logging.warning(f"Error extracting text from page {page_num+1}: {e}")
            
            # Create chunked text
            chunked_text = self._chunk_text(full_text)
            
            # Add text statistics
            total_word_count = len(re.findall(r'\b\w+\b', full_text))
            doc_info["total_word_count"] = total_word_count
            doc_info["average_words_per_page"] = total_word_count / max(1, len(pdf.pages))
            
            # Extract table information if available
            try:
                tables_count = 0
                for page in pdf.pages:
                    tables = page.extract_tables()
                    tables_count += len(tables)
                doc_info["tables_count"] = tables_count
            except:
                pass
            
            return doc_info, full_text, chunked_text
    
    def _process_with_pypdf2(self, file_path: str) -> Tuple[Dict[str, Any], str, List[str]]:
        """
        Process a PDF file using PyPDF2 (fallback method).
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple containing (document_info, full_text, chunked_text)
        """
        # Open the PDF file
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract metadata
            info = pdf_reader.metadata
            
            # Prepare document info
            doc_info = {
                "title": info.get("/Title", ""),
                "author": info.get("/Author", ""),
                "subject": info.get("/Subject", ""),
                "creator": info.get("/Creator", ""),
                "producer": info.get("/Producer", ""),
                "num_pages": len(pdf_reader.pages),
                "file_path": file_path,
                "file_size_bytes": os.path.getsize(file_path)
            }
            
            # Extract text content
            full_text = ""
            page_texts = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text:
                        page_texts.append(text)
                        full_text += text + "\n\n"
                        
                        # Add page info
                        word_count = len(re.findall(r'\b\w+\b', text))
                        doc_info[f"page_{page_num+1}_word_count"] = word_count
                except Exception as e:
                    logging.warning(f"Error extracting text from page {page_num+1}: {e}")
            
            # Create chunked text
            chunked_text = self._chunk_text(full_text)
            
            # Add text statistics
            total_word_count = len(re.findall(r'\b\w+\b', full_text))
            doc_info["total_word_count"] = total_word_count
            doc_info["average_words_per_page"] = total_word_count / max(1, len(pdf_reader.pages))
            
            return doc_info, full_text, chunked_text
    
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
            
            # Adjust chunk to end at a sentence boundary if possible
            if end < text_length:
                # Look for sentence ending within 100 characters of the end
                search_range = min(end + 100, text_length)
                sentence_end = -1
                
                for match in re.finditer(r'[.!?]\s+', text[end:search_range]):
                    sentence_end = end + match.end()
                    break
                
                if sentence_end != -1:
                    end = sentence_end
            
            # Add the chunk
            chunks.append(text[start:end].strip())
            
            # Move to next chunk position, accounting for overlap
            start = end - self.chunk_overlap if end < text_length else text_length
            
            # Ensure progress is made
            if start >= end:
                start = end
        
        return chunks
