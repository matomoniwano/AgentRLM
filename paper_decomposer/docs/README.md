# Paper Decomposer & Notebook Builder

A feature for AgentRLM that converts academic papers (PDF or arXiv) into executable Jupyter notebooks that reproduce key experiments.

## Overview

This module provides a complete pipeline for:

1. **Ingesting** academic papers from PDF files or arXiv URLs
2. **Decomposing** paper structure using RLM to extract experiments
3. **Generating** Jupyter notebooks from experiment specifications
4. **Executing** notebooks in DockerREPL with iterative error fixing
5. **Tracking** the entire process with detailed trajectory logs

## Installation

### Required Dependencies

```bash
pip install nbformat pymupdf papermill
```

Optional (for PDF extraction alternatives):
```bash
pip install pdfminer.six
```

### Docker Requirement

The notebook execution requires Docker to be installed and running, as notebooks are executed inside Docker containers using AgentRLM's DockerREPL environment.

## Quick Start

### From Python

```python
from paper_decomposer import PaperToNotebookController

# Initialize controller
controller = PaperToNotebookController(
    max_iterations=5,      # Max fix attempts
    toy_mode=True,         # Use synthetic data
    image="python:3.11-slim"
)

# Process a PDF
result = controller.run_from_pdf("path/to/paper.pdf", experiment_index=0)

# Or from arXiv
result = controller.run_from_arxiv("https://arxiv.org/abs/2301.12345", experiment_index=0)

# Check results
if result["success"]:
    print(f"Notebook created: {result['files']['notebook']}")
    print(f"Executed successfully in {result['execution']['iterations']} iterations")
else:
    print(f"Failed: {result.get('error')}")
```

### From Command Line

```bash
# Process a PDF file
python -m paper_decomposer.controller paper.pdf --experiment 0 --toy

# Process from arXiv
python -m paper_decomposer.controller https://arxiv.org/abs/2301.12345 --experiment 0

# With custom settings
python -m paper_decomposer.controller paper.pdf \
    --experiment 1 \
    --max-iterations 10 \
    --image python:3.11-slim \
    --timeout 900 \
    --output-dir my_output
```

### CLI Options

- `input`: Path to PDF file or arXiv URL (required)
- `--experiment N`: Which experiment to generate (default: 0)
- `--toy`: Use toy mode with synthetic datasets (default: True)
- `--no-toy`: Disable toy mode (download real datasets)
- `--image`: Docker image for execution (default: python:3.11-slim)
- `--max-iterations`: Maximum fix iterations (default: 5)
- `--output-dir`: Output directory (default: output)
- `--timeout`: Execution timeout in seconds (default: 600)

## Output Structure

After running the pipeline, you'll find:

```
output/
  <paper-id>/
    decomposition.json        # Structured paper analysis
    notebook-experiment0.ipynb # Generated notebook
    notebook-experiment0_executed.ipynb  # Executed version (if successful)
    trajectory.json           # Complete RLM interaction log
    run_report.json          # Summary of the run
```

## Features

### Toy Mode (Recommended)

By default, toy mode is enabled, which:
- Uses synthetic datasets instead of downloading large real datasets
- Keeps execution fast and resource-efficient
- Ensures notebooks are self-contained
- Reduces security/network concerns

Disable with `--no-toy` if you need real data.

### Iterative Error Fixing

If a notebook fails to execute:
1. The error is extracted and analyzed
2. RLM generates a fix for the failing cells
3. The notebook is updated and re-executed
4. Process repeats up to `max_iterations` times

### Resource Limits

DockerREPL provides:
- CPU limits (configurable)
- Memory limits (configurable)
- Execution timeouts
- Isolated execution environment

### Trajectory Logging

Every RLM interaction is logged to `trajectory.json`, including:
- All prompts sent to the LLM
- All responses received
- Timestamps for each step
- Success/failure status
- Error messages and fixes

## Architecture

### Module Structure

```
paper_decomposer/
  __init__.py          # Public API
  ingest.py            # PDF/arXiv ingestion
  decompose.py         # Paper structure extraction
  notebook_gen.py      # Notebook generation
  executor.py          # DockerREPL execution
  controller.py        # Orchestration & CLI
  prompts/
    decompose_prompt.txt
    notebook_generation_prompt.txt
    fix_notebook_prompt.txt
```

### Data Flow

```
PDF/arXiv → Text Extraction → Chunking → RLM Decomposition
    ↓
Structured JSON (experiments, sections, metadata)
    ↓
RLM Notebook Generation → Cell Assembly → .ipynb File
    ↓
DockerREPL Execution → Success? → Done
    ↓ (if failed)
Error Analysis → RLM Fix Generation → Apply Fixes → Retry
```

## Decomposition Schema

The paper decomposition produces JSON with this structure:

```json
{
  "title": "Paper Title",
  "authors": ["Author 1", "Author 2"],
  "abstract": "Paper abstract...",
  "sections": [
    {
      "id": "sec1",
      "heading": "Introduction",
      "summary": "Brief summary..."
    }
  ],
  "experiments": [
    {
      "id": "exp1",
      "title": "Experiment Name",
      "description": "What it does",
      "dataset_info": {
        "name": "MNIST",
        "source": "torchvision.datasets",
        "size": "60000 training samples",
        "is_synthetic": false
      },
      "inputs": "28x28 grayscale images",
      "outputs": "10 class probabilities",
      "model_spec": {
        "type": "CNN",
        "architecture": "2 conv layers + 2 fc layers",
        "framework": "pytorch"
      },
      "hyperparameters": {
        "learning_rate": "0.001",
        "batch_size": "64",
        "epochs": "10",
        "other": {}
      },
      "metrics_reported": ["accuracy", "loss"],
      "key_figures": ["figure_3", "table_1"]
    }
  ],
  "reproducibility_assessment": {
    "difficulty": "medium",
    "estimated_effort_hours": 4,
    "notes": "Requires GPU for reasonable training time"
  }
}
```

## Notebook Generation

Generated notebooks include:

1. **Markdown header**: Title and description
2. **Package installation**: `pip install` commands
3. **Imports**: All required libraries
4. **Data loading/generation**: Dataset setup (synthetic in toy mode)
5. **Preprocessing**: Data transformations
6. **Model definition**: Architecture implementation
7. **Training loop**: Short training (few epochs)
8. **Evaluation**: Compute metrics
9. **Visualization**: Plot results and save figures

## Advanced Usage

### Custom RLM Configuration

```python
from rlm import RLM
from rlm.clients.anthropic import AnthropicClient

# Use specific LLM provider
rlm = RLM(client=AnthropicClient(model="claude-3-5-sonnet-20241022"))

controller = PaperToNotebookController(rlm_client=rlm)
```

### Processing Multiple Experiments

```python
controller = PaperToNotebookController()

result = controller.run_from_pdf("paper.pdf")
num_experiments = len(result.get("decomposition", {}).get("experiments", []))

for i in range(num_experiments):
    print(f"Processing experiment {i}...")
    controller.run_from_pdf("paper.pdf", experiment_index=i)
```

### Custom Docker Images

Use a custom image with pre-installed packages:

```python
controller = PaperToNotebookController(
    image="myrepo/ml-image:latest",
    timeout_sec=1200
)
```

## Testing

Run the test suite:

```bash
# All tests
python -m pytest tests/paper_decomposer/

# Specific test file
python -m pytest tests/paper_decomposer/test_decompose.py

# Integration tests (requires Docker)
python -m pytest tests/paper_decomposer/test_integration_run.py

# With verbose output
python -m pytest tests/paper_decomposer/ -v
```

## Security Considerations

- **Isolated Execution**: All code runs in Docker containers
- **Resource Limits**: CPU, memory, and time limits prevent resource exhaustion
- **Network Control**: Toy mode avoids external downloads
- **No Host Access**: Containers don't mount host directories by default

## Limitations

- **PDF Quality**: Extraction quality depends on PDF structure
- **Complex Experiments**: Very complex experiments may not be fully reproducible
- **LLM Variability**: Results depend on LLM capabilities and prompts
- **Docker Required**: Execution requires Docker installation
- **Token Limits**: Very long papers may need chunking optimization

## Troubleshooting

### "Import fitz could not be resolved"

Install PyMuPDF: `pip install pymupdf`

### "Docker execution error"

Ensure Docker is running: `docker ps`

### "Failed to decompose paper"

- Check that the PDF is text-based (not scanned images)
- Try reducing `max_chunk_size` in code
- Verify RLM client is configured correctly

### Notebook execution timeout

- Increase timeout: `--timeout 1200`
- Use faster Docker image with pre-installed packages
- Reduce training epochs in generated notebooks

## Contributing

When adding features:
1. Follow existing code structure
2. Add tests for new functionality
3. Update prompts in `prompts/` directory
4. Document in this README

## License

Same as AgentRLM project license.
