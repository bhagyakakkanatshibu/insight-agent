# src/segmenter.py
import re
import sys
from pathlib import Path


def detect_sections(text: str) -> dict:
    lines = text.splitlines()
    sections, buffer = {}, []
    current_header = "Preamble"

    def is_header(line: str) -> bool:
        s = line.strip()
        if len(s) < 4: 
            return False
        # all caps with limited punctuation AND short length → likely section header
        if (s.isupper() and len(s) <= 60 and re.match(r"^[A-Z0-9 &/\-]+$", s)):
            return True
     # numbered headers like "1. Introduction" or "2) Methods"
        if re.match(r"^\d{1,2}[\.\)]\s+[A-Z].{2,60}$", s):
            return True
        # resume/report common headers (case-insensitive)
        if re.match(r"^(profile summary|summary|experience|work experience|professional experience|projects|education|skills|publications|notable projects|additional details)$", s, re.I):
            return True
        return False


    for line in lines:
        if is_header(line):
            if buffer:
                sections[current_header] = "\n".join(buffer).strip()
            current_header = line.strip()
            buffer = []
        else:
            buffer.append(line)

    if buffer:
        sections[current_header] = "\n".join(buffer).strip()
    return sections

def segment_text(text: str) -> dict:
    """
    App-friendly wrapper. Falls back to coarse chunks if no headers found.
    """
    sections = detect_sections(text)
    if sections and any(v.strip() for v in sections.values()):
        return sections

    # Fallback: chunk every ~1200 chars on blank lines
    chunks, chunk, count = {}, [], 0
    for para in text.split("\n\n"):
        chunk.append(para)
        if sum(len(p) for p in chunk) > 1200:
            count += 1
            chunks[f"Section {count}"] = "\n\n".join(chunk).strip()
            chunk = []
    if chunk:
        count += 1
        chunks[f"Section {count}"] = "\n\n".join(chunk).strip()
    return chunks

if __name__ == "__main__":
    run_name = sys.argv[1] if len(sys.argv) >= 2 else "sample"
    in_txt = Path(f"data/raw/{run_name}.pdf.txt")
    if not in_txt.exists():
        print(f"Run parser first. Text not found: {in_txt}")
        sys.exit(1)

    text = in_txt.read_text(encoding="utf-8")
    sections = segment_text(text)
    out_dir = Path(f"data/processed/{run_name}")
    out_dir.mkdir(parents=True, exist_ok=True)

    for title, content in sections.items():
        safe = re.sub(r"[^\w\-]+", "_", title.strip().lower()).strip("_")
        (out_dir / f"{safe}.txt").write_text(content, encoding="utf-8")

    print(f"Wrote {len(sections)} sections to: {out_dir}")
