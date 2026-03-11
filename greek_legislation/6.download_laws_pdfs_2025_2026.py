import re
import time
import pandas as pd
from pathlib import Path
from playwright.sync_api import sync_playwright

INPUT_CSV = "laws_2025_2026/laws_metadata_2025_2026.csv"
OUTPUT_DIR = Path("laws_2025_2026/pdfs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://search.et.gr"
SIMPLE_SEARCH_URL = f"{BASE_URL}/el/simple-search/"


def safe_filename(text: str) -> str:
    text = re.sub(r"[^\w\-.]+", "_", str(text), flags=re.UNICODE)
    return text.strip("._")[:180] or "document"


def accept_cookies(page):
    for sel in [
        "button:has-text('Αποδοχή')",
        "text=Αποδοχή",
        "button:has-text('Accept')",
        "text=Accept",
    ]:
        try:
            page.locator(sel).first.click(timeout=1500)
            page.wait_for_timeout(500)
            return
        except Exception:
            pass


def wait_for_search_form(page):
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1500)


def fill_by_label_or_fallback(page, label_text: str, value: str) -> bool:
    try:
        field = page.get_by_label(label_text, exact=False)
        if field.count() > 0:
            field.first.fill(value)
            return True
    except Exception:
        pass

    try:
        inputs = page.locator("input")
        for i in range(inputs.count()):
            inp = inputs.nth(i)
            typ = (inp.get_attribute("type") or "").lower()
            if typ in ("text", "search", "number", ""):
                inp.fill(value)
                return True
    except Exception:
        pass

    return False


def select_year_and_issue(page, year: int):
    selects = page.locator("select")
    year_done = False
    issue_done = False

    for i in range(selects.count()):
        sel = selects.nth(i)
        try:
            options = sel.locator("option")
            texts = [options.nth(j).inner_text().strip() for j in range(options.count())]

            if str(year) in texts and not year_done:
                try:
                    sel.select_option(label=str(year))
                except Exception:
                    sel.select_option(value=str(year))
                year_done = True
                page.wait_for_timeout(200)
                continue

            if not issue_done and any(t in texts for t in ["Α", "A", "1"]):
                for candidate in ["Α", "A", "1"]:
                    try:
                        sel.select_option(label=candidate)
                        issue_done = True
                        break
                    except Exception:
                        try:
                            sel.select_option(value=candidate)
                            issue_done = True
                            break
                        except Exception:
                            pass
        except Exception:
            pass

    return year_done, issue_done


def click_search(page):
    for sel in [
        "button:has-text('Αναζήτηση')",
        "input[type='submit']",
        "text=Αναζήτηση",
    ]:
        try:
            page.locator(sel).first.click(timeout=3000)
            page.wait_for_timeout(2500)
            return True
        except Exception:
            pass
    return False


def find_pdf_or_fek_link(page):
    pdf_links = page.locator("a[href$='.pdf'], a[href*='.pdf']")
    if pdf_links.count() > 0:
        href = pdf_links.first.get_attribute("href")
        if href:
            return {"kind": "pdf", "url": href}

    fek_links = page.locator("a[href*='/fek/']")
    if fek_links.count() > 0:
        href = fek_links.first.get_attribute("href")
        if href:
            return {"kind": "fek", "url": href}

    html = page.content()
    m = re.search(r'https?://[^"\']+\.pdf', html, flags=re.IGNORECASE)
    if m:
        return {"kind": "pdf", "url": m.group(0)}

    m = re.search(r'href="([^"]*/fek/[^"]*)"', html, flags=re.IGNORECASE)
    if m:
        return {"kind": "fek", "url": m.group(1)}

    return None


def resolve_pdf_from_fek_page(page, fek_url: str):
    if fek_url.startswith("/"):
        fek_url = BASE_URL + fek_url

    page.goto(fek_url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)

    pdf_links = page.locator("a[href$='.pdf'], a[href*='.pdf']")
    if pdf_links.count() > 0:
        href = pdf_links.first.get_attribute("href")
        if href:
            return href

    html = page.content()
    m = re.search(r'https?://[^"\']+\.pdf', html, flags=re.IGNORECASE)
    if m:
        return m.group(0)

    return None


def download_with_context(context, url: str, dest: Path):
    if url.startswith("/"):
        url = BASE_URL + url

    resp = context.request.get(url, timeout=120000)
    if not resp.ok:
        raise RuntimeError(f"Download failed: HTTP {resp.status} for {url}")
    dest.write_bytes(resp.body())


def scrape_one(page, year: int, feknum: int):
    page.goto(SIMPLE_SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
    accept_cookies(page)
    wait_for_search_form(page)

    year_done, issue_done = select_year_and_issue(page, year)
    fek_done = fill_by_label_or_fallback(page, "Αριθμός Φ.Ε.Κ.", str(feknum))

    if not (year_done and issue_done and fek_done):
        return None

    if not click_search(page):
        return None

    page.wait_for_timeout(2500)

    found = find_pdf_or_fek_link(page)
    if not found:
        return None

    if found["kind"] == "pdf":
        return found["url"]

    return resolve_pdf_from_fek_page(page, found["url"])


def main():
    df = pd.read_csv(INPUT_CSV)
    df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce")
    df["year"] = df["publication_date"].dt.year
    df["feknum"] = pd.to_numeric(df["feknum"], errors="coerce")

    df = df.dropna(subset=["year", "feknum"]).copy()

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="el-GR", accept_downloads=True)
        page = context.new_page()

        for _, row in df.iterrows():
            year = int(row["year"])
            feknum = int(row["feknum"])
            law = row.get("law", "")
            description = row.get("description", "")

            filename = safe_filename(f"{year}_fekA_{feknum}_law_{law}.pdf")
            dest = OUTPUT_DIR / filename

            if dest.exists():
                print(f"[SKIP] {dest}")
                results.append({
                    "law": law,
                    "year": year,
                    "feknum": feknum,
                    "description": description,
                    "status": "already_downloaded",
                    "downloaded_file": str(dest),
                })
                continue

            print(f"[INFO] Ψάχνω ΦΕΚ {feknum}/A/{year} για νόμο {law}")

            try:
                pdf_url = scrape_one(page, year, feknum)
                if pdf_url:
                    download_with_context(context, pdf_url, dest)
                    print(f"[OK] Κατέβηκε: {dest}")
                    status = "ok"
                else:
                    print(f"[WARN] Δεν βρέθηκε PDF για ΦΕΚ {feknum}/A/{year}")
                    status = "not_found"

                results.append({
                    "law": law,
                    "year": year,
                    "feknum": feknum,
                    "description": description,
                    "status": status,
                    "downloaded_file": str(dest) if dest.exists() else "",
                })

            except Exception as e:
                print(f"[FAIL] ΦΕΚ {feknum}/A/{year}: {e}")
                results.append({
                    "law": law,
                    "year": year,
                    "feknum": feknum,
                    "description": description,
                    "status": "error",
                    "error": str(e),
                })

            time.sleep(1)

        browser.close()

    pd.DataFrame(results).to_csv(
        "laws_2025_2026/download_results.csv",
        index=False,
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    main()