import re
import time
import pandas as pd
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

INPUT_CSV = "greek_laws_sample/laws_metadata_sample.csv"
OUTPUT_DIR = Path("downloaded_laws")
OUTPUT_DIR.mkdir(exist_ok=True)

BASE_URL = "https://search.et.gr"
SIMPLE_SEARCH_URL = f"{BASE_URL}/el/simple-search/"


def safe_filename(text: str) -> str:
    text = re.sub(r"[^\w\-.]+", "_", str(text), flags=re.UNICODE)
    return text.strip("._")[:180] or "document"


def get_year(value):
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        return None
    return int(dt.year)


def accept_cookies(page):
    for sel in [
        "button:has-text('Αποδοχή')",
        "text=Αποδοχή",
        "button:has-text('Accept')",
        "text=Accept",
    ]:
        try:
            page.locator(sel).first.click(timeout=1500)
            page.wait_for_timeout(800)
            return
        except Exception:
            pass


def wait_for_search_form(page):
    # Περιμένουμε τα labels της φόρμας, όχι το title/menu link.
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1500)

    targets = [
        "text=Έτος",
        "text=Τεύχος",
        "text=Αριθμός Φ.Ε.Κ.",
        "text=Λέξεις-κλειδιά",
        "text=Αναζήτηση",
    ]

    ok = 0
    for sel in targets:
        try:
            page.locator(sel).first.wait_for(state="visible", timeout=7000)
            ok += 1
        except Exception:
            pass

    if ok < 3:
        debug_file = OUTPUT_DIR / "debug_form_not_found.html"
        debug_file.write_text(page.content(), encoding="utf-8")
        raise RuntimeError(
            f"Δεν εντοπίστηκε σωστά η φόρμα αναζήτησης (βρέθηκαν {ok}/5 labels). "
            f"Δες το {debug_file}"
        )


def fill_by_label_or_fallback(page, label_text: str, value: str) -> bool:
    # Προσπάθεια με get_by_label
    try:
        field = page.get_by_label(label_text, exact=False)
        if field.count() > 0:
            field.first.fill(value)
            return True
    except Exception:
        pass

    # Fallback: πλησιέστερο input μετά το label
    xpaths = [
        f"//*[contains(normalize-space(), '{label_text}')]/following::input[1]",
        f"//*[contains(normalize-space(), '{label_text}')]/following::textarea[1]",
    ]
    for xp in xpaths:
        try:
            loc = page.locator(f"xpath={xp}")
            if loc.count() > 0:
                loc.first.fill(value)
                return True
        except Exception:
            pass

    # τελευταίο fallback: πρώτο text/number input
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
                page.wait_for_timeout(300)
                continue

            # τεύχος Α
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


def click_search(page) -> bool:
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
    page.wait_for_timeout(2500)

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


def scrape_one(page, context, year: int, feknum: int):
    page.goto(SIMPLE_SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
    accept_cookies(page)
    wait_for_search_form(page)

    year_done, issue_done = select_year_and_issue(page, year)
    fek_done = fill_by_label_or_fallback(page, "Αριθμός Φ.Ε.Κ.", str(feknum))

    if not click_search(page):
        return {
            "status": "search_click_failed",
            "year_done": year_done,
            "issue_done": issue_done,
            "fek_done": fek_done,
            "fek_page": None,
            "pdf_url": None,
        }

    page.wait_for_timeout(3000)

    found = find_pdf_or_fek_link(page)
    if not found:
        dbg = OUTPUT_DIR / f"debug_after_search_{year}_{feknum}.html"
        dbg.write_text(page.content(), encoding="utf-8")
        return {
            "status": "not_found",
            "year_done": year_done,
            "issue_done": issue_done,
            "fek_done": fek_done,
            "fek_page": None,
            "pdf_url": None,
            "debug_html": str(dbg),
        }

    if found["kind"] == "pdf":
        return {
            "status": "ok",
            "year_done": year_done,
            "issue_done": issue_done,
            "fek_done": fek_done,
            "fek_page": None,
            "pdf_url": found["url"],
        }

    fek_page = found["url"]
    pdf_url = resolve_pdf_from_fek_page(page, fek_page)

    return {
        "status": "ok" if pdf_url else "fek_found_no_pdf",
        "year_done": year_done,
        "issue_done": issue_done,
        "fek_done": fek_done,
        "fek_page": fek_page,
        "pdf_url": pdf_url,
    }


def main():
    df = pd.read_csv(INPUT_CSV)
    df["year"] = df["publication_date"].apply(get_year)
    df["feknum"] = pd.to_numeric(df["feknum"], errors="coerce")

    sample = df.dropna(subset=["year", "feknum"]).head(10).copy()
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="el-GR", accept_downloads=True)
        page = context.new_page()

        for _, row in sample.iterrows():
            year = int(row["year"])
            feknum = int(row["feknum"])
            law = row.get("law", "")
            description = row.get("description", "")

            print(f"\n[INFO] Ψάχνω ΦΕΚ {feknum}/A/{year} για νόμο {law}")

            try:
                res = scrape_one(page, context, year, feknum)
                out = {
                    "law": law,
                    "year": year,
                    "feknum": feknum,
                    "description": description,
                    **res,
                }

                if res.get("pdf_url"):
                    fname = safe_filename(f"{year}_fekA_{feknum}_law_{law}.pdf")
                    dest = OUTPUT_DIR / fname
                    download_with_context(context, res["pdf_url"], dest)
                    print(f"[OK] Κατέβηκε: {dest}")
                    out["downloaded_file"] = str(dest)
                else:
                    print(
                        f"[WARN] status={res['status']} "
                        f"(year={res.get('year_done')}, issue={res.get('issue_done')}, fek={res.get('fek_done')})"
                    )
                    if res.get("debug_html"):
                        print(f"[DEBUG] html={res['debug_html']}")

                results.append(out)
                time.sleep(1)

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

        browser.close()

    pd.DataFrame(results).to_csv(
        OUTPUT_DIR / "download_results.csv",
        index=False,
        encoding="utf-8-sig"
    )


if __name__ == "__main__":
    main()