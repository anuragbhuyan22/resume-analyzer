"""
core/parser.py — Extract raw text from PDF and DOCX resumes.
"""
import re
import pdfplumber
from docx import Document


def extract_text(filepath: str, ext: str) -> str:
    """Dispatch to the correct parser based on file extension."""
    if ext == "pdf":
        return _extract_pdf(filepath)
    elif ext == "docx":
        return _extract_docx(filepath)
    return ""


def _extract_pdf(filepath: str) -> str:
    """Extract text from all pages of a PDF using pdfplumber."""
    pages = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
    raw = "\n".join(pages)
    return _clean(raw)


def _extract_docx(filepath: str) -> str:
    """Extract paragraph text from a DOCX file."""
    doc = Document(filepath)
    lines = [para.text for para in doc.paragraphs if para.text.strip()]
    # Also grab text from tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    lines.append(cell.text.strip())
    return _clean("\n".join(lines))


def _clean(text: str) -> str:
    """Normalise whitespace and remove non-printable characters."""
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)   # keep printable ASCII
    text = re.sub(r"[ \t]{2,}", " ", text)           # collapse spaces
    text = re.sub(r"\n{3,}", "\n\n", text)            # collapse blank lines
    return text.strip()
