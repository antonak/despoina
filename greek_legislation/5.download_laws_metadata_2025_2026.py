import os
import requests
import pandas as pd
from pathlib import Path

API_URL = "https://data.gov.gr/api/v1/query/gov-et-laws"
API_KEY = os.getenv("DATA_GOV_GR_API_KEY")

OUT_DIR = Path("laws_2025_2026")
OUT_DIR.mkdir(exist_ok=True)

HEADERS = {"Accept": "application/json"}
if API_KEY:
    HEADERS["Authorization"] = f"Token {API_KEY}"


def get_json(url):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()


def normalize_to_df(payload):
    if isinstance(payload, list):
        return pd.json_normalize(payload)
    if isinstance(payload, dict):
        for key in ["results", "data", "items", "records"]:
            if key in payload and isinstance(payload[key], list):
                return pd.json_normalize(payload[key])
        return pd.json_normalize(payload)
    raise ValueError("Unexpected JSON format")


def main():
    payload = get_json(API_URL)
    df = normalize_to_df(payload)

    print("Columns:", df.columns.tolist())
    print("Rows before filtering:", len(df))

    df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce")
    df["year"] = df["publication_date"].dt.year

    df = df[df["year"].isin([2025, 2026])].copy()

    print("Rows after filtering for 2025-2026:", len(df))

    out_csv = OUT_DIR / "laws_metadata_2025_2026.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print("Saved:", out_csv)


if __name__ == "__main__":
    main()