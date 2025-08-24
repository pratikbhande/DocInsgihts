"""
Analysis prompts used for document analysis across different document types.
"""

# Excel Analysis Prompts

EXCEL_ANALYSIS_PROMPT = """
Generate Python code to perform an initial exploratory analysis of the following Excel/CSV file:

File Path: {file_path}

File Metadata:
{metadata}

Your code should:
1. Import necessary libraries (pandas, numpy, matplotlib, seaborn)
2. Load the data from the file path
3. Perform basic exploratory analysis:
   - Display basic information (shape, columns, data types)
   - Compute summary statistics
   - Check for missing values
   - Show sample data
4. For numerical columns:
   - Calculate basic statistics (mean, median, min, max, etc.)
   - Create a correlation matrix if multiple numerical columns exist
5. For categorical columns:
   - Display value counts and distributions
6. Include basic visualizations if appropriate (histograms, boxplots)
7. Print all results clearly with descriptive labels

Return complete, executable Python code without explanations or markdown formatting.
"""

EXCEL_QUERY_PROMPT = """
Answer the following query about an Excel/CSV file:

Query: {query}

File Metadata:
{metadata}

Recent Chat History:
{chat_history}

Generated Python Code:
{generated_code}

Code Execution Results:
{code_execution_result}

Based on the provided information, answer the user's query with:
1. A clear, direct answer to the question
2. Key insights from the data relevant to the query
3. Important patterns, trends, or anomalies found
4. Explanations of the analysis performed (if code was generated)
5. Suggestions for further analysis if appropriate

Keep your response concise and focused on the most valuable information.
If the code execution revealed visualizations, describe what they show.
Ensure all numerical values and statistics are accurately reported.
"""

EXCEL_CODE_GENERATION_PROMPT = """
Determine if Python code generation is needed to answer this query about Excel/CSV data:

Query: {query}

File Metadata:
{metadata}

Sample Data:
{data_samples}

Recent Chat History:
{chat_history}

Respond only with "YES" or "NO" based on these criteria:

Answer YES if the query:
- Requires complex calculations or analysis
- Involves statistical operations beyond simple counts or sums
- Requests data visualization or charts
- Needs filtering, grouping, or transformations of data
- Requires time series analysis or trend identification
- Involves finding patterns, correlations, or anomalies

Answer NO if the query:
- Can be answered directly from the sample data or metadata
- Is a simple factual question about the file structure
- Is a clarification about previous answers
- Is a general question not requiring specific data analysis
- Is unrelated to data analysis
"""

# PDF Analysis Prompts

PDF_ANALYSIS_PROMPT = """
Analyze the following PDF document and provide a comprehensive overview:

Document: {file_name}

Document Information:
{doc_info}

Document Content Sample:
{doc_content}

Provide a thorough analysis that includes:
1. Document type and purpose (e.g., academic paper, report, manual, etc.)
2. Main topics and themes covered
3. Key sections and their content
4. Important facts, figures, or statistics
5. Writing style and target audience
6. Notable features or unusual aspects
7. Overall quality and completeness of the document

Focus on being objective and factual in your analysis, avoiding speculation.
Organize your analysis with clear sections and bullet points for readability.
"""

PDF_QUERY_PROMPT = """
Answer the following query about a PDF document:

Query: {query}

Document Information:
{doc_info}

Relevant Content Sections:
{relevant_chunks}

Recent Chat History:
{chat_history}

Based on the provided information, answer the user's query with:
1. Direct references to relevant parts of the document
2. Specific quotes when helpful (with context)
3. Clear explanation of how the information relates to their query
4. Factual information without speculation beyond the document content
5. Accurate representation of the document's statements

If the answer cannot be fully determined from the provided content, clearly state what information is available and what might be missing.
Focus on being helpful, accurate, and concise in your response.
"""

# Web Analysis Prompts

WEB_ANALYSIS_PROMPT = """
Analyze the following web content and provide a comprehensive overview:

Source: {file_name}

Content Information:
{doc_info}

Content Sample:
{doc_content}

Provide a thorough analysis that includes:
1. Website/content type and purpose
2. Main topics and themes covered
3. Key sections and their content
4. Important facts, figures, or statistics
5. Writing style and target audience
6. Notable features or unusual aspects
7. Overall quality and reliability of the information

Focus on being objective and factual in your analysis, avoiding speculation.
Note any potential biases or credibility concerns if apparent.
Organize your analysis with clear sections and bullet points for readability.
"""

WEB_QUERY_PROMPT = """
Answer the following query about web content:

Query: {query}

Source URL: {url}

Content Information:
{doc_info}

Relevant Content Sections:
{relevant_chunks}

Initial Analysis:
{initial_analysis}

Recent Chat History:
{chat_history}

Based on the provided information, answer the user's query with:
1. Direct references to relevant parts of the web content
2. Specific quotes when helpful (with context)
3. Clear explanation of how the information relates to their query
4. Factual information without speculation beyond the content
5. Consideration of the source's credibility when appropriate

If the answer cannot be fully determined from the provided content, clearly state what information is available and what might be missing.
Focus on being helpful, accurate, and concise in your response.
"""