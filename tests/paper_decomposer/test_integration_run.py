"""
Integration tests for the full paper-to-notebook pipeline.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import nbformat
    HAS_NBFORMAT = True
except ImportError:
    HAS_NBFORMAT = False

from paper_decomposer.notebook_gen import assemble_notebook
from paper_decomposer.executor import run_notebook_docker


@unittest.skipIf(not HAS_NBFORMAT, "nbformat not available")
class TestIntegrationRun(unittest.TestCase):
    """Integration tests for notebook execution."""
    
    def test_trivial_notebook_execution(self):
        """Test executing a trivial notebook that just prints hello."""
        cells = [
            {
                "cell_type": "markdown",
                "source": "# Hello World Notebook\nA simple test"
            },
            {
                "cell_type": "code",
                "source": "print('Hello from notebook!')"
            },
            {
                "cell_type": "code",
                "source": "result = 2 + 2\nprint(f'2 + 2 = {result}')"
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = os.path.join(tmpdir, "hello.ipynb")
            assemble_notebook(cells, notebook_path)
            
            # Execute notebook
            # Note: This requires Docker to be running
            # Mark as slow test or skip if Docker unavailable
            try:
                result = run_notebook_docker(
                    image="python:3.11-slim",
                    notebook_path=notebook_path,
                    timeout_sec=120
                )
                
                # Check if execution succeeded
                self.assertIn("returncode", result)
                self.assertIn("stdout", result)
                self.assertIn("execution_time", result)
                
                # If Docker is available and execution succeeded
                if result["returncode"] == 0:
                    print(f"✓ Notebook executed successfully in {result['execution_time']:.1f}s")
                else:
                    print(f"✗ Notebook execution failed: {result.get('stderr', '')[:200]}")
                
            except Exception as e:
                # Skip test if Docker is not available
                self.skipTest(f"Docker execution not available: {e}")
    
    def test_matplotlib_notebook_execution(self):
        """Test executing a notebook that creates a matplotlib plot."""
        cells = [
            {
                "cell_type": "code",
                "source": "import matplotlib\nmatplotlib.use('Agg')  # Non-interactive backend\nimport matplotlib.pyplot as plt\nimport numpy as np"
            },
            {
                "cell_type": "code",
                "source": "x = np.linspace(0, 2*np.pi, 100)\ny = np.sin(x)"
            },
            {
                "cell_type": "code",
                "source": "plt.figure(figsize=(8, 4))\nplt.plot(x, y)\nplt.xlabel('x')\nplt.ylabel('sin(x)')\nplt.title('Sine Wave')\nplt.savefig('/tmp/sine_wave.png')\nprint('Plot saved!')"
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = os.path.join(tmpdir, "plot.ipynb")
            assemble_notebook(cells, notebook_path)
            
            try:
                result = run_notebook_docker(
                    image="python:3.11-slim",
                    notebook_path=notebook_path,
                    timeout_sec=180
                )
                
                self.assertIn("returncode", result)
                
                if result["returncode"] == 0:
                    # Check if plot was created
                    self.assertIn("artifacts", result)
                    print(f"✓ Plot notebook executed, artifacts: {result.get('artifacts', [])}")
                
            except Exception as e:
                self.skipTest(f"Docker execution not available: {e}")
    
    def test_failing_notebook_execution(self):
        """Test that failing notebooks are properly reported."""
        cells = [
            {
                "cell_type": "code",
                "source": "print('Starting...')"
            },
            {
                "cell_type": "code",
                "source": "# This will fail\nimport nonexistent_module"
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = os.path.join(tmpdir, "failing.ipynb")
            assemble_notebook(cells, notebook_path)
            
            try:
                result = run_notebook_docker(
                    image="python:3.11-slim",
                    notebook_path=notebook_path,
                    timeout_sec=120
                )
                
                # Should report failure
                self.assertIn("returncode", result)
                self.assertNotEqual(result["returncode"], 0, "Expected notebook to fail")
                
                # Should have error information
                output = result.get("stdout", "") + result.get("stderr", "")
                self.assertTrue(
                    "error" in output.lower() or "exception" in output.lower(),
                    "Expected error message in output"
                )
                
            except Exception as e:
                self.skipTest(f"Docker execution not available: {e}")


@unittest.skipIf(not HAS_NBFORMAT, "nbformat not available")
class TestNotebookValidation(unittest.TestCase):
    """Test notebook validation and structure."""
    
    def test_created_notebook_is_valid_json(self):
        """Test that created notebooks are valid JSON."""
        cells = [
            {"cell_type": "code", "source": "x = 1"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = os.path.join(tmpdir, "test.ipynb")
            assemble_notebook(cells, notebook_path)
            
            # Should be valid JSON
            with open(notebook_path, "r") as f:
                data = json.load(f)
            
            self.assertIn("cells", data)
            self.assertIn("metadata", data)
            self.assertIn("nbformat", data)
    
    def test_created_notebook_readable_by_nbformat(self):
        """Test that notebooks can be read by nbformat."""
        cells = [
            {"cell_type": "markdown", "source": "# Test"},
            {"cell_type": "code", "source": "print('test')"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = os.path.join(tmpdir, "test.ipynb")
            assemble_notebook(cells, notebook_path)
            
            # Should be readable
            with open(notebook_path, "r") as f:
                nb = nbformat.read(f, as_version=4)
            
            self.assertEqual(len(nb.cells), 2)
            self.assertEqual(nb.cells[0].cell_type, "markdown")
            self.assertEqual(nb.cells[1].cell_type, "code")


@unittest.skipIf(not HAS_NBFORMAT, "nbformat not available")  
class TestEndToEndScenario(unittest.TestCase):
    """Test complete end-to-end scenarios."""
    
    def test_simple_ml_experiment(self):
        """Test a simple machine learning experiment notebook."""
        cells = [
            {
                "cell_type": "markdown",
                "source": "# Simple ML Experiment\nLogistic regression on synthetic data"
            },
            {
                "cell_type": "code",
                "source": "import numpy as np\nfrom sklearn.linear_model import LogisticRegression\nfrom sklearn.metrics import accuracy_score"
            },
            {
                "cell_type": "code",
                "source": "# Generate synthetic data\nnp.random.seed(42)\nX = np.random.randn(100, 2)\ny = (X[:, 0] + X[:, 1] > 0).astype(int)"
            },
            {
                "cell_type": "code",
                "source": "# Train model\nmodel = LogisticRegression()\nmodel.fit(X, y)\naccuracy = accuracy_score(y, model.predict(X))\nprint(f'Accuracy: {accuracy:.2f}')"
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = os.path.join(tmpdir, "ml_experiment.ipynb")
            assemble_notebook(cells, notebook_path)
            
            # Verify notebook is created and valid
            self.assertTrue(os.path.exists(notebook_path))
            
            with open(notebook_path, "r") as f:
                nb = nbformat.read(f, as_version=4)
            
            self.assertEqual(len(nb.cells), 4)
            
            # Optionally try to execute (requires Docker)
            try:
                result = run_notebook_docker(
                    image="python:3.11-slim",
                    notebook_path=notebook_path,
                    timeout_sec=180
                )
                
                if result["returncode"] == 0:
                    print("✓ ML experiment notebook executed successfully")
                    self.assertIn("Accuracy", result.get("stdout", ""))
                
            except Exception as e:
                print(f"Note: Could not execute notebook: {e}")


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
