import logging
import os
import pandas as pd
import numpy as np
import json
from typing import Dict, Any, List, Tuple
import openpyxl

class ExcelProcessor:
    """
    Processor for Excel and CSV files
    """
    
    def __init__(self):
        """Initialize the Excel processor"""
        logging.info("ExcelProcessor initialized")
    
    def process_file(self, file_path: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Process an Excel or CSV file and extract metadata and sample data.
        
        Args:
            file_path: Path to the Excel or CSV file
            
        Returns:
            Tuple containing (metadata, sample_data)
        """
        logging.info(f"Processing Excel file: {file_path}")
        
        try:
            # Determine file type
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension in ['.xlsx', '.xls']:
                metadata, sample_data = self._process_excel(file_path)
            elif file_extension == '.csv':
                metadata, sample_data = self._process_csv(file_path)
            else:
                raise ValueError(f"Unsupported file extension: {file_extension}")
            
            # Make sure the data is JSON serializable
            metadata = self._json_serialize_metadata(metadata)
            sample_data = self._json_serialize_metadata(sample_data)
            
            return metadata, sample_data
                
        except Exception as e:
            logging.error(f"Error processing Excel file: {e}")
            raise
    
    def _process_excel(self, file_path: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Process an Excel file (.xlsx, .xls).
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Tuple containing (metadata, sample_data)
        """
        # Load the workbook to get sheet information
        workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet_names = workbook.sheetnames
        
        # Initialize metadata
        metadata = {
            "file_type": "excel",
            "file_path": file_path,
            "sheet_names": sheet_names,
            "sheets_info": {}
        }
        
        # Initialize sample data
        sample_data = {}
        
        # Process each sheet
        for sheet_name in sheet_names:
            try:
                # Read sheet with pandas
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Get sheet info
                sheet_info = {
                    "num_rows": len(df),
                    "num_cols": len(df.columns),
                    "columns": df.columns.tolist(),
                    "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                    "has_missing_values": df.isnull().any().any(),
                    "missing_percentage": df.isnull().mean().mean() * 100
                }
                
                # Add numeric column statistics if available
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    stats = df[numeric_cols].describe().to_dict()
                    # Convert numpy types to Python native types for JSON serialization
                    for col, col_stats in stats.items():
                        stats[col] = {k: float(v) if isinstance(v, np.floating) else int(v) if isinstance(v, np.integer) else v 
                                      for k, v in col_stats.items()}
                    sheet_info["numeric_stats"] = stats
                
                # Add categorical column information if available
                categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
                if categorical_cols:
                    cat_info = {}
                    for col in categorical_cols[:5]:  # Limit to first 5 categorical columns
                        try:
                            value_counts = df[col].value_counts().head(10).to_dict()
                            cat_info[col] = {
                                "unique_values": df[col].nunique(),
                                "top_values": value_counts
                            }
                        except:
                            pass
                    sheet_info["categorical_info"] = cat_info
                
                # Add to metadata
                metadata["sheets_info"][sheet_name] = sheet_info
                
                # Add sample data (first 10 rows)
                sample_rows = min(10, len(df))
                if sample_rows > 0:
                    # Convert to dictionary and handle numpy/pandas types
                    sample_df = df.head(sample_rows)
                    sample_data[sheet_name] = self._dataframe_to_dict(sample_df)
            
            except Exception as e:
                logging.error(f"Error processing sheet {sheet_name}: {e}")
                metadata["sheets_info"][sheet_name] = {"error": str(e)}
        
        return metadata, sample_data
    
    def _process_csv(self, file_path: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Process a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Tuple containing (metadata, sample_data)
        """
        # Start with some basic file metadata that doesn't depend on reading the file
        basic_metadata = {
            "file_type": "csv",
            "file_path": file_path,
            "file_size_bytes": os.path.getsize(file_path)
        }
        
        # Try multiple approaches to read the CSV file
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        delimiters = [',', ';', '\t', '|']
        
        last_error = None
        
        # Try different combinations of encoding and delimiter
        for encoding in encodings:
            for delimiter in delimiters:
                try:
                    # Try to read sample lines first to detect if this works
                    with open(file_path, 'r', encoding=encoding) as f:
                        sample_lines = [next(f) for _ in range(5)]
                    
                    # If we can read the file, try pandas
                    df = pd.read_csv(
                        file_path, 
                        encoding=encoding, 
                        sep=delimiter, 
                        engine='python',  # More flexible engine
                        error_bad_lines=False,  # Skip bad lines
                        warn_bad_lines=True,
                        nrows=100,
                        low_memory=False,  # Better for mixed data types
                        on_bad_lines='skip'  # Skip bad lines
                    )
                    
                    # Get metadata
                    metadata = {
                        **basic_metadata,
                        "encoding": encoding,
                        "delimiter": delimiter,
                        "num_rows": len(df),
                        "num_cols": len(df.columns),
                        "columns": df.columns.tolist(),
                        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                        "has_missing_values": df.isnull().any().any(),
                        "missing_percentage": df.isnull().mean().mean() * 100
                    }
                    
                    # Add numeric column statistics if available
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    if numeric_cols:
                        stats = df[numeric_cols].describe().to_dict()
                        # Convert numpy types to Python native types for JSON serialization
                        for col, col_stats in stats.items():
                            stats[col] = {k: float(v) if isinstance(v, np.floating) else int(v) if isinstance(v, np.integer) else v 
                                          for k, v in col_stats.items()}
                        metadata["numeric_stats"] = stats
                    
                    # Add categorical column information if available
                    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                    if categorical_cols:
                        cat_info = {}
                        for col in categorical_cols[:5]:  # Limit to first 5 categorical columns
                            try:
                                value_counts = df[col].value_counts().head(10).to_dict()
                                cat_info[col] = {
                                    "unique_values": df[col].nunique(),
                                    "top_values": value_counts
                                }
                            except Exception as cat_err:
                                logging.warning(f"Error processing categorical column {col}: {cat_err}")
                                cat_info[col] = {"error": str(cat_err)}
                        metadata["categorical_info"] = cat_info
                    
                    # Get sample data (first 10 rows)
                    sample_rows = min(10, len(df))
                    if sample_rows > 0:
                        sample_df = df.head(sample_rows)
                        sample_data = {"data": self._dataframe_to_dict(sample_df)}
                    else:
                        sample_data = {"data": []}
                    
                    # Get total row count if possible
                    try:
                        # Count lines in file for total row estimate
                        with open(file_path, 'r', encoding=encoding) as f:
                            total_rows = sum(1 for _ in f) - 1  # Subtract header row
                        metadata["estimated_total_rows"] = total_rows
                    except Exception as count_err:
                        logging.warning(f"Error counting total rows: {count_err}")
                        # Use the file size to give a rough estimate
                        avg_row_size = os.path.getsize(file_path) / max(1, len(df))
                        estimated_rows = int(os.path.getsize(file_path) / max(1, avg_row_size))
                        metadata["estimated_total_rows"] = estimated_rows
                    
                    logging.info(f"Successfully processed CSV file with encoding={encoding}, delimiter={delimiter}")
                    return metadata, sample_data
                
                except Exception as e:
                    logging.debug(f"Failed to process CSV with encoding={encoding}, delimiter={delimiter}: {e}")
                    last_error = e
        
        # If all combinations failed, try a more basic approach
        try:
            # Try to read the file as plain text and extract basic info
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                first_line = f.readline().strip()
                sample_content = f.read(1000)  # Read a sample
            
            # Count approximately how many columns by splitting the first line
            approx_columns = []
            for delimiter in delimiters:
                if delimiter in first_line:
                    fields = first_line.split(delimiter)
                    if len(fields) > 1:
                        approx_columns = [f"Column_{i+1}" for i in range(len(fields))]
                        break
            
            # If we couldn't detect columns, use a default
            if not approx_columns:
                approx_columns = ["Unknown_Column"]
            
            # Create a minimal metadata and sample
            metadata = {
                **basic_metadata,
                "error": "Could not fully parse CSV file. Basic info only.",
                "approx_columns": approx_columns,
                "encoding": "unknown",
                "delimiter": "unknown",
                "sample_content": sample_content[:500]  # Include some sample content
            }
            
            # Create a minimal sample
            sample_data = {
                "data": [{"Warning": "Could not parse file properly"}],
                "sample_text": sample_content[:500]
            }
            
            return metadata, sample_data
            
        except Exception as final_e:
            # If even the basic approach fails, return a minimal error response
            logging.error(f"All attempts to process CSV file failed. Last error: {last_error}")
            metadata = {
                **basic_metadata,
                "error": f"Failed to process file: {str(last_error or final_e)}",
                "status": "error"
            }
            sample_data = {"data": [{"Error": str(last_error or final_e)}]}
            
            return metadata, sample_data
    
    def _dataframe_to_dict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Convert a pandas DataFrame to a list of dictionaries with Python native types.
        
        Args:
            df: The pandas DataFrame to convert
            
        Returns:
            List of dictionaries representing rows
        """
        # Convert to dictionary format
        records = df.to_dict(orient='records')
        
        # Handle non-serializable types
        for record in records:
            for key, value in record.items():
                if isinstance(value, (np.integer, np.int64)):
                    record[key] = int(value)
                elif isinstance(value, (np.floating, np.float64)):
                    record[key] = float(value)
                elif isinstance(value, np.bool_):
                    record[key] = bool(value)
                elif pd.isna(value):
                    record[key] = None
        
        return records
        
    def _json_serialize_metadata(self, data):
        """
        Make data JSON serializable by converting non-serializable types to Python native types.
        
        Args:
            data: Any Python data structure
            
        Returns:
            Data structure with JSON serializable values
        """
        import numpy as np
        import pandas as pd
        
        if isinstance(data, dict):
            return {k: self._json_serialize_metadata(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._json_serialize_metadata(item) for item in data]
        elif isinstance(data, tuple):
            return [self._json_serialize_metadata(item) for item in data]
        elif isinstance(data, (np.integer, np.int64)):
            return int(data)
        elif isinstance(data, (np.floating, np.float64)):
            return float(data)
        elif isinstance(data, np.bool_):
            return bool(data)
        elif pd.isna(data) or data is pd.NaT:
            return None
        elif isinstance(data, np.ndarray):
            return self._json_serialize_metadata(data.tolist())
        else:
            # For any other types, convert to string if not JSON serializable
            try:
                json.dumps(data)  # Test if it's serializable
                return data
            except (TypeError, OverflowError):
                return str(data)