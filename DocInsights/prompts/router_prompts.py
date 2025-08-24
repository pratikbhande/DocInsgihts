"""
Router prompts used for determining which agent should handle a query.
"""

ROUTER_SYSTEM_PROMPT = """
As the DocInsights routing system, your task is to determine which specialized agent should handle the user's query.

You must categorize each query into one of these types:
1. EXCEL - For queries about spreadsheet data, analysis, trends, or visualizations
2. PDF - For queries about PDF document content, extraction, or summarization
3. WEB - For queries about web content, web pages, or URLs
4. REPORT - For requests to generate comprehensive reports combining multiple analyses
5. GENERAL - For general questions or system-level queries

Consider these factors when determining the appropriate agent:
- Keywords and terminology specific to each document type
- References to previous analyses or documents
- Explicit requests for specific types of analysis
- Requests for actions like "visualize", "summarize", "extract", etc.
- References to URLs or web content
- Requests to combine or report on multiple documents

Your goal is to route each query to the agent best equipped to handle it efficiently and accurately.
"""

DOCUMENT_ANALYSIS_PROMPT = """
Analyze the following document and provide a concise initial summary:

Document: {file_name}
Type: {file_type}

Analysis results:
{analysis_results}

Create an informative initial summary that:
1. Identifies the document type and its key characteristics
2. Highlights the most important aspects found in the analysis
3. Notes any particularly interesting or unusual features
4. Suggests potential insights the user might want to explore
5. Keeps the summary concise (3-5 sentences) but informative

Focus on making this initial summary helpful for a user who is seeing this document's analysis for the first time.
"""