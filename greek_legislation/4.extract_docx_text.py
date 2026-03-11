from pathlib import Path
from docx import Document

DOCX_DIR = Path("vouli_praktika/docx")
OUT_DIR = Path("vouli_praktika/docx_text")
OUT_DIR.mkdir(exist_ok=True)

for docx_file in DOCX_DIR.glob("*.docx"):
    doc = Document(str(docx_file))
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    out_file = OUT_DIR / (docx_file.stem + ".txt")
    out_file.write_text(text, encoding="utf-8")
    print(f"[OK] {out_file}")