"""
Unit tests for notebook generation and assembly.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import nbformat
    HAS_NBFORMAT = True
except ImportError:
    HAS_NBFORMAT = False

from paper_decomposer.notebook_gen import (
    generate_notebook_cells,
    assemble_notebook,
    apply_cell_fixes,
    read_notebook_cells,
    _validate_cells
)


@unittest.skipIf(not HAS_NBFORMAT, "nbformat not available")
class TestNotebookAssembly(unittest.TestCase):
    """Test notebook assembly functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_cells = [
            {
                "cell_type": "markdown",
                "source": "# Test Notebook\n\nThis is a test."
            },
            {
                "cell_type": "code",
                "source": "import numpy as np\nprint('hello')"
            },
            {
                "cell_type": "code",
                "source": "x = np.array([1, 2, 3])\nprint(x.mean())"
            }
        ]
        
        self.sample_experiment = {
            "id": "exp1",
            "title": "Test Experiment",
            "description": "A simple test experiment",
            "dataset_info": {
                "name": "Synthetic",
                "is_synthetic": True
            },
            "model_spec": {
                "type": "linear_regression",
                "framework": "sklearn"
            }
        }
    
    def test_validate_cells_valid(self):
        """Test cell validation with valid cells."""
        # Should not raise
        _validate_cells(self.sample_cells)
    
    def test_validate_cells_empty(self):
        """Test cell validation with empty list."""
        with self.assertRaises(ValueError) as cm:
            _validate_cells([])
        self.assertIn("empty", str(cm.exception))
    
    def test_validate_cells_missing_cell_type(self):
        """Test cell validation with missing cell_type."""
        invalid_cells = [{"source": "test"}]
        with self.assertRaises(ValueError) as cm:
            _validate_cells(invalid_cells)
        self.assertIn("cell_type", str(cm.exception))
    
    def test_validate_cells_invalid_cell_type(self):
        """Test cell validation with invalid cell_type."""
        invalid_cells = [{"cell_type": "invalid", "source": "test"}]
        with self.assertRaises(ValueError) as cm:
            _validate_cells(invalid_cells)
        self.assertIn("invalid cell_type", str(cm.exception))
    
    def test_validate_cells_missing_source(self):
        """Test cell validation with missing source."""
        invalid_cells = [{"cell_type": "code"}]
        with self.assertRaises(ValueError) as cm:
            _validate_cells(invalid_cells)
        self.assertIn("source", str(cm.exception))
    
    def test_assemble_notebook(self):
        """Test assembling a notebook from cells."""
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = os.path.join(tmpdir, "test.ipynb")
            
            assemble_notebook(self.sample_cells, notebook_path)
            
            # Verify file exists
            self.assertTrue(os.path.exists(notebook_path))
            
            # Verify it's valid
            with open(notebook_path, "r", encoding="utf-8") as f:
                nb = nbformat.read(f, as_version=4)
            
            self.assertEqual(len(nb.cells), 3)
            self.assertEqual(nb.cells[0].cell_type, "markdown")
            self.assertEqual(nb.cells[1].cell_type, "code")
            self.assertIn("numpy", nb.cells[1].source)
    
    def test_read_notebook_cells(self):
        """Test reading cells from an existing notebook."""
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = os.path.join(tmpdir, "test.ipynb")
            
            # Create a notebook
            assemble_notebook(self.sample_cells, notebook_path)
            
            # Read it back
            cells = read_notebook_cells(notebook_path)
            
            self.assertEqual(len(cells), 3)
            self.assertEqual(cells[0]["cell_type"], "markdown")
            self.assertEqual(cells[1]["cell_type"], "code")
            self.assertIn("numpy", cells[1]["source"])
    
    def test_apply_cell_fixes(self):
        """Test applying fixes to notebook cells."""
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = os.path.join(tmpdir, "test.ipynb")
            
            # Create initial notebook
            assemble_notebook(self.sample_cells, notebook_path)
            
            # Apply fix to second cell
            fixes = [
                {
                    "cell_index": 1,
                    "source": "import numpy as np\nimport pandas as pd\nprint('fixed')"
                }
            ]
            
            apply_cell_fixes(notebook_path, fixes)
            
            # Read back and verify
            cells = read_notebook_cells(notebook_path)
            self.assertIn("pandas", cells[1]["source"])
            self.assertIn("fixed", cells[1]["source"])
    
    def test_apply_cell_fixes_out_of_bounds(self):
        """Test applying fix with invalid cell index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = os.path.join(tmpdir, "test.ipynb")
            assemble_notebook(self.sample_cells, notebook_path)
            
            fixes = [{"cell_index": 99, "source": "test"}]
            
            with self.assertRaises(ValueError) as cm:
                apply_cell_fixes(notebook_path, fixes)
            self.assertIn("out of bounds", str(cm.exception))
    
    @patch('paper_decomposer.notebook_gen.RLM')
    def test_generate_notebook_cells_success(self, mock_rlm_class):
        """Test successful notebook generation."""
        mock_rlm = Mock()
        
        # Mock response
        response_data = {"cells": self.sample_cells}
        mock_rlm.return_value = json.dumps(response_data)
        
        cells = generate_notebook_cells(mock_rlm, self.sample_experiment, toy_mode=True)
        
        self.assertEqual(len(cells), 3)
        self.assertEqual(cells[0]["cell_type"], "markdown")
        mock_rlm.assert_called_once()
    
    @patch('paper_decomposer.notebook_gen.RLM')
    def test_generate_notebook_cells_with_retry(self, mock_rlm_class):
        """Test notebook generation with retry on invalid JSON."""
        mock_rlm = Mock()
        
        # First call returns invalid JSON, second succeeds
        response_data = {"cells": self.sample_cells}
        mock_rlm.side_effect = [
            "Invalid JSON {",
            json.dumps(response_data)
        ]
        
        cells = generate_notebook_cells(mock_rlm, self.sample_experiment)
        
        self.assertEqual(len(cells), 3)
        self.assertEqual(mock_rlm.call_count, 2)
    
    @patch('paper_decomposer.notebook_gen.RLM')
    def test_generate_notebook_cells_max_retries(self, mock_rlm_class):
        """Test notebook generation failing after max retries."""
        mock_rlm = Mock()
        mock_rlm.return_value = "Invalid JSON"
        
        with self.assertRaises(ValueError) as cm:
            generate_notebook_cells(mock_rlm, self.sample_experiment)
        
        self.assertIn("Failed to generate", str(cm.exception))


@unittest.skipIf(not HAS_NBFORMAT, "nbformat not available")
class TestNotebookCreation(unittest.TestCase):
    """Test full notebook creation workflow."""
    
    def test_create_simple_notebook(self):
        """Test creating a simple runnable notebook."""
        cells = [
            {
                "cell_type": "markdown",
                "source": "# Simple Test\nJust print hello world"
            },
            {
                "cell_type": "code",
                "source": "print('Hello, World!')"
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = os.path.join(tmpdir, "simple.ipynb")
            assemble_notebook(cells, notebook_path)
            
            # Verify the notebook is valid JSON
            with open(notebook_path, "r") as f:
                data = json.load(f)
            
            self.assertIn("cells", data)
            self.assertEqual(len(data["cells"]), 2)
    
    def test_create_notebook_with_plots(self):
        """Test creating a notebook with matplotlib plot."""
        cells = [
            {
                "cell_type": "code",
                "source": "import matplotlib.pyplot as plt\nimport numpy as np"
            },
            {
                "cell_type": "code",
                "source": "x = np.linspace(0, 10, 100)\nplt.plot(x, np.sin(x))\nplt.savefig('plot.png')"
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = os.path.join(tmpdir, "plot.ipynb")
            assemble_notebook(cells, notebook_path)
            
            self.assertTrue(os.path.exists(notebook_path))


if __name__ == "__main__":
    unittest.main()
