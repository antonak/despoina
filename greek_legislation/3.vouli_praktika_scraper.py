import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin

BASE_URL = "https://www.hellenicparliament.gr"
INDEX_URL = f"{BASE_URL}/praktika/synedriaseis-olomeleias"

OUT_DIR = Path("vouli_praktika")
OUT_DIR.mkdir(exist_ok=True)

HTML_DIR = OUT_DIR / "html"
DOCX_DIR = OUT_DIR / "docx"
TXT_DIR = OUT_DIR / "txt_extracted"
HTML_DIR.mkdir(exist_ok=True)
DOCX_DIR.mkdir(exist_ok=True)
TXT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


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


def extract_session_links(index_html: str):
    soup = BeautifulSoup(index_html, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(" ", strip=True)

        if "sessionRecord=" in href and "synedriaseis-olomeleias" in href:
            full_url = urljoin(BASE_URL, href)
            links.append((full_url, text))

    seen = set()
    uniq = []
    for url, text in links:
        if url not in seen:
            seen.add(url)
            uniq.append((url, text))

    return uniq


def extract_title(html: str):
    soup = BeautifulSoup(html, "html.parser")
    for h in soup.find_all(["h1", "h2"]):
        txt = h.get_text(" ", strip=True)
        if txt:
            return txt
    return "praktika"


def extract_date(text: str):
    m = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", text)
    if m:
        return m.group(1)
    return ""


def extract_docx_link(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # 1) κανονικό anchor προς docx
    for a in soup.find_all("a", href=True):
        href = a["href"]
        txt = a.get_text(" ", strip=True)
        if href.lower().endswith(".docx") or txt.lower().endswith(".docx"):
            return urljoin(BASE_URL, href), txt or Path(href).name

    # 2) regex για πλήρες URL .docx μέσα στο HTML
    m = re.search(r'https?://[^"\']+\.docx', html, flags=re.IGNORECASE)
    if m:
        url = m.group(0)
        return url, Path(url).name

    # 3) regex για relative path .docx
    m = re.search(r'(/UserFiles/[^"\']+\.docx)', html, flags=re.IGNORECASE)
    if m:
        url = urljoin(BASE_URL, m.group(1))
        return url, Path(url).name

    return None, None


def save_plain_text_from_html(html: str, out_path: Path):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    out_path.write_text(text, encoding="utf-8")


def main():
    print(f"[INFO] Κατεβάζω index: {INDEX_URL}")
    index_html = get_html(INDEX_URL)

    session_links = extract_session_links(index_html)
    print(f"[INFO] Βρέθηκαν {len(session_links)} links συνεδριάσεων")

    session_links = session_links[:20]
    rows = []

    for i, (url, link_text) in enumerate(session_links, start=1):
        print(f"[INFO] ({i}/{len(session_links)}) {url}")

        try:
            html = get_html(url)
            title = extract_title(html)
            date_str = extract_date(html)

            base_name = safe_filename(f"{date_str}_{title}")[:150]
            html_path = HTML_DIR / f"{base_name}.html"
            txt_path = TXT_DIR / f"{base_name}.txt"

            html_path.write_text(html, encoding="utf-8")
            save_plain_text_from_html(html, txt_path)

            docx_url, docx_name = extract_docx_link(html)

            downloaded_docx = ""
            if docx_url:
                if not docx_name:
                    docx_name = f"{base_name}.docx"
                docx_name = safe_filename(docx_name)
                docx_path = DOCX_DIR / docx_name
                download_file(docx_url, docx_path)
                downloaded_docx = str(docx_path)
                print(f"[OK] DOCX: {docx_path}")
            else:
                print(f"[WARN] Δεν βρέθηκε docx link για {url}")

            rows.append({
                "url": url,
                "link_text": link_text,
                "title": title,
                "date": date_str,
                "html_file": str(html_path),
                "txt_file": str(txt_path),
                "docx_url": docx_url or "",
                "docx_file": downloaded_docx,
            })

        except Exception as e:
            print(f"[FAIL] {url}: {e}")
            rows.append({
                "url": url,
                "link_text": link_text,
                "title": "",
                "date": "",
                "html_file": "",
                "txt_file": "",
                "docx_url": "",
                "docx_file": "",
                "error": str(e),
            })

        time.sleep(1)

    out_csv = OUT_DIR / "praktika_index.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[INFO] Αποθηκεύτηκε: {out_csv}")


if __name__ == "__main__":
    main()