import subprocess
import re

def extract_info(pdf_path: str) -> dict:
    result = subprocess.run(
        ["pdfinfo", pdf_path], capture_output=True, text=True, check=True
    )
    info = {"title": None, "author": None, "page_count": 0, "pdf_version": None}
    for line in result.stdout.splitlines():
        if line.startswith("Title:"):
            info["title"] = line[len("Title:"):].strip() or None
        elif line.startswith("Author:"):
            info["author"] = line[len("Author:"):].strip() or None
        elif line.startswith("Pages:"):
            info["page_count"] = int(line[len("Pages:"):].strip())
        elif line.startswith("PDF version:"):
            info["pdf_version"] = line[len("PDF version:"):].strip()
    return info