"""
DocInsights Agents Module

This module contains the agent classes that power the DocInsights application.
Each agent is specialized for a specific document type or functionality.
"""

from .base_agent import BaseAgent
from .router_agent import RouterAgent
from .excel_agent import ExcelAgent
from .pdf_agent import PdfAgent
from .web_agent import WebAgent
from .report_agent import ReportAgent

__all__ = [
    'BaseAgent',
    'RouterAgent',
    'ExcelAgent',
    'PdfAgent',
    'WebAgent',
    'ReportAgent'
]
