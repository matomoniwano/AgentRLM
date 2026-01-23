"""
Paper Decomposer & Notebook Builder

A feature that takes academic papers (PDF or arXiv URL), extracts structure and experiments,
generates runnable Jupyter notebooks to reproduce key figures/experiments, and executes them
in DockerREPL with iterative fixes through RLM.
"""

from .controller import PaperToNotebookController
from .decompose import decompose_paper
from .ingest import extract_text_from_pdf, fetch_arxiv_pdf
from .notebook_gen import generate_notebook_cells, assemble_notebook
from .executor import run_notebook_docker

__all__ = [
    "PaperToNotebookController",
    "decompose_paper",
    "extract_text_from_pdf",
    "fetch_arxiv_pdf",
    "generate_notebook_cells",
    "assemble_notebook",
    "run_notebook_docker",
]
