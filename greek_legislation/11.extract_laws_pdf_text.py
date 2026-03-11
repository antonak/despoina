import os
from pathlib import Path
from pypdf import PdfReader

PDF_DIR = Path("praktika_2025_2026/top_laws_pdfs")
TXT_DIR = Path("praktika_2025_2026/top_laws_txt")

# Δημιουργία του φακέλου για τα .txt αν δεν υπάρχει
TXT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    if not PDF_DIR.exists():
        print(f"[ERROR] Δεν βρέθηκε ο φάκελος {PDF_DIR}")
        return

    pdf_files = list(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"[WARN] Δεν βρέθηκαν αρχεία PDF στον φάκελο {PDF_DIR}")
        return

    print(f"[INFO] Ξεκινάει η εξαγωγή κειμένου από {len(pdf_files)} PDF αρχεία...")

    for pdf_path in pdf_files:
        txt_filename = TXT_DIR / f"{pdf_path.stem}.txt"
        
        # Αν το έχουμε ήδη κάνει extract, το προσπερνάμε
        if txt_filename.exists():
            print(f"[SKIP] Το {txt_filename.name} υπάρχει ήδη.")
            continue

        try:
            reader = PdfReader(pdf_path)
            extracted_text = []
            
            # Διάβασμα κάθε σελίδας
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
            
            full_text = "\n".join(extracted_text)
            
            # Αποθήκευση στο .txt αρχείο
            txt_filename.write_text(full_text, encoding="utf-8")
            print(f"[OK] Εξήχθη κείμενο: {txt_filename.name} ({len(reader.pages)} σελίδες)")
            
        except Exception as e:
            print(f"[FAIL] Πρόβλημα με το αρχείο {pdf_path.name}: {e}")

    print("\n[INFO] Η εξαγωγή ολοκληρώθηκε!")

if __name__ == "__main__":
    main()