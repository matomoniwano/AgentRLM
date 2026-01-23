"""
PDF and arXiv paper ingestion utilities.
"""

import os
import re
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from pdfminer.high_level import extract_text as pdfminer_extract
    HAS_PDFMINER = True
except ImportError:
    HAS_PDFMINER = False


def extract_text_from_pdf(path: str, max_pages: Optional[int] = None) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        path: Path to the PDF file
        max_pages: Maximum number of pages to extract (None for all pages)
        
    Returns:
        Combined text from the PDF
        
    Raises:
        ImportError: If neither PyMuPDF nor pdfminer is available
        FileNotFoundError: If the PDF file doesn't exist
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF file not found: {path}")
    
    if HAS_PYMUPDF:
        return _extract_with_pymupdf(path, max_pages)
    elif HAS_PDFMINER:
        return _extract_with_pdfminer(path, max_pages)
    else:
        raise ImportError(
            "No PDF extraction library available. "
            "Install PyMuPDF (pip install pymupdf) or pdfminer.six (pip install pdfminer.six)"
        )


def _extract_with_pymupdf(path: str, max_pages: Optional[int] = None) -> str:
    """Extract text using PyMuPDF (fitz)."""
    doc = fitz.open(path)
    texts = []
    
    page_limit = min(len(doc), max_pages) if max_pages else len(doc)
    
    for page_num in range(page_limit):
        page = doc[page_num]
        texts.append(page.get_text())
    
    doc.close()
    return "\n\n".join(texts)


def _extract_with_pdfminer(path: str, max_pages: Optional[int] = None) -> str:
    """Extract text using pdfminer.six."""
    text = pdfminer_extract(path, page_numbers=None if max_pages is None else list(range(max_pages)))
    return text


def fetch_arxiv_pdf(arxiv_url: str, output_dir: Optional[str] = None) -> str:
    """
    Download a PDF from arXiv and return the local path.
    
    Args:
        arxiv_url: arXiv URL (e.g., "https://arxiv.org/abs/2301.12345" or "https://arxiv.org/pdf/2301.12345.pdf")
        output_dir: Directory to save the PDF (uses temp directory if None)
        
    Returns:
        Local path to the downloaded PDF
        
    Raises:
        ValueError: If the URL is not a valid arXiv URL
        urllib.error.URLError: If download fails
    """
    # Extract arXiv ID
    arxiv_id_match = re.search(r'(\d{4}\.\d{4,5})', arxiv_url)
    if not arxiv_id_match:
        raise ValueError(f"Invalid arXiv URL: {arxiv_url}")
    
    arxiv_id = arxiv_id_match.group(1)
    
    # Construct PDF URL
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    # Determine output path
    if output_dir is None:
        output_dir = tempfile.gettempdir()
    
    output_path = os.path.join(output_dir, f"{arxiv_id}.pdf")
    
    # Download
    print(f"Downloading arXiv paper {arxiv_id} from {pdf_url}...")
    urllib.request.urlretrieve(pdf_url, output_path)
    print(f"Downloaded to {output_path}")
    
    return output_path


def chunk_text(text: str, max_chunk_size: int = 8000, overlap: int = 200) -> list[str]:
    """
    Split text into chunks with overlap for better context preservation.
    
    Args:
        text: Text to chunk
        max_chunk_size: Maximum characters per chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chunk_size
        
        # If this is not the last chunk, try to break at a paragraph or sentence
        if end < len(text):
            # Look for paragraph break
            last_double_newline = text.rfind('\n\n', start, end)
            if last_double_newline > start:
                end = last_double_newline
            else:
                # Look for sentence break
                last_period = text.rfind('. ', start, end)
                if last_period > start:
                    end = last_period + 1
        
        chunks.append(text[start:end])
        start = end - overlap if end < len(text) else end
    
    return chunks
