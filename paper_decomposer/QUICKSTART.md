# Quick Start Guide - Paper Decomposer

## Installation

1. **Install the package with paper decomposer dependencies:**

```bash
pip install -e ".[paper_decomposer]"
```

Or install dependencies manually:

```bash
pip install nbformat pymupdf papermill pdfminer.six
```

2. **Ensure Docker is installed and running:**

```bash
docker --version
docker ps
```

## Quick Test

### 1. Run Unit Tests

```bash
# Test decomposition logic
python -m pytest tests/paper_decomposer/test_decompose.py -v

# Test notebook assembly  
python -m pytest tests/paper_decomposer/test_notebook_assembly.py -v

# Test integration (requires Docker)
python -m pytest tests/paper_decomposer/test_integration_run.py -v
```

### 2. Use the Example Script

```python
# Create a simple test script
from paper_decomposer import PaperToNotebookController

# Initialize
controller = PaperToNotebookController(toy_mode=True)

# Test with sample paper (you'll need to create or download a PDF)
result = controller.run_from_pdf("examples/sample_paper.pdf", experiment_index=0)

print(f"Success: {result['success']}")
print(f"Output: {result.get('output_directory')}")
```

### 3. Command Line Test

```bash
# Download a simple arXiv paper
python -m paper_decomposer.controller \
    https://arxiv.org/abs/1706.03762 \
    --experiment 0 \
    --toy \
    --max-iterations 3
```

## Expected Output

After a successful run, you should see:

```
output/
  <paper-id>/
    decomposition.json
    notebook-experiment0.ipynb
    notebook-experiment0_executed.ipynb  # if execution succeeded
    trajectory.json
    run_report.json
```

## Troubleshooting

### "Import fitz could not be resolved"
```bash
pip install pymupdf
```

### "Import nbformat could not be resolved"  
```bash
pip install nbformat
```

### "Docker execution error"
- Ensure Docker is running: `docker ps`
- Check Docker permissions
- Try pulling the image manually: `docker pull python:3.11-slim`

### "RLM client not configured"
- Set up your LLM API keys (Anthropic, OpenAI, etc.)
- Or configure RLM client explicitly:

```python
from rlm import RLM
from rlm.clients.anthropic import AnthropicClient

rlm = RLM(client=AnthropicClient())
controller = PaperToNotebookController(rlm_client=rlm)
```

## Next Steps

1. Read the full documentation: `paper_decomposer/docs/README.md`
2. Check the feature overview: `paper_decomposer/FEATURE_OVERVIEW.md`
3. Explore example code: `examples/paper_decomposer_example.py`
4. Try processing your own papers!

## Minimal Working Example

```python
#!/usr/bin/env python3
"""Minimal example - just test the pipeline without execution."""

from paper_decomposer.ingest import extract_text_from_pdf, chunk_text
from paper_decomposer.decompose import decompose_paper
from paper_decomposer.notebook_gen import generate_notebook_cells, assemble_notebook
from rlm import RLM

# 1. Extract text
text = extract_text_from_pdf("paper.pdf")
chunks = chunk_text(text, max_chunk_size=8000)

# 2. Decompose
rlm = RLM()
decomposition = decompose_paper(rlm, chunks)
print(f"Found {len(decomposition['experiments'])} experiments")

# 3. Generate notebook
if decomposition['experiments']:
    experiment = decomposition['experiments'][0]
    cells = generate_notebook_cells(rlm, experiment, toy_mode=True)
    assemble_notebook(cells, "output/test_notebook.ipynb")
    print("Notebook created: output/test_notebook.ipynb")
```

Save this as `test_pipeline.py` and run:
```bash
python test_pipeline.py
```

## Success Criteria

✅ Tests pass (at least the non-Docker ones)
✅ Can decompose a paper to JSON
✅ Can generate a notebook from experiment spec
✅ Can assemble a valid .ipynb file
✅ (Optional) Can execute notebook in Docker
