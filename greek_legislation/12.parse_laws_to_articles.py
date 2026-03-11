import re
import pandas as pd
from pathlib import Path

TXT_DIR = Path("praktika_2025_2026/top_laws_txt")
OUT_FILE = Path("praktika_2025_2026/laws_articles.csv")

def main():
    if not TXT_DIR.exists():
        print(f"[ERROR] Δεν βρέθηκε ο φάκελος {TXT_DIR}")
        return

    all_articles = []
    
    # Regex για να εντοπίζει "Άρθρο 1", "ΑΡΘΡΟ 2Α" κλπ. στην αρχή μιας γραμμής
    article_pattern = re.compile(r'^(?:Άρθρο|ΑΡΘΡΟ|Α ρ θ ρ ο)\s*([0-9]+[Α-Ωα-ω]?)\b', re.MULTILINE)

    for txt_file in TXT_DIR.glob("*.txt"):
        law_name = txt_file.stem  # π.χ. Law_4887_2022
        text = txt_file.read_text(encoding="utf-8")

        # Εύρεση όλων των επικεφαλίδων άρθρων
        matches = list(article_pattern.finditer(text))

        if not matches:
            print(f"[WARN] Δεν μπόρεσα να κάνω parse τα άρθρα στο {law_name}.")
            continue

        for i in range(len(matches)):
            article_num = matches[i].group(1)
            # Το κείμενο του άρθρου ξεκινάει μετά τον τίτλο του
            start_idx = matches[i].end()
            # Και τελειώνει εκεί που ξεκινάει το επόμενο άρθρο (ή στο τέλος του αρχείου)
            end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)

            article_text = text[start_idx:end_idx].strip()

            # Κρατάμε μόνο άρθρα που έχουν κάποιο ουσιαστικό κείμενο (π.χ. > 20 χαρακτήρες)
            if len(article_text) > 20:
                all_articles.append({
                    "Law": law_name,
                    "Article": article_num,
                    "Text": article_text,
                    "Character_Count": len(article_text)
                })
                
        print(f"[OK] {law_name}: Διαχωρίστηκε σε {len(matches)} άρθρα.")

    # Αποθήκευση σε DataFrame και CSV
    if all_articles:
        df = pd.DataFrame(all_articles)
        df.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
        print(f"\n[INFO] Εξαιρετικά! Αποθηκεύτηκαν {len(df)} συνολικά άρθρα στο {OUT_FILE}.")
    else:
        print("\n[WARN] Δεν εξήχθησαν άρθρα.")

if __name__ == "__main__":
    main()