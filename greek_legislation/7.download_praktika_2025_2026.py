import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

BASE_URL = "https://www.hellenicparliament.gr"
INDEX_URL = f"{BASE_URL}/praktika/synedriaseis-olomeleias"

OUT_DIR = Path("praktika_2025_2026")
OUT_DIR.mkdir(exist_ok=True)

HTML_DIR = OUT_DIR / "html"
DOCX_DIR = OUT_DIR / "docx"
HTML_DIR.mkdir(exist_ok=True)
DOCX_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

MAX_PAGES = 200
SLEEP_SECONDS = 1


def safe_filename(text: str) -> str:
    text = re.sub(r"[^\w\-.]+", "_", str(text), flags=re.UNICODE)
    return text.strip("._")[:180] or "document"


def get_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.text


def download_file(url: str, dest: Path):
    with requests.get(url, headers=HEADERS, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 128):
                if chunk:
                    f.write(chunk)


def page_url(page_no: int) -> str:
    return f"{INDEX_URL}?pageNo={page_no}"


def extract_session_links(index_html: str):
    soup = BeautifulSoup(index_html, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(" ", strip=True)

        if "sessionRecord=" in href and "synedriaseis-olomeleias" in href.lower():
            links.append((urljoin(BASE_URL, href), text))

    seen = set()
    out = []
    for item in links:
        if item[0] not in seen:
            seen.add(item[0])
            out.append(item)
    return out


def extract_docx_link(html: str):
    soup = BeautifulSoup(html, "html.parser")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(" ", strip=True)
        if href.lower().endswith(".docx") or text.lower().endswith(".docx"):
            return urljoin(BASE_URL, href), Path(href).name

    m = re.search(r'https?://[^"\']+\.docx', html, flags=re.IGNORECASE)
    if m:
        url = m.group(0)
        return url, Path(url).name

    m = re.search(r'(/UserFiles/[^"\']+\.docx)', html, flags=re.IGNORECASE)
    if m:
        url = urljoin(BASE_URL, m.group(1))
        return url, Path(url).name

    return None, None


def get_session_record_id(url: str):
    qs = parse_qs(urlparse(url).query)
    vals = qs.get("sessionRecord", [])
    return vals[0] if vals else ""


def extract_date_from_html(html: str):
    m = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", html)
    if m:
        return pd.to_datetime(m.group(1), dayfirst=True, errors="coerce")
    return pd.NaT


def main():
    all_sessions = []
    seen = set()

    for page_no in range(1, MAX_PAGES + 1):
        url = page_url(page_no)
        print(f"[INFO] Listing page {page_no}: {url}")

        html = get_html(url)
        page_links = extract_session_links(html)

        if not page_links:
            break

        new_count = 0
        for item in page_links:
            if item[0] not in seen:
                seen.add(item[0])
                all_sessions.append(item)
                new_count += 1

        print(f"[INFO] found={len(page_links)}, new={new_count}")

        if new_count == 0:
            break

        time.sleep(SLEEP_SECONDS)

    rows = []

    for i, (url, link_text) in enumerate(all_sessions, start=1):
        print(f"[INFO] ({i}/{len(all_sessions)}) {url}")
        try:
            html = get_html(url)
            dt = extract_date_from_html(html)

            if pd.isna(dt) or dt.year not in [2025, 2026]:
                continue

            session_id = get_session_record_id(url)
            docx_url, docx_name = extract_docx_link(html)

            html_name = safe_filename(f"{dt.date()}_{session_id}.html")
            html_path = HTML_DIR / html_name
            html_path.write_text(html, encoding="utf-8")

            docx_path_str = ""
            if docx_url:
                if not docx_name:
                    docx_name = f"{dt.date()}_{session_id}.docx"
                docx_name = safe_filename(docx_name)
                docx_path = DOCX_DIR / docx_name
                if not docx_path.exists():
                    download_file(docx_url, docx_path)
                docx_path_str = str(docx_path)
                print(f"[OK] {docx_path}")

            rows.append({
                "url": url,
                "session_record": session_id,
                "session_date": dt.date(),
                "link_text": link_text,
                "html_file": str(html_path),
                "docx_url": docx_url or "",
                "docx_file": docx_path_str,
            })

        except Exception as e:
            print(f"[FAIL] {url}: {e}")

        time.sleep(SLEEP_SECONDS)

    pd.DataFrame(rows).to_csv(
        OUT_DIR / "praktika_index_2025_2026.csv",
        index=False,
        encoding="utf-8-sig"
    )


if __name__ == "__main__":
    main()