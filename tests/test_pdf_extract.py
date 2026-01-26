from __future__ import annotations

from pathlib import Path

from infrastructure.ingestion.docs_loader import load_pdf


def main() -> None:
    base_dir = Path(__file__).with_name("samples")
    pdf_path = base_dir / "iso_21500.pdf"
    if not pdf_path.exists():
        print(f"[PDF-EXTRACT] sample PDF not found: {pdf_path}")
        return
    payload = load_pdf(pdf_path, base_dir)
    text = payload.text or ""
    print(f"[PDF-EXTRACT] doc_id={payload.doc_id} chars={len(text)}")
    if text:
        print("[PDF-EXTRACT] preview:")
        print(text[:500])


if __name__ == "__main__":
    main()
