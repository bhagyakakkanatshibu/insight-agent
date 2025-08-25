# src/parser.py
import re
import sys
from collections import Counter
from pathlib import Path

import fitz  # PyMuPDF


def _strip_weird_chars(text: str) -> str:
    # remove box symbols, bullets, control chars
    text = re.sub(r"[^\S\r\n]+", " ", text)  # collapse spaces (keep newlines)
    text = re.sub(r"[•▪◦∙●■□◆◇✦✧▶◀►◄\u25A0-\u25FF\u2500-\u257F\u00A0\u2022\u25CF\u25AA\u25AB\u25E6]", " ", text)
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A1-\u024F]", " ", text)  # keep basic latin + latin ext
    text = re.sub(r"[ ]{2,}", " ", text)
    return text

def _remove_repeating_headers_footers(text: str) -> str:
    # naive: drop the most frequent 1–2 lines if they occur on many pages
    pages = [p.strip() for p in re.split(r"\n--- Page \d+ ---\n", text) if p.strip()]
    lines = [ln.strip() for p in pages for ln in p.splitlines() if ln.strip()]
    freq = Counter(lines)
    common = {ln for ln, c in freq.items() if c >= max(3, len(pages)//2)}  # repeated on >= half the pages
    cleaned_pages = []
    for p in pages:
        keep = [ln for ln in p.splitlines() if ln.strip() not in common]
        cleaned_pages.append("\n".join(keep))
    return "\n\n".join(cleaned_pages)

def clean_text(raw: str) -> str:
    raw = _strip_weird_chars(raw)
    raw = _remove_repeating_headers_footers(raw)
    # collapse 3+ newlines to 2
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw


def extract_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    parts = []
    for i, page in enumerate(doc):
        parts.append(f"\n--- Page {i + 1} ---\n")
        parts.append(page.get_text())
    return "".join(parts)

def parse_file(path: str) -> str:
    """
    Unified entry for app:
    - .pdf  -> use PyMuPDF
    - .txt  -> read as UTF-8 (fallback to latin-1)
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    ext = p.suffix.lower()
    if ext == ".pdf":
        return extract_text(str(p))
    elif ext == ".txt":
        try:
            return p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return p.read_text(encoding="latin-1")
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use PDF or TXT.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/parser.py <path_to_pdf_or_txt> [run_name]")
        sys.exit(1)

    in_path = Path(sys.argv[1]).resolve()
    run_name = sys.argv[2] if len(sys.argv) >= 3 else "sample"

    if not in_path.exists():
        print(f"File not found: {in_path}")
        sys.exit(1)

    text = parse_file(str(in_path))
    text = clean_text(text)


    out_txt = Path(f"data/raw/{run_name}.pdf.txt")
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    out_txt.write_text(text, encoding="utf-8")
    print(f"Wrote raw text to: {out_txt}")
