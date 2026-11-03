import os
import time
import json
from pathlib import Path
from typing import Dict, Any

from markitdown import MarkItDown
from langdetect import detect, LangDetectException

# Supported file extensions according to MarkItDown documentation
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".html", ".htm", ".txt", ".csv"}

MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB

def validate_file(uploaded_file) -> Dict[str, Any]:
    """Validate the uploaded Streamlit ``UploadedFile``.

    Returns a dictionary with ``valid`` (bool) and a ``message`` explaining
    the result.  On success the original ``uploaded_file`` object is also
    returned under the ``file`` key.
    """
    if uploaded_file is None:
        return {"valid": False, "message": "No file uploaded."}
    if uploaded_file.size == 0:
        return {"valid": False, "message": "Uploaded file is empty."}
    if uploaded_file.size > MAX_UPLOAD_SIZE:
        return {"valid": False, "message": f"File exceeds the maximum allowed size of {MAX_UPLOAD_SIZE // (1024 * 1024)} MB."}
    _, ext = os.path.splitext(uploaded_file.name)
    ext = ext.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return {"valid": False, "message": f"Unsupported file extension '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."}
    return {"valid": True, "file": uploaded_file, "extension": ext}

def _save_to_temp(uploaded_file) -> Path:
    """Write the uploaded file to a temporary location and return the path.

    The caller is responsible for deleting the file when finished.
    """
    temp_dir = Path("./tmp")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / uploaded_file.name
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return temp_path

def _compute_markdown_stats(md_text: str) -> Dict[str, int]:
    """Calculate simple statistics from a Markdown string.

    Returns a dictionary containing:
    * ``word_count``
    * ``char_count``
    * ``line_count``
    * ``heading_count`` (lines starting with '#')
    * ``table_row_count`` (Markdown table rows – lines that start and end with '|')
    """
    lines = md_text.splitlines()
    line_count = len(lines)
    char_count = len(md_text)
    word_count = len(md_text.split())
    heading_count = sum(1 for l in lines if l.lstrip().startswith("#"))
    table_row_count = sum(1 for l in lines if l.strip().startswith("|") and l.strip().endswith("|"))
    return {
        "word_count": word_count,
        "char_count": char_count,
        "line_count": line_count,
        "heading_count": heading_count,
        "table_row_count": table_row_count,
    }

def detect_language(md_text: str) -> str:
    """Detect the language of the extracted Markdown text.
    Returns a short ISO‑639‑1 code (e.g., "en", "es"). If detection fails, returns "unknown".
    """
    try:
        import re
        plain = re.sub(r"[#>\*\-\[\]\(\)\`]+", " ", md_text)
        return detect(plain)
    except LangDetectException:
        return "unknown"
    except Exception:
        return "unknown"

def convert_document(file_path: str) -> Dict[str, Any]:
    """Convert a document to Markdown using MarkItDown.

    Returns a dict with keys ``markdown``, ``metadata`` and ``stats`` (including language).
    """
    start = time.time()
    try:
        converter = MarkItDown()
        result = converter.convert(file_path)
        markdown_text = result.text_content
    except Exception as exc:
        raise RuntimeError(f"MarkItDown conversion failed: {exc}") from exc
    duration = time.time() - start
    input_size = os.path.getsize(file_path)
    output_size = len(markdown_text.encode("utf-8"))
    stats = _compute_markdown_stats(markdown_text)
    stats["language"] = detect_language(markdown_text)
    metadata = {
        "input_size_bytes": input_size,
        "output_size_bytes": output_size,
        "duration_seconds": round(duration, 3),
    }
    return {"markdown": markdown_text, "metadata": metadata, "stats": stats}

def cleanup_temp(path: Path) -> None:
    """Remove temporary files safely."""
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass
