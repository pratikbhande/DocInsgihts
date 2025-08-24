import logging
import sys
import io
import os
import traceback
from typing import Dict, Any, Optional
import tempfile
import matplotlib.pyplot as plt
from contextlib import contextmanager, redirect_stdout, redirect_stderr

@contextmanager
def capture_output():
    """
    Context manager to capture stdout and stderr.
    
    Yields:
        StringIO object with captured output
    """
    stdout = io.StringIO()
    stderr = io.StringIO()
    
    with redirect_stdout(stdout), redirect_stderr(stderr):
        yield stdout, stderr

def execute_python_code(code: str, file_path: Optional[str] = None) -> str:
    """
    Execute Python code in a safe environment and capture the output.
    
    Args:
        code: Python code to execute
        file_path: Optional path to a file the code should operate on
        
    Returns:
        String containing execution output or error messages
    """
    logging.info("Executing Python code")
    
    # Clean up code - strip markdown formatting if present
    code = _clean_code_for_execution(code)
    
    # Create a unique temp directory for execution
    temp_dir = tempfile.mkdtemp()
    cwd = os.getcwd()
    
    try:
        # Change to the temp directory
        os.chdir(temp_dir)
        
        # Create a dictionary with global variables for the execution environment
        globals_dict = {
            "__name__": "__main__",
            "file_path": file_path  # Pass file_path to the executed code
        }
        
        # Add the temp directory to sys.path to allow imports
        sys.path.insert(0, temp_dir)
        
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(code)
        
        # Capture stdout and stderr
        with capture_output() as (stdout, stderr):
            # Execute the code
            with open(temp_file_path, 'r') as file:
                exec(compile(file.read(), temp_file_path, 'exec'), globals_dict)
            
        # Get captured output
        output = stdout.getvalue()
        error = stderr.getvalue()
        
        # Check if any plots were created
        plot_created = False
        try:
            if plt.get_fignums():
                plot_created = True
                # Save the figure to a temporary file
                plt_file = os.path.join(temp_dir, 'plot.png')
                plt.savefig(plt_file)
                output += f"\n[Plot saved to {plt_file}]"
                plt.close('all')
        except:
            pass
        
        # Combine output and error messages
        if error:
            return f"Code execution error:\n{error}\n\nOutput (if any):\n{output}"
        else:
            return output
        
    except Exception as e:
        # Capture the full exception traceback
        tb = traceback.format_exc()
        logging.error(f"Code execution error: {e}\n{tb}")
        return f"Code execution error: {str(e)}\n\n{tb}"
    
    finally:
        # Reset working directory
        os.chdir(cwd)
        
        # Clean up
        try:
            os.remove(temp_file_path)
        except:
            pass
        
        # Restore sys.path
        if temp_dir in sys.path:
            sys.path.remove(temp_dir)

def _clean_code_for_execution(code: str) -> str:
    """
    Clean code to remove markdown formatting and prepare for execution.
    
    Args:
        code: The code potentially containing markdown formatting
        
    Returns:
        Clean code ready for execution
    """
    # First, check for markdown code blocks (```python ... ```)
    import re
    
    # Look for markdown code blocks
    code_block_pattern = r"```(?:python|py)?\s*([\s\S]*?)```"
    code_blocks = re.findall(code_block_pattern, code)
    
    if code_blocks:
        # If we found markdown code blocks, use the content of the first one
        return code_blocks[0].strip()
    
    # If no markdown blocks found, just return the original code
    return code