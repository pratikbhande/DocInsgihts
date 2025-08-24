import logging
import os
import re
import requests
from typing import Dict, Any, List, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import html2text

class WebProcessor:
    """
    Processor for web content and HTML files
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the Web processor.
        
        Args:
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.ignore_tables = False
        logging.info("WebProcessor initialized")
    
    def process_file(self, file_path: str) -> Tuple[Dict[str, Any], str, List[str]]:
        """
        Process an HTML file and extract metadata, content, and chunked content.
        
        Args:
            file_path: Path to the HTML file
            
        Returns:
            Tuple containing (document_info, full_text, chunked_text)
        """
        logging.info(f"Processing HTML file: {file_path}")
        
        try:
            # Read the HTML file
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # Process the HTML content
            return self._process_html_content(html_content, file_path)
            
        except Exception as e:
            # Try with different encoding if UTF-8 fails
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    html_content = file.read()
                
                return self._process_html_content(html_content, file_path)
            except Exception as e2:
                logging.error(f"HTML processing failed: {e2}")
                raise
    
    def process_url(self, url: str) -> Tuple[Dict[str, Any], str, List[str]]:
        """
        Process a web URL and extract metadata, content, and chunked content.
        
        Args:
            url: Web URL to process
            
        Returns:
            Tuple containing (document_info, full_text, chunked_text)
        """
        logging.info(f"Processing URL: {url}")
        
        try:
            # Fetch the URL content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            # Process the HTML content
            return self._process_html_content(response.text, url)
            
        except Exception as e:
            logging.error(f"URL processing failed: {e}")
            raise
    
    def _process_html_content(self, html_content: str, source: str) -> Tuple[Dict[str, Any], str, List[str]]:
        """
        Process HTML content and extract metadata, text, and chunked text.
        
        Args:
            html_content: The HTML content to process
            source: Source identifier (file path or URL)
            
        Returns:
            Tuple containing (document_info, full_text, chunked_text)
        """
        # Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract metadata
        title = soup.title.string if soup.title else ""
        
        # Get all meta tags
        meta_tags = {}
        for meta in soup.find_all('meta'):
            if meta.get('name') and meta.get('content'):
                meta_tags[meta['name']] = meta['content']
            elif meta.get('property') and meta.get('content'):
                meta_tags[meta['property']] = meta['content']
        
        # Prepare document info
        doc_info = {
            "title": title,
            "meta_tags": meta_tags,
            "source": source,
            "content_size_bytes": len(html_content)
        }
        
        # Extract main content
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Extract text from HTML
        body_content = soup.body if soup.body else soup
        
        # Convert HTML to markdown text
        markdown_text = self.html_converter.handle(str(body_content))
        
        # Clean up markdown text
        clean_text = self._clean_markdown_text(markdown_text)
        
        # Create chunked text
        chunked_text = self._chunk_text(clean_text)
        
        # Add text statistics
        word_count = len(re.findall(r'\b\w+\b', clean_text))
        doc_info["word_count"] = word_count
        
        # Extract links
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        doc_info["links_count"] = len(links)
        doc_info["external_links"] = self._count_external_links(links, source)
        
        return doc_info, clean_text, chunked_text
    
    def _clean_markdown_text(self, text: str) -> str:
        """
        Clean up markdown text from html2text conversion.
        
        Args:
            text: Markdown text to clean
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove UTF-8 control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Fix URL formatting issues common in html2text output
        text = re.sub(r'\[\s*([^\]]+)\s*\]\s*\(\s*([^)]+)\s*\)', r'[\1](\2)', text)
        
        # Remove any remaining HTML entities
        text = re.sub(r'&[a-zA-Z0-9]+;', ' ', text)
        
        return text.strip()
    
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
    
    def _count_external_links(self, links: List[str], source: str) -> int:
        """
        Count external links in a list of URLs.
        
        Args:
            links: List of URLs
            source: Source URL or file path
            
        Returns:
            Count of external links
        """
        if not links:
            return 0
        
        # Parse the source to get the domain
        try:
            source_domain = urlparse(source).netloc
            if not source_domain:
                # If source is a file path, there's no domain to compare against
                return 0
                
            # Count links that have a different domain
            external_count = 0
            for link in links:
                try:
                    link_domain = urlparse(link).netloc
                    if link_domain and link_domain != source_domain:
                        external_count += 1
                except:
                    pass
                    
            return external_count
            
        except:
            return 0
