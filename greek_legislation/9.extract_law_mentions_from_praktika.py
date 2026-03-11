import re
from pathlib import Path
import pandas as pd
from collections import Counter

TXT_DIR = Path("praktika_2025_2026/docx_text")
OUT_FILE = Path("praktika_2025_2026/law_mentions.csv")

def main():
    if not TXT_DIR.exists():
        print(f"[ERROR] Δεν βρέθηκε ο φάκελος: {TXT_DIR}")
        return

    # Regex για να πιάνουμε μοτίβα όπως: ν. 1234/2025, Ν. 1234/2025, νόμος 1234/2025, Νόμου 1234/2025
    # Group 1: Αριθμός νόμου (2-5 ψηφία)
    # Group 2: Έτος (4 ψηφία)
    law_pattern = re.compile(r'(?:ν\.|Ν\.|νόμος|Νόμος|νόμου|Νόμου|νόμω)\s*(\d{2,5})\s*/\s*(\d{4})')

    all_mentions = []

    print("[INFO] Σάρωση αρχείων .txt για αναφορές σε νόμους...")
    for txt_file in TXT_DIR.glob("*.txt"):
        try:
            text = txt_file.read_text(encoding="utf-8")
            matches = law_pattern.findall(text)
            for num, year in matches:
                # Καθαρισμός και ομαδοποίηση (π.χ. "1234/2025")
                all_mentions.append(f"{num}/{year}")
        except Exception as e:
            print(f"[ERROR] Αποτυχία ανάγνωσης του {txt_file.name}: {e}")

    if not all_mentions:
        print("[WARN] Δεν βρέθηκαν αναφορές σε νόμους.")
        return

    # Μέτρηση συχνότητας αναφορών (ποιος νόμος συζητήθηκε περισσότερο;)
    counts = Counter(all_mentions)

    # Δημιουργία DataFrame, διαχωρισμός αριθμού/έτους και ταξινόμηση
    df = pd.DataFrame(counts.items(), columns=["Law", "Mentions"])
    df[["Law_Num", "Law_Year"]] = df["Law"].str.split("/", expand=True)
    df = df.sort_values(by="Mentions", ascending=False).reset_index(drop=True)

    # Αποθήκευση σε CSV
    df.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
    
    print(f"\n[OK] Εντοπίστηκαν {len(df)} μοναδικοί νόμοι.")
    print(f"[OK] Τα αποτελέσματα αποθηκεύτηκαν στο: {OUT_FILE}\n")
    print("--- Top 10 πιο συζητημένοι νόμοι ---")
    print(df.head(10).to_string(index=False))

if __name__ == "__main__":
    main()