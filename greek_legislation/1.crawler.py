import os
import re
import json
import requests
import pandas as pd
from pathlib import Path
from urllib.parse import urlparse

API_URL = "https://data.gov.gr/api/v1/query/gov-et-laws"

# Αν το data.gov.gr ζητήσει API key, βάλε το εδώ ως environment variable:
# export DATA_GOV_GR_API_KEY="....."
API_KEY = os.getenv("DATA_GOV_GR_API_KEY")

OUT_DIR = Path("greek_laws_sample")
OUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "Accept": "application/json",
}
if API_KEY:
    # Αν το endpoint θέλει auth, συνήθως το βάζεις έτσι.
    HEADERS["Authorization"] = f"Token {API_KEY}"

# -----------------------------
# Helper functions
# -----------------------------
def get_json(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def normalize_to_df(payload):
    """
    Προσπαθεί να μετατρέψει ό,τι επιστρέψει το API σε pandas DataFrame.
    """
    if isinstance(payload, list):
        return pd.json_normalize(payload)

    if isinstance(payload, dict):
        # συνήθη patterns
        for key in ["results", "data", "items", "records"]:
            if key in payload and isinstance(payload[key], list):
                return pd.json_normalize(payload[key])

        # fallback: αν είναι dict από dicts / mixed
        return pd.json_normalize(payload)

    raise ValueError("Μη αναμενόμενη μορφή JSON από το API")

def find_col(df, patterns):
    """
    Βρίσκει την πρώτη στήλη που ταιριάζει σε κάποιο regex pattern.
    """
    cols = list(df.columns)
    for pat in patterns:
        rgx = re.compile(pat, re.IGNORECASE)
        for c in cols:
            if rgx.search(c):
                return c
    return None

def safe_filename(text, default="document.pdf"):
    text = str(text) if text is not None else default
    text = re.sub(r"[^\w\-\.]+", "_", text, flags=re.UNICODE)
    text = text.strip("._")
    return text or default

def download_file(url, dest):
    r = requests.get(url, stream=True, timeout=120)
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 128):
            if chunk:
                f.write(chunk)

# -----------------------------
# 1) Πάρε δεδομένα από το API
# -----------------------------
payload = get_json(API_URL)
df = normalize_to_df(payload)

print("Στήλες που βρέθηκαν:")
print(df.columns.tolist())
print(f"\nΠλήθος εγγραφών που γύρισαν: {len(df)}")

# -----------------------------
# 2) Βρες πιθανές χρήσιμες στήλες
# -----------------------------
title_col = find_col(df, [r"title", r"titl", r"τίτ", r"descr", r"περιγραφ"])
year_col = find_col(df, [r"year", r"έτος", r"etos"])
issue_col = find_col(df, [r"issue", r"τεύχος", r"teyx"])
law_num_col = find_col(df, [r"law.*number", r"number", r"arithm", r"αριθ"])
type_col = find_col(df, [r"type", r"kind", r"category", r"κατηγ"])
url_col = find_col(df, [r"pdf", r"url", r"link", r"download"])

print("\nΧαρτογράφηση στηλών:")
print("title_col  =", title_col)
print("year_col   =", year_col)
print("issue_col  =", issue_col)
print("law_num_col=", law_num_col)
print("type_col   =", type_col)
print("url_col    =", url_col)

# -----------------------------
# 3) Ελαφρύ φιλτράρισμα
#    Συνήθως οι νόμοι δημοσιεύονται σε τεύχος Α
# -----------------------------
work = df.copy()

if year_col:
    work[year_col] = pd.to_numeric(work[year_col], errors="coerce")
    work = work[work[year_col] >= 2020]   # άλλαξε το όπως θέλεις

if issue_col:
    # κράτα τεύχος Α αν υπάρχει
    work = work[work[issue_col].astype(str).str.contains(r"\bA\b|Α", na=False)]

if type_col:
    # αν υπάρχει τύπος, προσπάθησε να κρατήσεις εγγραφές που μοιάζουν με νόμους
    work = work[work[type_col].astype(str).str.contains(r"νόμ|nom", case=False, na=False)]

# κράτα μόνο μερικές εγγραφές για αρχή
sample_n = 20
sample = work.head(sample_n).copy()

print(f"\nΕγγραφές μετά το φιλτράρισμα: {len(sample)}")

# -----------------------------
# 4) Σώσε metadata
# -----------------------------
sample.to_csv(OUT_DIR / "laws_metadata_sample.csv", index=False, encoding="utf-8-sig")
sample.to_json(OUT_DIR / "laws_metadata_sample.json", orient="records", force_ascii=False, indent=2)

print(f"Αποθηκεύτηκαν metadata στο: {OUT_DIR}")

# -----------------------------
# 5) Κατέβασε PDF / links αν υπάρχουν
# -----------------------------
downloaded = 0

if url_col:
    pdf_dir = OUT_DIR / "pdfs"
    pdf_dir.mkdir(exist_ok=True)

    for i, row in sample.iterrows():
        url = row.get(url_col)
        if not isinstance(url, str) or not url.startswith("http"):
            continue

        # όνομα αρχείου
        title = row.get(title_col, "") if title_col else ""
        law_no = row.get(law_num_col, "") if law_num_col else ""
        year = row.get(year_col, "") if year_col else ""

        parsed = urlparse(url)
        ext = Path(parsed.path).suffix or ".pdf"
        fname = safe_filename(f"{year}_{law_no}_{title}")[:180] + ext

        try:
            download_file(url, pdf_dir / fname)
            downloaded += 1
            print(f"[OK] {fname}")
        except Exception as e:
            print(f"[FAIL] {url} -> {e}")

print(f"\nΚατέβηκαν {downloaded} αρχεία.")
print("Τέλος.")