"""
Report generation prompts for creating comprehensive reports.
"""

REPORT_GENERATION_PROMPT = """
Generate a comprehensive, professional report based on the following information:

User Query: {query}

Document Analyses:
{analyses_summary}

Recent Chat History:
{chat_history}

Visualization Code:
{visualization_code}

Visualization Results:
{visualization_results}

Create a detailed, thorough report in Markdown format that would span 2-3 pages when printed. Include:

# 1. Executive Summary
Provide a concise but comprehensive overview of the key findings and insights (2-3 paragraphs). Highlight the most important discoveries and their implications.

# 2. Introduction
Explain the purpose of the report, the context of the analysis, and a brief overview of the documents analyzed. Clearly state the objectives of the analysis.

# 3. Methodology
Detail the analytical approach used, including:
- Data sources and their characteristics
- Data preparation steps
- Analytical techniques applied
- Tools and algorithms used
- Any limitations or assumptions made

# 4. Key Findings
Present a detailed exposition of the most important insights discovered, organized into logical sections with:
- Clear section headings for each major finding
- Supporting evidence with specific data points
- Interpretation of what each finding means in context
- Comparative analysis where applicable

# 5. Data Visualization
Include detailed descriptions and interpretations of at least 3-5 visualizations:
- Describe exactly what each visualization shows
- Explain patterns, trends, outliers, and correlations revealed
- Connect visualizations to the key findings
- Address any limitations or potential misinterpretations

# 6. Detailed Analysis
Provide an in-depth analysis of each document or data source:
- Comprehensive breakdown of important elements
- Statistical analysis with significance testing where appropriate
- Cross-document comparisons and contrasts
- Contradictory findings and how they were reconciled

# 7. Connections and Patterns
Highlight relationships between different pieces of information across documents:
- Identify recurring themes and patterns
- Analyze relationships between variables
- Address causality vs. correlation
- Synthesize findings into a coherent narrative

# 8. Conclusions
Synthesize all findings into comprehensive conclusions:
- Address the original objectives
- Summarize major discoveries
- Discuss implications for decision-making
- Address any unanswered questions

# 9. Recommendations
Provide actionable, specific recommendations based on the findings:
- Prioritized list of actions
- Implementation considerations
- Expected outcomes
- Potential challenges and mitigations

# 10. Appendices
Include supplementary information:
- Additional data tables
- Methodological details
- Technical notes on code or algorithms used

Formatting Guidelines:
- Use proper Markdown formatting with headers, lists, tables, etc.
- Include relevant data points and statistics with proper attribution
- Make the report visually scannable with clear section headings
- Ensure professional language and tone throughout
- For any visualizations mentioned, describe what they show and their implications in detail
- Use tables to present structured data where appropriate
- Include proper citations and references to data sources
- Use bold formatting for key insights and findings

The report should be comprehensive, detailed, and professional, suitable for executive review.
"""

VISUALIZATION_CODE_PROMPT = """
Generate high-quality Python code to create multiple sophisticated data visualizations for the following analysis request:

Query: {query}

File Path: {file_path}

File Metadata:
{metadata}

Generate comprehensive visualization code that creates at least 5 different high-quality, publication-ready visualizations that address different aspects of the data. Your code should:

1. Import necessary libraries:
   - pandas, numpy for data manipulation
   - matplotlib, seaborn for visualization
   - plotly for interactive visualizations if appropriate
   - Other specialized visualization libraries as needed

2. Load and prepare the data:
   - Handle missing values, outliers, and data type conversions
   - Create derivative variables if useful for visualization
   - Aggregate or transform data as needed for effective visualization

3. Create a diverse set of visualizations that collectively tell a complete story:
   - Distribution plots (histograms, KDE plots, box plots) to understand variables
   - Relationship plots (scatter plots, pair plots, correlation heatmaps) to explore connections
   - Time series plots when applicable (line charts, area charts)
   - Categorical comparisons (bar charts, grouped bars, pie charts)
   - Advanced visualizations (treemaps, geographical plots, faceted plots) when appropriate

4. For each visualization:
   - Use a descriptive title and proper axis labels with units
   - Choose appropriate color schemes (colorblind-friendly)
   - Include legends and annotations where needed
   - Set appropriate figure sizes for readability
   - Add explanatory text or annotations to highlight key insights
   - Apply consistent styling across visualizations

5. Create combination/multi-panel figures:
   - At least one figure should combine multiple subplots for comparison
   - Create faceted plots to show multiple dimensions simultaneously

6. Save each visualization:
   - Use high resolution (minimum 300 dpi)
   - Save in multiple formats (PNG and PDF)
   - Use descriptive filenames

7. Print descriptive output about each visualization:
   - Explain what each visualization shows
   - Highlight key patterns or insights visible in each figure
   - Provide statistical context where appropriate

Return complete, executable Python code without explanations or markdown formatting.
The code should be well-structured with comments explaining each major section and visualization.
Focus on creating visualizations that together provide a comprehensive understanding of the data.
"""