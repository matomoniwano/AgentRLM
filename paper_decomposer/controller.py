"""
High-level controller for paper-to-notebook workflow.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

from rlm import RLM

from .ingest import extract_text_from_pdf, fetch_arxiv_pdf, chunk_text
from .decompose import decompose_paper
from .notebook_gen import generate_notebook_cells, assemble_notebook, apply_cell_fixes, read_notebook_cells
from .executor import run_notebook_docker, extract_notebook_error


class PaperToNotebookController:
    """
    Controller that orchestrates the full paper-to-notebook pipeline.
    """
    
    def __init__(
        self,
        rlm_client: Optional[RLM] = None,
        max_iterations: int = 5,
        toy_mode: bool = True,
        image: str = "python:3.11-slim",
        output_dir: str = "output",
        timeout_sec: int = 600
    ):
        """
        Initialize the controller.
        
        Args:
            rlm_client: RLM client instance (will create default if None)
            max_iterations: Maximum fix iterations for notebook execution
            toy_mode: Use synthetic datasets instead of real downloads
            image: Docker image for notebook execution
            output_dir: Base directory for output files
            timeout_sec: Timeout for notebook execution
        """
        self.rlm_client = rlm_client or RLM()
        self.max_iterations = max_iterations
        self.toy_mode = toy_mode
        self.image = image
        self.output_dir = output_dir
        self.timeout_sec = timeout_sec
        
        # Trajectory tracking
        self.trajectory = []
    
    def run_from_pdf(self, pdf_path: str, experiment_index: int = 0) -> dict:
        """
        Complete pipeline: PDF -> decomposition -> notebook -> execution with fixes.
        
        Args:
            pdf_path: Path to PDF file
            experiment_index: Which experiment to generate notebook for (0-indexed)
            
        Returns:
            Dictionary with pipeline results and output paths
        """
        print("=" * 80)
        print("PAPER TO NOTEBOOK PIPELINE")
        print("=" * 80)
        
        start_time = time.time()
        
        # Step 1: Extract text
        print("\n[1/6] Extracting text from PDF...")
        try:
            text = extract_text_from_pdf(pdf_path)
            print(f"Extracted {len(text)} characters from PDF")
            self._log_step("text_extraction", {"length": len(text), "success": True})
        except Exception as e:
            error_msg = f"Failed to extract text: {e}"
            print(error_msg)
            self._log_step("text_extraction", {"success": False, "error": str(e)})
            return self._create_failure_report(error_msg)
        
        # Step 2: Chunk text
        print("\n[2/6] Chunking text...")
        chunks = chunk_text(text, max_chunk_size=8000, overlap=200)
        print(f"Created {len(chunks)} chunks")
        self._log_step("chunking", {"num_chunks": len(chunks)})
        
        # Step 3: Decompose paper
        print("\n[3/6] Decomposing paper structure...")
        try:
            decomposition = decompose_paper(self.rlm_client, chunks)
            print(f"Found {len(decomposition.get('experiments', []))} experiments")
            self._log_step("decomposition", {
                "num_experiments": len(decomposition.get('experiments', [])),
                "success": True
            })
        except Exception as e:
            error_msg = f"Failed to decompose paper: {e}"
            print(error_msg)
            self._log_step("decomposition", {"success": False, "error": str(e)})
            return self._create_failure_report(error_msg)
        
        # Save decomposition
        paper_id = Path(pdf_path).stem
        paper_output_dir = os.path.join(self.output_dir, paper_id)
        os.makedirs(paper_output_dir, exist_ok=True)
        
        decomposition_path = os.path.join(paper_output_dir, "decomposition.json")
        with open(decomposition_path, "w", encoding="utf-8") as f:
            json.dump(decomposition, f, indent=2)
        print(f"Saved decomposition to: {decomposition_path}")
        
        # Step 4: Select and generate notebook
        experiments = decomposition.get("experiments", [])
        if not experiments:
            error_msg = "No experiments found in paper"
            print(error_msg)
            return self._create_failure_report(error_msg)
        
        if experiment_index >= len(experiments):
            error_msg = f"Experiment index {experiment_index} out of range (only {len(experiments)} experiments found)"
            print(error_msg)
            return self._create_failure_report(error_msg)
        
        experiment = experiments[experiment_index]
        print(f"\n[4/6] Generating notebook for experiment {experiment_index}: {experiment.get('title', 'Untitled')}")
        
        try:
            cells = generate_notebook_cells(self.rlm_client, experiment, self.toy_mode)
            print(f"Generated {len(cells)} cells")
            self._log_step("notebook_generation", {
                "num_cells": len(cells),
                "experiment_id": experiment.get("id"),
                "success": True
            })
        except Exception as e:
            error_msg = f"Failed to generate notebook: {e}"
            print(error_msg)
            self._log_step("notebook_generation", {"success": False, "error": str(e)})
            return self._create_failure_report(error_msg)
        
        # Assemble notebook
        notebook_path = os.path.join(paper_output_dir, f"notebook-experiment{experiment_index}.ipynb")
        assemble_notebook(cells, notebook_path)
        
        # Step 5: Execute notebook with iteration loop
        print(f"\n[5/6] Executing notebook (max {self.max_iterations} iterations)...")
        
        execution_history = []
        final_result = None
        
        for iteration in range(self.max_iterations):
            print(f"\n--- Iteration {iteration + 1}/{self.max_iterations} ---")
            
            result = run_notebook_docker(
                self.image,
                notebook_path,
                timeout_sec=self.timeout_sec
            )
            
            execution_history.append({
                "iteration": iteration + 1,
                "returncode": result["returncode"],
                "execution_time": result["execution_time"]
            })
            
            if result["returncode"] == 0:
                print(f"✓ Notebook executed successfully in {result['execution_time']:.1f}s")
                final_result = result
                self._log_step("execution", {
                    "success": True,
                    "iterations": iteration + 1,
                    "execution_time": result["execution_time"]
                })
                break
            else:
                print(f"✗ Execution failed (iteration {iteration + 1})")
                
                if iteration < self.max_iterations - 1:
                    # Try to fix the notebook
                    print("Analyzing error and generating fix...")
                    
                    error_info = extract_notebook_error(result, notebook_path)
                    fix_result = self._generate_fix(notebook_path, error_info)
                    
                    if fix_result["success"]:
                        print("Applied fix, retrying...")
                    else:
                        print("Could not generate valid fix")
                        final_result = result
                        break
                else:
                    print("Maximum iterations reached")
                    final_result = result
                    self._log_step("execution", {
                        "success": False,
                        "iterations": self.max_iterations,
                        "error": "Max iterations reached"
                    })
        
        # Step 6: Create final report
        print("\n[6/6] Creating final report...")
        
        total_time = time.time() - start_time
        
        report = {
            "success": final_result["returncode"] == 0 if final_result else False,
            "paper_id": paper_id,
            "experiment_index": experiment_index,
            "experiment_title": experiment.get("title"),
            "output_directory": paper_output_dir,
            "files": {
                "decomposition": decomposition_path,
                "notebook": notebook_path,
                "executed_notebook": final_result.get("notebook_output") if final_result else None,
                "trajectory": os.path.join(paper_output_dir, "trajectory.json")
            },
            "execution": {
                "iterations": len(execution_history),
                "final_returncode": final_result["returncode"] if final_result else -1,
                "execution_time": final_result["execution_time"] if final_result else 0,
                "artifacts": final_result.get("artifacts", []) if final_result else []
            },
            "total_time": total_time,
            "trajectory": self.trajectory
        }
        
        # Save report
        report_path = os.path.join(paper_output_dir, "run_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        
        # Save trajectory
        trajectory_path = os.path.join(paper_output_dir, "trajectory.json")
        with open(trajectory_path, "w", encoding="utf-8") as f:
            json.dump(self.trajectory, f, indent=2)
        
        print("\n" + "=" * 80)
        print("PIPELINE COMPLETE")
        print("=" * 80)
        print(f"Status: {'SUCCESS' if report['success'] else 'FAILED'}")
        print(f"Total time: {total_time:.1f}s")
        print(f"Output directory: {paper_output_dir}")
        print("=" * 80)
        
        return report
    
    def run_from_arxiv(self, arxiv_url: str, experiment_index: int = 0) -> dict:
        """
        Run pipeline from an arXiv URL.
        
        Args:
            arxiv_url: arXiv URL (e.g., "https://arxiv.org/abs/2301.12345")
            experiment_index: Which experiment to generate notebook for
            
        Returns:
            Pipeline results dictionary
        """
        print(f"Fetching paper from arXiv: {arxiv_url}")
        
        try:
            pdf_path = fetch_arxiv_pdf(arxiv_url, output_dir=self.output_dir)
            self._log_step("arxiv_fetch", {"url": arxiv_url, "success": True})
        except Exception as e:
            error_msg = f"Failed to fetch arXiv paper: {e}"
            print(error_msg)
            self._log_step("arxiv_fetch", {"url": arxiv_url, "success": False, "error": str(e)})
            return self._create_failure_report(error_msg)
        
        return self.run_from_pdf(pdf_path, experiment_index)
    
    def _generate_fix(self, notebook_path: str, error_info: dict) -> dict:
        """Generate and apply fixes for a failed notebook."""
        # Load fix prompt
        prompt_path = Path(__file__).parent / "prompts" / "fix_notebook_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        
        # Read notebook cells for context
        cells = read_notebook_cells(notebook_path)
        
        failing_idx = error_info.get("failing_cell_index", 0)
        
        # Get context
        previous_cells = "\n\n".join([
            f"Cell {i}:\n{cell['source']}"
            for i, cell in enumerate(cells[max(0, failing_idx-2):failing_idx])
        ])
        
        following_cells = "\n\n".join([
            f"Cell {i}:\n{cell['source']}"
            for i, cell in enumerate(cells[failing_idx+1:min(len(cells), failing_idx+3)])
        ])
        
        # Construct prompt
        prompt = prompt_template.format(
            failing_cell_code=error_info.get("failing_cell_code", ""),
            error_trace=error_info.get("error_trace", ""),
            previous_cells=previous_cells or "None",
            following_cells=following_cells or "None"
        )
        
        # Call RLM
        try:
            response = self.rlm_client(prompt)
            fix_data = json.loads(response)
            
            self._log_step("fix_generation", {
                "analysis": fix_data.get("analysis"),
                "num_fixes": len(fix_data.get("cells", []))
            })
            
            # Apply fixes
            apply_cell_fixes(notebook_path, fix_data.get("cells", []))
            
            return {"success": True, "fixes": fix_data.get("cells", [])}
            
        except Exception as e:
            print(f"Error generating fix: {e}")
            self._log_step("fix_generation", {"success": False, "error": str(e)})
            return {"success": False, "error": str(e)}
    
    def _log_step(self, step_name: str, data: dict):
        """Log a step to the trajectory."""
        self.trajectory.append({
            "step": step_name,
            "timestamp": time.time(),
            "data": data
        })
    
    def _create_failure_report(self, error_message: str) -> dict:
        """Create a failure report."""
        return {
            "success": False,
            "error": error_message,
            "trajectory": self.trajectory
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert academic papers to executable Jupyter notebooks"
    )
    
    parser.add_argument(
        "input",
        help="Path to PDF file or arXiv URL"
    )
    
    parser.add_argument(
        "--experiment",
        type=int,
        default=0,
        help="Experiment index to generate notebook for (default: 0)"
    )
    
    parser.add_argument(
        "--toy",
        action="store_true",
        help="Use toy mode (synthetic datasets)"
    )
    
    parser.add_argument(
        "--no-toy",
        action="store_true",
        help="Disable toy mode (download real datasets)"
    )
    
    parser.add_argument(
        "--image",
        default="python:3.11-slim",
        help="Docker image for execution (default: python:3.11-slim)"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="Maximum fix iterations (default: 5)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory (default: output)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Execution timeout in seconds (default: 600)"
    )
    
    args = parser.parse_args()
    
    # Determine toy mode
    toy_mode = True
    if args.no_toy:
        toy_mode = False
    elif args.toy:
        toy_mode = True
    
    # Create controller
    controller = PaperToNotebookController(
        max_iterations=args.max_iterations,
        toy_mode=toy_mode,
        image=args.image,
        output_dir=args.output_dir,
        timeout_sec=args.timeout
    )
    
    # Run pipeline
    if args.input.startswith("http"):
        result = controller.run_from_arxiv(args.input, args.experiment)
    else:
        result = controller.run_from_pdf(args.input, args.experiment)
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
