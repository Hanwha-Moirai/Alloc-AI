from pathlib import Path
from typing import Tuple

import fitz


def extract_pdf_text(path: Path) -> Tuple[str, int]:
    doc = fitz.open(path)
    texts = []
    for page in doc:
        texts.append(page.get_text("text"))
    page_count = doc.page_count
    doc.close()
    text = "\n".join(texts).strip()
    return text, page_count
