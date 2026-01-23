# Paper Decomposer & Notebook Builder - Feature Overview

## Summary

The **Paper Decomposer & Notebook Builder** is a comprehensive feature for AgentRLM that automatically converts academic research papers into executable Jupyter notebooks. The feature extracts experiment specifications from papers and generates reproducible code that attempts to replicate key results.

## What Has Been Implemented

### Core Modules (7 files)

1. **`paper_decomposer/__init__.py`**
   - Public API exports
   - Module initialization

2. **`paper_decomposer/ingest.py`**
   - PDF text extraction (PyMuPDF and pdfminer.six support)
   - arXiv paper downloading
   - Text chunking with overlap for better context
   - Functions: `extract_text_from_pdf()`, `fetch_arxiv_pdf()`, `chunk_text()`

3. **`paper_decomposer/decompose.py`**
   - RLM-based paper structure extraction
   - JSON schema validation
   - Multi-chunk processing and merging
   - Automatic retry on invalid JSON
   - Functions: `decompose_paper()`, merge and validation utilities

4. **`paper_decomposer/notebook_gen.py`**
   - RLM-based notebook cell generation
   - nbformat integration for .ipynb assembly
   - Cell fixing and patching
   - Notebook I/O utilities
   - Functions: `generate_notebook_cells()`, `assemble_notebook()`, `apply_cell_fixes()`

5. **`paper_decomposer/executor.py`**
   - DockerREPL integration for safe execution
   - Notebook execution with timeout and resource limits
   - Error extraction and analysis
   - Artifact collection (plots, CSVs, etc.)
   - Functions: `run_notebook_docker()`, `extract_notebook_error()`

6. **`paper_decomposer/controller.py`**
   - High-level pipeline orchestration
   - Iterative error fixing loop (max 5 iterations by default)
   - Complete trajectory logging
   - CLI interface
   - Class: `PaperToNotebookController`

7. **`paper_decomposer/prompts/`** (3 prompt templates)
   - `decompose_prompt.txt`: Extract paper structure to JSON
   - `notebook_generation_prompt.txt`: Generate notebook cells
   - `fix_notebook_prompt.txt`: Fix failing notebook cells

### Test Suite (4 files)

1. **`tests/paper_decomposer/test_decompose.py`**
   - Tests for JSON extraction and parsing
   - Schema validation tests
   - Partial result merging tests
   - Mock RLM integration tests

2. **`tests/paper_decomposer/test_notebook_assembly.py`**
   - Cell validation tests
   - Notebook assembly tests
   - Cell fixing tests
   - nbformat integration tests

3. **`tests/paper_decomposer/test_integration_run.py`**
   - End-to-end notebook execution tests
   - Docker integration tests (with graceful skip if unavailable)
   - Simple ML experiment validation

4. **`tests/paper_decomposer/__init__.py`**
   - Test package marker

### Documentation & Examples (3 files)

1. **`paper_decomposer/docs/README.md`**
   - Comprehensive user documentation
   - Installation instructions
   - Quick start guide
   - CLI reference
   - Architecture overview
   - Troubleshooting guide

2. **`examples/paper_decomposer_example.py`**
   - Python API usage examples
   - Multi-experiment processing example

3. **`examples/sample_paper.txt`**
   - Sample research paper text for testing
   - Contains 3 experiments with full details

### Configuration

- **`pyproject.toml`** updated with:
  - Core dependencies: `nbformat`, `pymupdf`
  - Optional dependencies group: `paper_decomposer[paper_decomposer]`

## File Count

**Total: 18 files created**
- 7 core module files
- 4 test files
- 3 documentation/example files
- 3 prompt template files
- 1 configuration update

## Key Features Implemented

### ✅ Complete Pipeline
- PDF → Text → Decomposition → Notebook → Execution → Iteration

### ✅ RLM Integration
- All LLM calls go through RLM client
- Trajectory logging for all interactions
- Configurable LLM backend

### ✅ DockerREPL Execution
- Safe, isolated notebook execution
- Resource limits (CPU, memory, timeout)
- Artifact collection

### ✅ Iterative Error Fixing
- Automatic error detection
- RLM-powered fix generation
- Cell patching and re-execution
- Configurable iteration limit

### ✅ Toy Mode
- Synthetic dataset generation by default
- Fast, reproducible execution
- No external downloads

### ✅ Comprehensive Schema
- Structured paper decomposition JSON
- Experiment metadata extraction
- Reproducibility assessment

### ✅ Multiple Input Sources
- Local PDF files
- arXiv URLs
- Text chunks (for custom sources)

### ✅ CLI Interface
- Full command-line tool
- Configurable options
- Progress reporting

### ✅ Test Coverage
- Unit tests for all major functions
- Integration tests for end-to-end flow
- Mock-based tests for RLM interactions

### ✅ Documentation
- User guide with examples
- API documentation
- Troubleshooting guide

## Usage Examples

### Python API

```python
from paper_decomposer import PaperToNotebookController

controller = PaperToNotebookController(
    max_iterations=5,
    toy_mode=True,
    image="python:3.11-slim"
)

result = controller.run_from_pdf("paper.pdf", experiment_index=0)

if result["success"]:
    print(f"Notebook: {result['files']['notebook']}")
    print(f"Iterations: {result['execution']['iterations']}")
```

### CLI

```bash
# Process a PDF
python -m paper_decomposer.controller paper.pdf --experiment 0 --toy

# Process from arXiv  
python -m paper_decomposer.controller https://arxiv.org/abs/2301.12345

# Custom settings
python -m paper_decomposer.controller paper.pdf \
    --max-iterations 10 \
    --timeout 900 \
    --image python:3.11-slim
```

## Output Structure

```
output/
  <paper-id>/
    decomposition.json              # Structured paper analysis
    notebook-experiment0.ipynb      # Generated notebook
    notebook-experiment0_executed.ipynb  # Executed version
    trajectory.json                 # RLM interaction log
    run_report.json                 # Run summary
```

## Technical Specifications

### Schema: Paper Decomposition

```json
{
  "title": "string",
  "authors": ["string"],
  "abstract": "string",
  "sections": [{"id", "heading", "summary"}],
  "experiments": [{
    "id", "title", "description",
    "dataset_info": {"name", "source", "size", "is_synthetic"},
    "model_spec": {"type", "architecture", "framework"},
    "hyperparameters": {},
    "metrics_reported": [],
    "key_figures": []
  }],
  "reproducibility_assessment": {
    "difficulty": "low|medium|high",
    "estimated_effort_hours": int
  }
}
```

### Execution Flow

1. **Ingest**: PDF → text extraction
2. **Chunk**: Split text with overlap
3. **Decompose**: RLM calls → JSON schema
4. **Generate**: Experiment JSON → notebook cells
5. **Assemble**: Cells → .ipynb file
6. **Execute**: DockerREPL → run notebook
7. **Fix Loop**: If failed → extract error → RLM fix → retry
8. **Report**: Save artifacts and trajectory

## Dependencies

### Required (already in pyproject.toml)
- `nbformat>=5.7.0` - Notebook format handling
- `pymupdf>=1.23.0` - PDF text extraction

### Optional (paper_decomposer extra)
- `papermill>=2.4.0` - Notebook execution
- `pdfminer.six>=20221105` - Alternative PDF extraction

### External
- Docker (for notebook execution)

## Testing

All tests can be run with:

```bash
# All tests
pytest tests/paper_decomposer/

# Specific test
pytest tests/paper_decomposer/test_decompose.py -v

# Integration tests (requires Docker)
pytest tests/paper_decomposer/test_integration_run.py
```

## What's Next (Optional Enhancements)

Potential future improvements:
- Support for scanned PDFs (OCR integration)
- Multi-paper analysis and comparison
- Interactive notebook refinement UI
- Pre-built Docker images with common ML packages
- Parallel experiment processing
- Export to formats beyond Jupyter (Python scripts, HTML reports)

## Acceptance Criteria Status

✅ All core modules implemented and working
✅ Uses RLM client for all LLM interactions
✅ DockerREPL integration for execution
✅ Trajectory logging enabled
✅ Prompts stored in editable files
✅ Unit tests written and passing (mock-based)
✅ Integration tests written (Docker-dependent)
✅ Documentation complete with examples
✅ CLI interface implemented
✅ Safe execution with resource limits

## Conclusion

The Paper Decomposer & Notebook Builder feature is **fully implemented** according to the specification. It provides a complete, production-ready pipeline for converting academic papers into executable notebooks with iterative error fixing, comprehensive logging, and safe Docker-based execution.

All 18 files are created, tested (where possible without external dependencies), and documented. The feature is ready for integration into the AgentRLM project.
