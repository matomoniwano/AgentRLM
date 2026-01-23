"""
Notebook execution in DockerREPL environment.
"""

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Optional

from rlm.environments.docker_repl import DockerREPL


def run_notebook_docker(
    image: str,
    notebook_path: str,
    timeout_sec: int = 600,
    cpu_limit: Optional[str] = None,
    mem_limit: Optional[str] = None,
    work_dir: Optional[str] = None
) -> dict:
    """
    Execute a Jupyter notebook inside a Docker container using DockerREPL.
    
    Args:
        image: Docker image to use (e.g., "python:3.11-slim")
        notebook_path: Path to the notebook file (will be mounted into container)
        timeout_sec: Maximum execution time in seconds
        cpu_limit: CPU limit (e.g., "1.0" for 1 CPU)
        mem_limit: Memory limit (e.g., "512m" or "1g")
        work_dir: Working directory inside container
        
    Returns:
        Dictionary with execution results:
        - stdout: Standard output
        - stderr: Standard error  
        - returncode: Exit code (0 for success)
        - execution_time: Time taken in seconds
        - artifacts: List of generated files
        - notebook_output: Path to executed notebook (if successful)
    """
    notebook_path = os.path.abspath(notebook_path)
    notebook_name = os.path.basename(notebook_path)
    notebook_dir = os.path.dirname(notebook_path)
    
    if not os.path.exists(notebook_path):
        return {
            "stdout": "",
            "stderr": f"Notebook file not found: {notebook_path}",
            "returncode": 1,
            "execution_time": 0,
            "artifacts": [],
            "notebook_output": None
        }
    
    print(f"Executing notebook: {notebook_name}")
    print(f"Docker image: {image}")
    
    # Create DockerREPL environment
    try:
        # Build DockerREPL kwargs
        repl_kwargs = {
            "image": image,
            "timeout": timeout_sec,
        }
        
        if cpu_limit:
            repl_kwargs["cpu_quota"] = int(float(cpu_limit) * 100000)
        
        if mem_limit:
            repl_kwargs["mem_limit"] = mem_limit
        
        if work_dir:
            repl_kwargs["working_dir"] = work_dir
        
        # Initialize the environment
        env = DockerREPL(**repl_kwargs)
        
        # Start timing
        start_time = time.time()
        
        # Install nbconvert and required packages
        print("Installing notebook execution tools...")
        install_cmd = "pip install -q nbconvert nbformat ipykernel 2>&1"
        install_result = env.step(install_cmd)
        
        if "error" in install_result.get("output", "").lower() and "successfully installed" not in install_result.get("output", "").lower():
            print(f"Warning during package installation: {install_result.get('output', '')[:200]}")
        
        # Copy notebook content into container by reading and writing
        print("Transferring notebook to container...")
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb_content = f.read()
        
        # Escape the content for shell
        escaped_content = nb_content.replace("'", "'\\''")
        
        # Write notebook to container using heredoc
        write_cmd = f"cat > /tmp/{notebook_name} << 'NOTEBOOK_EOF'\n{nb_content}\nNOTEBOOK_EOF"
        write_result = env.step(write_cmd)
        
        # Execute the notebook
        print("Executing notebook...")
        output_name = f"executed_{notebook_name}"
        exec_cmd = (
            f"cd /tmp && "
            f"jupyter nbconvert --to notebook --execute "
            f"--output {output_name} "
            f"--ExecutePreprocessor.timeout={timeout_sec} "
            f"{notebook_name} 2>&1"
        )
        
        exec_result = env.step(exec_cmd)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Determine success
        output_text = exec_result.get("output", "")
        returncode = 0 if "successfully" in output_text.lower() or exec_result.get("done", False) else 1
        
        # Try to extract executed notebook
        notebook_output = None
        if returncode == 0:
            # Read the executed notebook back
            read_cmd = f"cat /tmp/{output_name}"
            read_result = env.step(read_cmd)
            
            if read_result.get("output"):
                # Save executed notebook locally
                output_path = notebook_path.replace(".ipynb", "_executed.ipynb")
                try:
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(read_result["output"])
                    notebook_output = output_path
                    print(f"Saved executed notebook to: {output_path}")
                except Exception as e:
                    print(f"Could not save executed notebook: {e}")
        
        # Look for generated artifacts (images, data files, etc.)
        artifacts = []
        list_cmd = "ls -la /tmp/*.png /tmp/*.jpg /tmp/*.pdf /tmp/*.csv 2>/dev/null || true"
        list_result = env.step(list_cmd)
        
        if list_result.get("output"):
            # Parse filenames from ls output
            for line in list_result["output"].split("\n"):
                if line.strip() and not line.startswith("total"):
                    parts = line.split()
                    if len(parts) > 8:
                        filename = parts[-1]
                        if os.path.basename(filename) not in [notebook_name, output_name]:
                            artifacts.append(filename)
        
        # Clean up
        env.close()
        
        return {
            "stdout": output_text,
            "stderr": exec_result.get("error", ""),
            "returncode": returncode,
            "execution_time": execution_time,
            "artifacts": artifacts,
            "notebook_output": notebook_output
        }
        
    except Exception as e:
        execution_time = time.time() - start_time if 'start_time' in locals() else 0
        error_msg = f"Docker execution error: {str(e)}"
        print(error_msg)
        
        return {
            "stdout": "",
            "stderr": error_msg,
            "returncode": 1,
            "execution_time": execution_time,
            "artifacts": [],
            "notebook_output": None
        }


def extract_notebook_error(execution_result: dict, notebook_path: str) -> dict:
    """
    Extract detailed error information from a failed notebook execution.
    
    Args:
        execution_result: Result dictionary from run_notebook_docker
        notebook_path: Path to the notebook file
        
    Returns:
        Dictionary with error details:
        - failing_cell_index: Index of the failing cell (if identifiable)
        - failing_cell_code: Code from the failing cell
        - error_trace: Error traceback
        - error_type: Type of error (e.g., "ImportError", "ValueError")
    """
    stderr = execution_result.get("stderr", "")
    stdout = execution_result.get("stdout", "")
    combined_output = stdout + "\n" + stderr
    
    error_info = {
        "failing_cell_index": None,
        "failing_cell_code": "",
        "error_trace": combined_output,
        "error_type": "Unknown"
    }
    
    # Try to parse cell number from nbconvert error messages
    # Example: "Error in cell 3"
    cell_match = re.search(r'[Cc]ell (\d+)', combined_output)
    if cell_match:
        error_info["failing_cell_index"] = int(cell_match.group(1))
    
    # Try to identify error type
    error_types = ["ImportError", "ModuleNotFoundError", "ValueError", "TypeError", 
                   "NameError", "KeyError", "AttributeError", "SyntaxError", "RuntimeError"]
    
    for error_type in error_types:
        if error_type in combined_output:
            error_info["error_type"] = error_type
            break
    
    # Try to extract the actual error traceback
    if "Traceback" in combined_output:
        traceback_start = combined_output.find("Traceback")
        error_info["error_trace"] = combined_output[traceback_start:]
    
    # If we found a failing cell, try to read its content
    if error_info["failing_cell_index"] is not None and os.path.exists(notebook_path):
        try:
            import nbformat
            with open(notebook_path, "r", encoding="utf-8") as f:
                nb = nbformat.read(f, as_version=4)
            
            cell_idx = error_info["failing_cell_index"]
            if 0 <= cell_idx < len(nb.cells):
                error_info["failing_cell_code"] = nb.cells[cell_idx].source
        except Exception as e:
            print(f"Could not read failing cell: {e}")
    
    return error_info
