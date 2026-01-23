"""
Jupyter notebook generation from experiment specifications.
"""

import json
import os
from pathlib import Path
from typing import Any

try:
    import nbformat
    from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell
    HAS_NBFORMAT = True
except ImportError:
    HAS_NBFORMAT = False

from rlm import RLM


def generate_notebook_cells(rlm_client: RLM, experiment: dict, toy_mode: bool = True) -> list[dict]:
    """
    Generate notebook cells for an experiment using RLM.
    
    Args:
        rlm_client: RLM client instance
        experiment: Experiment dictionary from decomposition
        toy_mode: If True, prefer synthetic datasets over real downloads
        
    Returns:
        List of cell dictionaries with 'cell_type' and 'source' keys
        
    Raises:
        ValueError: If RLM fails to produce valid cell specification
    """
    # Load the notebook generation prompt
    prompt_path = Path(__file__).parent / "prompts" / "notebook_generation_prompt.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    
    # Add toy mode instruction if enabled
    toy_mode_note = ""
    if toy_mode:
        toy_mode_note = "\n\n**IMPORTANT: This is TOY MODE. You MUST use synthetic datasets. Do NOT download large real datasets.**"
    
    # Construct full prompt with experiment details
    experiment_json = json.dumps(experiment, indent=2)
    full_prompt = f"{prompt_template}{toy_mode_note}\n\n---\n\nExperiment specification:\n\n{experiment_json}"
    
    print(f"Generating notebook for experiment: {experiment.get('title', 'Untitled')}")
    
    # Call RLM with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        response = rlm_client(full_prompt)
        
        try:
            # Extract and validate JSON
            result = _extract_json_from_response(response)
            
            if "cells" not in result:
                raise ValueError("Response missing 'cells' array")
            
            cells = result["cells"]
            
            # Validate cells structure
            _validate_cells(cells)
            
            return cells
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse notebook cells (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                full_prompt = (
                    f"{prompt_template}{toy_mode_note}\n\n"
                    f"Your previous response was invalid: {e}\n"
                    f"Please output ONLY valid JSON matching the schema.\n\n"
                    f"Experiment specification:\n\n{experiment_json}"
                )
            else:
                raise ValueError(f"Failed to generate valid notebook cells after {max_retries} attempts")


def _extract_json_from_response(response: str) -> dict:
    """Extract JSON from RLM response, handling markdown code blocks."""
    # Try direct parsing
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try extracting from markdown code blocks
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        if end > start:
            return json.loads(response[start:end].strip())
    
    if "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        if end > start:
            return json.loads(response[start:end].strip())
    
    # Try finding JSON boundaries
    start_idx = response.find("{")
    end_idx = response.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return json.loads(response[start_idx:end_idx+1])
    
    raise json.JSONDecodeError("Could not find valid JSON in response", response, 0)


def _validate_cells(cells: list[dict]) -> None:
    """
    Validate notebook cells structure.
    
    Args:
        cells: List of cell dictionaries
        
    Raises:
        ValueError: If validation fails
    """
    if not isinstance(cells, list):
        raise ValueError("cells must be a list")
    
    if len(cells) == 0:
        raise ValueError("cells list is empty")
    
    for i, cell in enumerate(cells):
        if not isinstance(cell, dict):
            raise ValueError(f"Cell {i} is not a dictionary")
        
        if "cell_type" not in cell:
            raise ValueError(f"Cell {i} missing 'cell_type'")
        
        if cell["cell_type"] not in ["code", "markdown"]:
            raise ValueError(f"Cell {i} has invalid cell_type: {cell['cell_type']}")
        
        if "source" not in cell:
            raise ValueError(f"Cell {i} missing 'source'")
        
        if not isinstance(cell["source"], str):
            raise ValueError(f"Cell {i} source must be a string")


def assemble_notebook(cells: list[dict], out_path: str) -> None:
    """
    Assemble a Jupyter notebook from cell specifications and save to file.
    
    Args:
        cells: List of cell dictionaries with 'cell_type' and 'source'
        out_path: Path where the notebook should be saved
        
    Raises:
        ImportError: If nbformat is not available
    """
    if not HAS_NBFORMAT:
        raise ImportError(
            "nbformat is required for notebook generation. "
            "Install it with: pip install nbformat"
        )
    
    # Create a new notebook
    nb = new_notebook()
    
    # Add cells
    for cell_spec in cells:
        cell_type = cell_spec["cell_type"]
        source = cell_spec["source"]
        
        if cell_type == "code":
            nb.cells.append(new_code_cell(source))
        elif cell_type == "markdown":
            nb.cells.append(new_markdown_cell(source))
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    # Write notebook to file
    with open(out_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    
    print(f"Notebook saved to: {out_path}")


def apply_cell_fixes(notebook_path: str, fixes: list[dict]) -> None:
    """
    Apply fixes to specific cells in a notebook.
    
    Args:
        notebook_path: Path to the notebook file
        fixes: List of fix dictionaries with 'cell_index' and 'source'
        
    Raises:
        ImportError: If nbformat is not available
        ValueError: If cell_index is out of bounds
    """
    if not HAS_NBFORMAT:
        raise ImportError("nbformat is required. Install it with: pip install nbformat")
    
    # Read the notebook
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)
    
    # Apply fixes
    for fix in fixes:
        cell_index = fix.get("cell_index")
        new_source = fix.get("source")
        
        if cell_index is None:
            print(f"Warning: Fix missing cell_index, skipping")
            continue
        
        if cell_index < 0 or cell_index >= len(nb.cells):
            raise ValueError(f"Cell index {cell_index} out of bounds (notebook has {len(nb.cells)} cells)")
        
        # Update the cell source
        nb.cells[cell_index].source = new_source
        print(f"Applied fix to cell {cell_index}")
    
    # Save the modified notebook
    with open(notebook_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    
    print(f"Saved fixes to: {notebook_path}")


def read_notebook_cells(notebook_path: str) -> list[dict]:
    """
    Read cells from an existing notebook.
    
    Args:
        notebook_path: Path to the notebook file
        
    Returns:
        List of cell dictionaries with 'cell_type' and 'source'
        
    Raises:
        ImportError: If nbformat is not available
    """
    if not HAS_NBFORMAT:
        raise ImportError("nbformat is required. Install it with: pip install nbformat")
    
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)
    
    cells = []
    for cell in nb.cells:
        cells.append({
            "cell_type": cell.cell_type,
            "source": cell.source
        })
    
    return cells
