import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tempfile
import os
from typing import Dict, Any, List, Optional, Tuple

def create_visualization(data: Any, 
                        chart_type: str, 
                        title: str = "",
                        x_column: Optional[str] = None,
                        y_column: Optional[str] = None,
                        category_column: Optional[str] = None,
                        file_path: Optional[str] = None) -> Tuple[str, str]:
    """
    Create a visualization based on data and parameters.
    
    Args:
        data: Data to visualize (DataFrame or path to data file)
        chart_type: Type of chart to create (bar, line, scatter, pie, etc.)
        title: Chart title
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        category_column: Column name for categories/grouping
        file_path: Optional path to save the visualization
        
    Returns:
        Tuple containing (file_path, description)
    """
    logging.info(f"Creating {chart_type} visualization")
    
    try:
        # Load data if it's a file path
        if isinstance(data, str) and os.path.exists(data):
            if data.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(data)
            elif data.endswith('.csv'):
                df = pd.read_csv(data)
            else:
                raise ValueError(f"Unsupported data file format: {data}")
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("Data must be a DataFrame or path to a data file")
        
        # Set up the figure
        plt.figure(figsize=(10, 6))
        
        # Apply seaborn styling
        sns.set_style("whitegrid")
        
        # Create the visualization based on chart type
        if chart_type.lower() == 'bar':
            _create_bar_chart(df, x_column, y_column, category_column, title)
        elif chart_type.lower() == 'line':
            _create_line_chart(df, x_column, y_column, category_column, title)
        elif chart_type.lower() == 'scatter':
            _create_scatter_plot(df, x_column, y_column, category_column, title)
        elif chart_type.lower() == 'pie':
            _create_pie_chart(df, x_column, y_column, title)
        elif chart_type.lower() == 'histogram':
            _create_histogram(df, x_column, title)
        elif chart_type.lower() == 'heatmap':
            _create_heatmap(df, title)
        elif chart_type.lower() == 'boxplot':
            _create_boxplot(df, x_column, y_column, title)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        # Save the figure
        if not file_path:
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            file_path = temp_file.name
            temp_file.close()
        
        plt.tight_layout()
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Generate a description of the visualization
        description = f"{chart_type.capitalize()} chart showing {y_column} by {x_column}"
        if category_column:
            description += f", grouped by {category_column}"
        
        return file_path, description
        
    except Exception as e:
        logging.error(f"Error creating visualization: {e}")
        raise

def _create_bar_chart(df: pd.DataFrame, 
                     x_column: str, 
                     y_column: str, 
                     category_column: Optional[str] = None, 
                     title: str = ""):
    """
    Create a bar chart.
    
    Args:
        df: DataFrame with the data
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        category_column: Optional column name for grouping
        title: Chart title
    """
    if category_column:
        # Grouped bar chart
        grouped_data = df.groupby([x_column, category_column])[y_column].mean().unstack()
        grouped_data.plot(kind='bar', ax=plt.gca())
    else:
        # Simple bar chart
        sns.barplot(x=x_column, y=y_column, data=df, ax=plt.gca())
    
    plt.title(title)
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.xticks(rotation=45)

def _create_line_chart(df: pd.DataFrame, 
                      x_column: str, 
                      y_column: str, 
                      category_column: Optional[str] = None, 
                      title: str = ""):
    """
    Create a line chart.
    
    Args:
        df: DataFrame with the data
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        category_column: Optional column name for multiple lines
        title: Chart title
    """
    if category_column:
        # Multiple line chart
        for category, group in df.groupby(category_column):
            plt.plot(group[x_column], group[y_column], marker='o', linestyle='-', label=category)
        plt.legend()
    else:
        # Simple line chart
        plt.plot(df[x_column], df[y_column], marker='o', linestyle='-')
    
    plt.title(title)
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.xticks(rotation=45)

def _create_scatter_plot(df: pd.DataFrame, 
                        x_column: str, 
                        y_column: str, 
                        category_column: Optional[str] = None, 
                        title: str = ""):
    """
    Create a scatter plot.
    
    Args:
        df: DataFrame with the data
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        category_column: Optional column name for point colors
        title: Chart title
    """
    if category_column:
        sns.scatterplot(x=x_column, y=y_column, hue=category_column, data=df, ax=plt.gca())
    else:
        sns.scatterplot(x=x_column, y=y_column, data=df, ax=plt.gca())
    
    plt.title(title)
    plt.xlabel(x_column)
    plt.ylabel(y_column)

def _create_pie_chart(df: pd.DataFrame, 
                     x_column: str, 
                     y_column: Optional[str] = None, 
                     title: str = ""):
    """
    Create a pie chart.
    
    Args:
        df: DataFrame with the data
        x_column: Column name for categories
        y_column: Optional column name for values (uses counts if None)
        title: Chart title
    """
    if y_column:
        # Use values from y_column
        values = df.groupby(x_column)[y_column].sum()
    else:
        # Use counts of x_column values
        values = df[x_column].value_counts()
    
    plt.pie(values, labels=values.index, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')  # Equal aspect ratio ensures the pie chart is circular
    plt.title(title)

def _create_histogram(df: pd.DataFrame, 
                     x_column: str, 
                     title: str = ""):
    """
    Create a histogram.
    
    Args:
        df: DataFrame with the data
        x_column: Column name for the values
        title: Chart title
    """
    sns.histplot(df[x_column], kde=True, ax=plt.gca())
    plt.title(title)
    plt.xlabel(x_column)
    plt.ylabel("Frequency")

def _create_heatmap(df: pd.DataFrame, 
                   title: str = ""):
    """
    Create a correlation heatmap.
    
    Args:
        df: DataFrame with the data
        title: Chart title
    """
    # Get only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    # Calculate correlation matrix
    corr = numeric_df.corr()
    
    # Plot heatmap
    sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1, ax=plt.gca())
    plt.title(title)

def _create_boxplot(df: pd.DataFrame, 
                   x_column: str, 
                   y_column: str, 
                   title: str = ""):
    """
    Create a boxplot.
    
    Args:
        df: DataFrame with the data
        x_column: Column name for categories
        y_column: Column name for values
        title: Chart title
    """
    sns.boxplot(x=x_column, y=y_column, data=df, ax=plt.gca())
    plt.title(title)
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.xticks(rotation=45)