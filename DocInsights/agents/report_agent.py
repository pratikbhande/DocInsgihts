import logging
import os
import json
import tempfile
import base64
import re
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from utils.chat_memory import ChatMemory
from utils.code_executor import execute_python_code
from prompts.report_prompts import REPORT_GENERATION_PROMPT, VISUALIZATION_CODE_PROMPT

class ReportAgent(BaseAgent):
    """
    Agent for generating comprehensive reports from analyzed documents
    """
    
    def __init__(self, gemini_client, generation_config=None):
        """
        Initialize the Report agent.
        
        Args:
            gemini_client: The initialized Gemini client
            generation_config: Optional configuration for generation
        """
        super().__init__(gemini_client, generation_config)
        self.reports = {}  # Store generated reports
        self.report_visuals = {}  # Store report visualizations
        self.report_dir = os.path.join(os.getcwd(), "reports")
        
        # Create reports directory if it doesn't exist
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)
            
        logging.info("ReportAgent initialized")
        
    def process_query(self, query: str, chat_memory: Any = None) -> str:
        """
        Process a query from the user.
        
        Args:
            query: The user's query string
            chat_memory: Optional chat memory object
            
        Returns:
            The response string
        """
        # For the ReportAgent, most of the reporting is handled by generate_report()
        # This method primarily handles direct queries about reports
        
        if "generate" in query.lower() or "create" in query.lower() or "report" in query.lower():
            # Suggest that report generation is done through the RouterAgent
            return ("To generate a report, please provide details about what document data you want included. "
                   "The report will be created based on all analyzed documents.")
        else:
            # General query about reports
            existing_reports = len(self.reports)
            if existing_reports > 0:
                # If reports exist, provide info about them
                return f"You currently have {existing_reports} report(s) generated. You can view them in the Reports tab."
            else:
                return "No reports have been generated yet. Ask about your documents and request a report when ready."
    
    def generate_report(self, query: str, analyses: Dict[str, Any], chat_memory: ChatMemory) -> str:
        """
        Generate a comprehensive report based on document analyses.
        
        Args:
            query: The user's query requesting a report
            analyses: Dictionary of document analyses
            chat_memory: Chat memory object with conversation history
            
        Returns:
            Markdown-formatted report
        """
        logging.info(f"Generating report for query: {query}")
        
        try:
            # Create a timestamped directory for this report
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            report_id = f"report_{timestamp}"
            report_dir = os.path.join(self.report_dir, report_id)
            
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            
            # Get chat history for context
            chat_history = chat_memory.get_formatted_history(max_messages=10)
            
            # Prepare analyses for prompt
            analyses_summary = self._prepare_analyses_summary(analyses)
            
            # Generate multiple visualizations
            visualization_codes = []
            visualization_results = []
            visualization_files = []
            
            # Check if we need to generate visualizations
            excel_analyses = {name: analysis for name, analysis in analyses.items() 
                             if analysis.get("file_type") in ["excel", "csv"] or 
                             "metadata" in analysis and analysis["metadata"].get("file_type") in ["excel", "csv"]}
            
            # Determine target file paths from analyses (use Excel files if available)
            file_paths = []
            for name, analysis in excel_analyses.items():
                if "file_path" in analysis:
                    file_paths.append(analysis["file_path"])
                elif "metadata" in analysis and "file_path" in analysis["metadata"]:
                    file_paths.append(analysis["metadata"]["file_path"])
            
            if file_paths:
                # Generate visualization code for each Excel file
                for file_path in file_paths[:3]:  # Limit to 3 files for efficiency
                    # Get metadata for this file
                    file_metadata = None
                    for name, analysis in excel_analyses.items():
                        if analysis.get("file_path") == file_path or \
                           (analysis.get("metadata") and analysis["metadata"].get("file_path") == file_path):
                            file_metadata = analysis.get("metadata", {})
                            break
                    
                    # Generate visualization code
                    viz_code = self._generate_visualization_code(query, file_path, file_metadata)
                    visualization_codes.append(viz_code)
                    
                    # Execute visualization code
                    viz_result = execute_python_code(viz_code, file_path)
                    visualization_results.append(viz_result)
                    
                    # Extract image file paths from the result
                    image_files = self._extract_image_paths(viz_result)
                    visualization_files.extend(image_files)
                    
                    # Copy image files to the report directory
                    for img_file in image_files:
                        if os.path.exists(img_file):
                            import shutil
                            dest_file = os.path.join(report_dir, os.path.basename(img_file))
                            shutil.copy2(img_file, dest_file)
            
            # Generate the report
            report_prompt = REPORT_GENERATION_PROMPT.format(
                query=query,
                analyses_summary=analyses_summary,
                chat_history=chat_history,
                visualization_code="\n\n".join(visualization_codes),
                visualization_results="\n\n".join(visualization_results)
            )
            
            report = self.generate_response(report_prompt)
            
            # Enhance the report with image references
            if visualization_files:
                report = self._enhance_report_with_images(report, visualization_files, report_dir)
            
            # Save the report to file
            report_file = os.path.join(report_dir, "report.md")
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report)
            
            # Generate HTML version if possible
            try:
                import markdown
                html_content = markdown.markdown(report, extensions=['tables', 'fenced_code'])
                html_report = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Data Analysis Report</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; }}
                        h1 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                        h2 {{ color: #3498db; margin-top: 30px; }}
                        h3 {{ color: #2980b9; }}
                        img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; padding: 5px; margin: 10px 0; }}
                        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                        th, td {{ text-align: left; padding: 12px; }}
                        tr:nth-child(even) {{ background-color: #f2f2f2; }}
                        th {{ background-color: #3498db; color: white; }}
                        pre {{ background-color: #f8f8f8; border: 1px solid #ddd; border-radius: 3px; padding: 10px; overflow-x: auto; }}
                        code {{ font-family: monospace; background-color: #f8f8f8; padding: 2px 4px; border-radius: 3px; }}
                        blockquote {{ background-color: #f9f9f9; border-left: 10px solid #ccc; margin: 1.5em 10px; padding: 0.5em 10px; }}
                        .figure {{ text-align: center; margin: 20px 0; }}
                        .figure img {{ max-width: 90%; }}
                        .figure p {{ font-style: italic; color: #666; }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """
                
                html_file = os.path.join(report_dir, "report.html")
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(html_report)
            except Exception as e:
                logging.warning(f"Error creating HTML report: {e}")
            
            # Store the report
            self.reports[report_id] = {
                "query": query,
                "content": report,
                "dir": report_dir,
                "visualization_files": visualization_files,
                "timestamp": timestamp
            }
            
            # If we have visualization files, add them to the report
            if visualization_files:
                # Add a section about the visualizations if not already included
                if "# Data Visualization" not in report:
                    visualization_section = "\n\n# Data Visualization\n\n"
                    for i, img_file in enumerate(visualization_files):
                        file_name = os.path.basename(img_file)
                        visualization_section += f"## Visualization {i+1}: {file_name}\n\n"
                        visualization_section += f"![{file_name}]({file_name})\n\n"
                    
                    # Add the visualization section before the conclusion
                    if "# Conclusion" in report:
                        report = report.replace("# Conclusion", visualization_section + "# Conclusion")
                    else:
                        report += visualization_section
            
            return report
            
        except Exception as e:
            error_msg = f"Error generating report: {str(e)}"
            logging.error(error_msg)
            return f"""
            # Error Generating Report
            
            I encountered an error while generating your report: {str(e)}
            
            Please try again with a more specific query, or ensure that your documents have been properly analyzed.
            """
    
    def _prepare_analyses_summary(self, analyses: Dict[str, Any]) -> str:
        """
        Prepare a summary of document analyses for the report prompt.
        
        Args:
            analyses: Dictionary of document analyses
            
        Returns:
            Formatted summary string
        """
        if not analyses:
            return "No document analyses available."
        
        summary_parts = []
        
        for doc_name, analysis in analyses.items():
            summary = f"## Document: {doc_name}\n"
            
            # Add metadata if available
            if "metadata" in analysis:
                summary += f"### Metadata\n"
                summary += json.dumps(analysis["metadata"], indent=2) + "\n\n"
            
            if "doc_info" in analysis:
                summary += f"### Document Info\n"
                summary += json.dumps(analysis["doc_info"], indent=2) + "\n\n"
            
            # Add analysis if available
            if "analysis" in analysis:
                summary += f"### Analysis\n"
                summary += analysis["analysis"] + "\n\n"
            
            # Add exploration results if available
            if "exploration_results" in analysis:
                summary += f"### Exploration Results\n"
                summary += analysis["exploration_results"] + "\n\n"
            
            # Add sample data if available
            if "sample_data" in analysis:
                summary += f"### Sample Data\n"
                sample_str = json.dumps(analysis["sample_data"], indent=2)
                # Limit sample data size
                if len(sample_str) > 1000:
                    sample_str = sample_str[:1000] + "...(truncated)"
                summary += sample_str + "\n\n"
            
            elif "content_sample" in analysis:
                summary += f"### Content Sample\n"
                sample = analysis["content_sample"]
                # Limit sample size
                if len(sample) > 1000:
                    sample = sample[:1000] + "...(truncated)"
                summary += sample + "\n\n"
            
            summary_parts.append(summary)
        
        return "\n".join(summary_parts)
    
    def _generate_visualization_code(self, query: str, file_path: str, metadata: Dict[str, Any]) -> str:
        """
        Generate Python code for visualizations based on the query and file metadata.
        
        Args:
            query: The user's query requesting a report
            file_path: Path to the data file
            metadata: Metadata about the file
            
        Returns:
            Python code for visualizations
        """
        # Generate visualization code
        viz_prompt = VISUALIZATION_CODE_PROMPT.format(
            query=query,
            file_path=file_path,
            metadata=json.dumps(metadata, indent=2) if metadata else "{}"
        )
        
        visualization_code = self.generate_response(viz_prompt)
        
        # Ensure the code is properly formatted
        if not visualization_code.strip().startswith("import"):
            # Provide a default visualization code if the generated one is invalid
            visualization_code = self._generate_default_visualization_code(file_path)
        
        return visualization_code
    
    def _extract_image_paths(self, execution_result: str) -> List[str]:
        """
        Extract image file paths from code execution results.
        
        Args:
            execution_result: String output from code execution
            
        Returns:
            List of image file paths
        """
        # Look for common image file mentions in the output
        image_paths = []
        
        # Pattern matching for saved image files
        import re
        # Match patterns like "Saved to: image.png" or "saved image.png" etc.
        patterns = [
            r'saved (?:to )?([\w\._/-]+\.(?:png|jpg|jpeg|svg|pdf))',
            r'saved (?:as )?([\w\._/-]+\.(?:png|jpg|jpeg|svg|pdf))',
            r'saved ([\w\._/-]+\.(?:png|jpg|jpeg|svg|pdf))',
            r'created ([\w\._/-]+\.(?:png|jpg|jpeg|svg|pdf))',
            r'output (?:to |as )?([\w\._/-]+\.(?:png|jpg|jpeg|svg|pdf))',
            r'(?:written|generated) (?:to )?([\w\._/-]+\.(?:png|jpg|jpeg|svg|pdf))',
            r'plt\.savefig\([\'\"]([\w\._/-]+\.(?:png|jpg|jpeg|svg|pdf))[\'\"]',
            r'fig\.savefig\([\'\"]([\w\._/-]+\.(?:png|jpg|jpeg|svg|pdf))[\'\"]'
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
        
        # Also look for common image filenames in the current directory
        try:
            current_dir = os.getcwd()
            for file in os.listdir(current_dir):
                if file.endswith(('.png', '.jpg', '.jpeg', '.svg', '.pdf')):
                    # Check if created/modified in the last minute
                    file_path = os.path.join(current_dir, file)
                    file_mtime = os.path.getmtime(file_path)
                    import time
                    if time.time() - file_mtime < 60:  # Created in the last minute
                        image_paths.append(file_path)
        except Exception as e:
            logging.warning(f"Error checking for image files in current directory: {e}")
        
        # Remove duplicates while preserving order
        unique_paths = []
        for path in image_paths:
            if path not in unique_paths:
                unique_paths.append(path)
        
        return unique_paths
    
    def _enhance_report_with_images(self, report: str, image_files: List[str], report_dir: str) -> str:
        """
        Enhance a report by adding image references.
        
        Args:
            report: Original report content
            image_files: List of image file paths
            report_dir: Directory where the report is saved
            
        Returns:
            Enhanced report with image references
        """
        # Check if we have image files to add
        if not image_files:
            return report
        
        # Check if the report already has image references
        if "![" in report:
            # Report already has images, so don't modify it
            return report
        
        # Determine appropriate location to add images
        enhanced_report = report
        
        # Look for a data visualization section
        viz_section_match = re.search(r'#\s*(?:Data|Visualization|Data\s+Visualization)', enhanced_report, re.IGNORECASE)
        
        if viz_section_match:
            # Find the end of the section heading
            section_start = viz_section_match.end()
            
            # Create image references
            image_content = "\n\n"
            for i, img_file in enumerate(image_files):
                file_name = os.path.basename(img_file)
                image_content += f"### Figure {i+1}: {file_name.replace('_', ' ').replace('.png', '')}\n\n"
                image_content += f"![{file_name}]({file_name})\n\n"
            
            # Insert into report after the section heading
            enhanced_report = enhanced_report[:section_start] + image_content + enhanced_report[section_start:]
        else:
            # No visualization section found - create one before conclusions
            conclusion_match = re.search(r'#\s*(?:Conclusion|Conclusions)', enhanced_report, re.IGNORECASE)
            
            visualization_section = "\n\n# Data Visualization\n\n"
            visualization_section += "The following visualizations provide graphical representation of the key data points and patterns identified in the analysis:\n\n"
            
            for i, img_file in enumerate(image_files):
                file_name = os.path.basename(img_file)
                visualization_section += f"### Figure {i+1}: {file_name.replace('_', ' ').replace('.png', '')}\n\n"
                visualization_section += f"![{file_name}]({file_name})\n\n"
            
            if conclusion_match:
                # Add before conclusion
                conclusion_start = conclusion_match.start()
                enhanced_report = enhanced_report[:conclusion_start] + visualization_section + enhanced_report[conclusion_start:]
            else:
                # Add at the end
                enhanced_report += visualization_section
        
        return enhanced_report
    
    def _generate_default_visualization_code(self, file_path: str) -> str:
        """
        Generate default visualization code when the LLM-generated code is invalid.
        
        Args:
            file_path: Path to the data file
            
        Returns:
            Python code for default visualizations
        """
        return f"""
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns
        from matplotlib.colors import LinearSegmentedColormap
        
        # Set visualization style
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_palette('viridis')
        
        # Custom color map for better visualization
        colors = ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725']
        cmap = LinearSegmentedColormap.from_list('custom_cmap', colors)
        
        # Load the data
        print(f"Loading data from {{file_path}}...")
        file_path = "{file_path}"
        
        try:
            # Determine file type and load accordingly
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
                print("File loaded as Excel")
            else:
                try:
                    df = pd.read_csv(file_path)
                    print("File loaded as CSV with default parameters")
                except:
                    # Try with more flexible parameters
                    df = pd.read_csv(
                        file_path, 
                        encoding='utf-8', 
                        sep=None,  # Try to infer separator
                        engine='python',  # More flexible engine
                        on_bad_lines='skip'  # Skip problematic lines
                    )
                    print("File loaded as CSV with flexible parameters")
            
            print(f"Data loaded successfully with shape: {{df.shape}}")
            
            # Get numeric and categorical columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            print(f"Numeric columns ({{len(numeric_cols)}}): {{numeric_cols[:5]}}")
            print(f"Categorical columns ({{len(categorical_cols)}}): {{categorical_cols[:5]}}")
            
            # Create multiple visualizations
            
            # 1. Distribution of numeric values
            if numeric_cols:
                print("\\nCreating distribution plots for numeric columns...")
                for i, col in enumerate(numeric_cols[:3]):  # First 3 numeric columns
                    plt.figure(figsize=(10, 6))
                    sns.histplot(df[col].dropna(), kde=True, bins=30, color='#3498db')
                    plt.title(f'Distribution of {{col}}', fontsize=16)
                    plt.xlabel(col, fontsize=12)
                    plt.ylabel('Frequency', fontsize=12)
                    plt.xticks(fontsize=10)
                    plt.yticks(fontsize=10)
                    plt.tight_layout()
                    filename = f'distribution_{{col.replace(" ", "_")}}.png'
                    plt.savefig(filename, dpi=300)
                    plt.close()
                    print(f"Saved distribution plot to {{filename}}")
            
            # 2. Correlation heatmap if multiple numeric columns
            if len(numeric_cols) > 1:
                print("\\nCreating correlation heatmap...")
                plt.figure(figsize=(12, 10))
                corr = df[numeric_cols].corr()
                mask = np.triu(np.ones_like(corr, dtype=bool))
                sns.heatmap(corr, mask=mask, cmap=cmap, annot=True, fmt=".2f", 
                            linewidths=0.5, cbar_kws={{"shrink": .8}})
                plt.title('Correlation Heatmap', fontsize=16)
                plt.tight_layout()
                plt.savefig('correlation_heatmap.png', dpi=300)
                plt.close()
                print("Saved correlation heatmap to correlation_heatmap.png")
            
            # 3. Bar chart for categorical columns
            if categorical_cols:
                print("\\nCreating bar charts for categorical columns...")
                for i, col in enumerate(categorical_cols[:2]):  # First 2 categorical columns
                    plt.figure(figsize=(12, 8))
                    value_counts = df[col].value_counts().nlargest(10)
                    sns.barplot(x=value_counts.index, y=value_counts.values, palette='viridis')
                    plt.title(f'Top 10 Values in {{col}}', fontsize=16)
                    plt.xlabel(col, fontsize=12)
                    plt.ylabel('Count', fontsize=12)
                    plt.xticks(rotation=45, ha='right', fontsize=10)
                    plt.yticks(fontsize=10)
                    plt.tight_layout()
                    filename = f'barchart_{{col.replace(" ", "_")}}.png'
                    plt.savefig(filename, dpi=300)
                    plt.close()
                    print(f"Saved bar chart to {{filename}}")
            
            # 4. Scatter plot if multiple numeric columns
            if len(numeric_cols) > 1:
                print("\\nCreating scatter plot...")
                plt.figure(figsize=(10, 8))
                x_col = numeric_cols[0]
                y_col = numeric_cols[1]
                
                # Add color dimension if we have 3+ numeric columns
                if len(numeric_cols) > 2:
                    color_col = numeric_cols[2]
                    scatter = plt.scatter(df[x_col], df[y_col], c=df[color_col], 
                                        cmap=cmap, alpha=0.7, s=50, edgecolor='w')
                    plt.colorbar(scatter, label=color_col)
                else:
                    plt.scatter(df[x_col], df[y_col], color='#2980b9', alpha=0.7, s=50, edgecolor='w')
                
                plt.title(f'Relationship between {{x_col}} and {{y_col}}', fontsize=16)
                plt.xlabel(x_col, fontsize=12)
                plt.ylabel(y_col, fontsize=12)
                plt.tight_layout()
                plt.savefig('scatter_plot.png', dpi=300)
                plt.close()
                print("Saved scatter plot to scatter_plot.png")
            
            # 5. Multi-panel figure with box plots
            if numeric_cols and categorical_cols:
                print("\\nCreating multi-panel boxplot figure...")
                numeric_to_use = numeric_cols[:2]  # Use first 2 numeric columns
                categorical_to_use = categorical_cols[0]  # Use first categorical column
                
                # Get top categories for better visualization
                top_categories = df[categorical_to_use].value_counts().nlargest(5).index.tolist()
                df_subset = df[df[categorical_to_use].isin(top_categories)]
                
                fig, axes = plt.subplots(1, len(numeric_to_use), figsize=(15, 8), sharey=False)
                
                for i, num_col in enumerate(numeric_to_use):
                    if len(numeric_to_use) == 1:
                        ax = axes
                    else:
                        ax = axes[i]
                    
                    sns.boxplot(x=categorical_to_use, y=num_col, data=df_subset, palette='viridis', ax=ax)
                    ax.set_title(f'{{num_col}} by {{categorical_to_use}}', fontsize=14)
                    ax.set_xlabel(categorical_to_use, fontsize=12)
                    ax.set_ylabel(num_col, fontsize=12)
                    ax.tick_params(axis='x', rotation=45)
                
                plt.tight_layout()
                plt.savefig('multi_panel_boxplot.png', dpi=300)
                plt.close()
                print("Saved multi-panel boxplot to multi_panel_boxplot.png")
                
            print("\\nAll visualizations created successfully.")
            
        except Exception as e:
            print(f"Error during visualization generation: {{e}}")
            
            # Try to create at least one simple visualization
            try:
                print("\\nAttempting to create a simple visualization...")
                plt.figure(figsize=(10, 6))
                plt.text(0.5, 0.5, f"Error generating visualizations: {{e}}", 
                        horizontalalignment='center', verticalalignment='center', fontsize=12)
                plt.axis('off')
                plt.savefig('visualization_error.png', dpi=300)
                plt.close()
                print("Created error notification image: visualization_error.png")
            except:
                print("Failed to create even the error visualization.")
        """