import os
import time
import pandas as pd
from pathlib import Path
from playwright.sync_api import sync_playwright

INPUT_CSV = Path("praktika_2025_2026/law_mentions.csv")
OUTPUT_DIR = Path("praktika_2025_2026/top_laws_pdfs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SEARCH_URL = "https://search.et.gr/el/search-legislation/"

def accept_cookies(page):
    try:
        page.locator("text=Αποδοχή").first.click(timeout=2000)
        page.wait_for_timeout(500)
    except:
        pass

def main():
    if not INPUT_CSV.exists():
        print(f"[ERROR] Δεν βρέθηκε το αρχείο {INPUT_CSV}")
        return

    df = pd.read_csv(INPUT_CSV)
    top_laws = df.head(20)

    print(f"[INFO] Θα κατεβάσουμε τους {len(top_laws)} πιο συζητημένους νόμους...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        for _, row in top_laws.iterrows():
            law_num = str(row['Law_Num']).strip()
            law_year = str(row['Law_Year']).strip()
            
            pdf_filename = OUTPUT_DIR / f"Law_{law_num}_{law_year}.pdf"
            
            if pdf_filename.exists():
                print(f"[SKIP] Το {pdf_filename.name} υπάρχει ήδη.")
                continue

            print(f"\n[*] Αναζήτηση για Ν. {law_num}/{law_year}...")
            
            try:
                page.goto(SEARCH_URL, wait_until="domcontentloaded")
                accept_cookies(page)
                page.wait_for_timeout(1000)

                # --- Η ΔΙΟΡΘΩΣΗ ΕΙΝΑΙ ΕΔΩ ---
                # 1. Επιλογή Έτους (ως dropdown) με χρήση του ID και force=True
                page.locator("#search_per_year").select_option(law_year, force=True)
                
                # 2. Εισαγωγή Αριθμού Νόμου (χρησιμοποιούμε το .first για να αποφύγουμε strict mode violation)
                try:
                    # Προσπαθούμε να βρούμε το πεδίο με το ID του
                    page.locator("#search_law").fill(law_num)
                except:
                    # Αν αποτύχει, πάμε μέσω του label
                    page.get_by_label("Αριθμός").first.fill(law_num)

                # Πάτημα του κουμπιού "Αναζήτηση"
                page.get_by_role("button", name="Αναζήτηση").first.click()
                page.wait_for_timeout(2000) # Αναμονή για τα αποτελέσματα

                # Εντοπισμός του PDF link στα αποτελέσματα
                pdf_link = page.locator("a[href$='.pdf']").first
                
                if pdf_link.count() > 0:
                    with page.expect_download() as download_info:
                        pdf_link.click()
                    download = download_info.value
                    download.save_as(pdf_filename)
                    print(f"[OK] Αποθηκεύτηκε: {pdf_filename.name}")
                else:
                    print(f"[WARN] Δεν βρέθηκε PDF στα αποτελέσματα για Ν. {law_num}/{law_year}")

            except Exception as e:
                print(f"[FAIL] Σφάλμα στον Ν. {law_num}/{law_year}: {e}")

            time.sleep(2)

        browser.close()
    
    print("\n[INFO] Η διαδικασία ολοκληρώθηκε!")

if __name__ == "__main__":
    main()