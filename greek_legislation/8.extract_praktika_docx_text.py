from pathlib import Path
from docx import Document

DOCX_DIR = Path("praktika_2025_2026/docx")
OUT_DIR = Path("praktika_2025_2026/docx_text")
OUT_DIR.mkdir(exist_ok=True)

for docx_file in DOCX_DIR.glob("*.docx"):
    out_file = OUT_DIR / (docx_file.stem + ".txt")
    if out_file.exists():
        print(f"[SKIP] {out_file}")
        continue

    doc = Document(str(docx_file))
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    out_file.write_text(text, encoding="utf-8")
    print(f"[OK] {out_file}")