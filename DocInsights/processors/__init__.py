"""
DocInsights Processors Module

This module contains the document processor classes that handle different document types.
Each processor is specialized for a specific document format and provides extraction and analysis capabilities.
"""

from .excel_processor import ExcelProcessor
from .pdf_processor import PdfProcessor
from .web_processor import WebProcessor
from .text_processor import TextProcessor

__all__ = [
    'ExcelProcessor',
    'PdfProcessor',
    'WebProcessor',
    'TextProcessor'
]
