# -*- coding: utf-8 -*-
"""
web-scrap/immersion_scraper.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

RSC scraper for immersion-cooling literature.

Workflow
--------
1. Run RscSearchScraper.perform_search() for each (query, page) pair to collect
   article metadata (DOI, html_url) from search result pages.
2. Run RscHtmlScraper on each article's HTML URL to extract full document
   metadata (title, abstract, authors, journal …).
3. Save each article's raw HTML and a companion JSON metadata file under
   OUTPUT_DIR / <safe_doi>/.

Usage
-----
    # Use default queries from ../keywords.txt (one query per line)
    python immersion_scraper.py

    # Override queries on the command line
    python immersion_scraper.py "immersion cooling" "dielectric fluid battery"

    # Set page range via env vars
    PAGE_START=1 PAGE_END=10 python immersion_scraper.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import urllib.request
import urllib.error
import re
import argparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
def safe_js_click(self):
    """Overrides the default .click() to use JavaScript, bypassing overlaps."""
    self._parent.execute_script("arguments[0].click();", self)

# Replace the standard Selenium click with our JS-based version
WebElement.click = safe_js_click
# ---------------------------------------------------------------------------
# Path setup – allow running from inside web-scrap/ or from batterydatabase/
# ---------------------------------------------------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from chemdataextractor_immersion.chemdataextractor15.scrape.pub.rsc import (
    RscSearchScraper,
    RscHtmlScraper,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults (all overridable via CLI or env vars)
# ---------------------------------------------------------------------------
DEFAULT_KEYWORDS_FILE = os.path.join(ROOT_DIR, "keywords.txt")
DEFAULT_OUTPUT_DIR    = os.path.join(ROOT_DIR, "data")
DEFAULT_PAGE_START    = int(os.environ.get("PAGE_START", 1))
DEFAULT_PAGE_END      = int(os.environ.get("PAGE_END",   20))
SEARCH_DELAY_S        = float(os.environ.get("SEARCH_DELAY", 2.0))
DOWNLOAD_DELAY_S      = float(os.environ.get("DOWNLOAD_DELAY", 1.5))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_driver() -> webdriver.Chrome:
    """Return a headless Chrome driver (auto-managed binary)."""
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080") 
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return webdriver.Chrome(service=service, options=options)


def _safe_name(doi: str) -> str:
    """Convert a DOI into a filesystem-safe string."""
    return doi.replace("/", "_").replace(":", "_").replace(" ", "_")


def _build_downloaded_dois(output_dir: str) -> set[str]:
    """Return safe DOI names already present as subfolders under any query folder in output_dir."""
    downloaded: set[str] = set()
    if not os.path.isdir(output_dir):
        return downloaded
    for query_folder in os.scandir(output_dir):
        if not query_folder.is_dir():
            continue
        for doi_folder in os.scandir(query_folder.path):
            if doi_folder.is_dir():
                downloaded.add(doi_folder.name)
    return downloaded


def _build_filtered_dois(filtered_dir: str) -> set[str]:
    """Return safe DOI stems already present as .html files under filtered_dir."""
    filtered: set[str] = set()
    if not os.path.isdir(filtered_dir):
        return filtered
    for entry in os.scandir(filtered_dir):
        if entry.is_file() and entry.name.endswith(".html"):
            filtered.add(entry.name[:-5])  # strip .html suffix
    return filtered


def _query_folder_name(query: str) -> str:
    """
    Derive a short folder name from a query string.

    Rule: use the first quoted term (content inside the first pair of "…");
    fall back to the full query when no quotes are present.

    Examples
    --------
    '"dielectric strength" OR "dielectric constant"'  →  'dielectric_strength'
    '"immersion cooling"'                              →  'immersion_cooling'
    'heat transfer fluid'                             →  'heat_transfer_fluid'
    """
    match = re.search(r'"([^"]+)"', query)
    phrase = match.group(1) if match else query
    # Keep only alphanumeric and spaces, then replace spaces with underscores
    phrase = re.sub(r'[^\w\s]', '', phrase).strip()
    return re.sub(r'\s+', '_', phrase).lower()


def _resolve_html_url(doi: str) -> str | None:
    """
    Follow the doi.org redirect and extract the RSC article-HTML URL.

    Returns None when the URL cannot be resolved.
    """
    try:
        r = urllib.request.urlopen(
            "http://doi.org/" + doi,
            timeout=20,
        )
        text = r.read().decode("utf-8", errors="replace")
    except Exception as exc:
        log.warning("Could not resolve DOI %s: %s", doi, exc)
        return None

    matches = re.findall(r'https://pubs\.rsc\.org/en/content/articlehtml/[^"\'>\s]+', text)
    if not matches:
        log.warning("No articlehtml URL found for DOI %s", doi)
        return None
    return matches[0].rstrip("\"'")


def _download_html(url: str) -> bytes | None:
    """Download raw HTML bytes from *url*. Returns None on failure."""
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        log.warning("Download failed (%s): %s", url, exc)
        return None


def load_queries(keywords_file: str) -> list[str]:
    """Read non-empty, non-comment lines from *keywords_file*."""
    if not os.path.isfile(keywords_file):
        log.warning("Keywords file not found: %s", keywords_file)
        return []
    with open(keywords_file, encoding="utf-8") as fh:
        return [
            line.strip()
            for line in fh
            if line.strip() and not line.startswith("#")
        ]


# ---------------------------------------------------------------------------
# Core scraping functions
# ---------------------------------------------------------------------------

def search_query(scraper: RscSearchScraper, query: str, page_range: range, driver: webdriver.Chrome) -> list[dict]:
    """
    Run perform_search for each page in *page_range* and return a deduplicated
    list of article dicts with at least {doi, html_url, title, landing_url}.
    """
    seen_dois: set[str] = set()
    results: list[dict] = []

    for page in page_range:
        log.info("  Searching page %d for '%s' …", page, query)
        try:
            entities = scraper.run(query, page=page)
        except Exception as exc:
            log.error("  Search failed on page %d: %s", page, exc)
            time.sleep(SEARCH_DELAY_S)
            continue
        if page == page_range[0]:
                try:
                    accept_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                    )
                    accept_btn.click() # This will also use the new safe_js_click
                except:
                    pass
        if not entities:
            log.info("  No results on page %d – stopping early.", page)
            break

        page_count = 0
        for item in entities:
            data = item.serialize() if hasattr(item, "serialize") else dict(item)
            doi = data.get("doi", "")
            if not doi or doi in seen_dois:
                continue
            seen_dois.add(doi)
            results.append(data)
            page_count += 1

        log.info("  Page %d: %d new articles (cumulative %d).", page, page_count, len(results))
        time.sleep(SEARCH_DELAY_S)

    return results


def scrape_html_document(html_scraper: RscHtmlScraper, html_url: str) -> dict:
    """
    Run RscHtmlScraper on *html_url* and return the first entity as a dict.
    Returns an empty dict on failure.
    """
    try:
        entities = html_scraper.run(html_url)
        if entities:
            data = entities[0].serialize() if hasattr(entities[0], "serialize") else dict(entities[0])
            return data
    except Exception as exc:
        log.warning("  HtmlScraper failed for %s: %s", html_url, exc)
    return {}


def process_articles(
    search_results: list[dict],
    html_scraper: RscHtmlScraper,
    output_dir: str,
    query_folder: str,
    downloaded_dois: set[str],
    filtered_dois: set[str],
) -> None:
    """
    For each article in *search_results*:
      - Resolve / use the html_url
      - Scrape full metadata with RscHtmlScraper
      - Download raw HTML
      - Write <output_dir>/<query_folder>/<safe_doi>/article.html and metadata.json

    Skips DOIs already present in any query subfolder of output_dir or in filtered_dois.
    Prints per-query skip/download statistics on completion.
    """
    total = len(search_results)
    skipped_existing = 0   # already in another query folder or this one
    skipped_filtered = 0   # already in filtered_rsc
    downloaded = 0

    for idx, article in enumerate(search_results, start=1):
        doi      = article.get("doi", "")
        html_url = article.get("html_url", "")

        if not doi:
            log.warning("Skipping result with no DOI: %s", article)
            total -= 1
            continue

        safe = _safe_name(doi)

        # Skip if already present in filtered_rsc
        if safe in filtered_dois:
            log.info("  [%d/%d] In filtered_rsc, skipping: %s", idx, total, doi)
            skipped_filtered += 1
            continue

        # Skip if already downloaded under any query folder
        if safe in downloaded_dois:
            log.info("  [%d/%d] Already downloaded, skipping: %s", idx, total, doi)
            skipped_existing += 1
            continue

        article_dir = os.path.join(output_dir, query_folder, safe)
        html_path   = os.path.join(article_dir, "article.html")
        meta_path   = os.path.join(article_dir, "metadata.json")

        log.info("  [%d/%d] Processing: %s", idx, total, doi)
        os.makedirs(article_dir, exist_ok=True)

        # Resolve HTML URL if missing
        if not html_url:
            html_url = _resolve_html_url(doi)
        if not html_url:
            log.warning("  No HTML URL for %s – skipping.", doi)
            continue

        # --- Full metadata via RscHtmlScraper ---
        if not os.path.exists(meta_path):
            doc_meta = scrape_html_document(html_scraper, html_url)
            merged   = {**article, **doc_meta}  # html-page metadata wins
            with open(meta_path, "w", encoding="utf-8") as fh:
                json.dump(merged, fh, ensure_ascii=False, indent=2)
            log.debug("  Metadata written: %s", meta_path)

        # --- Raw HTML download ---
        if not os.path.exists(html_path):
            raw = _download_html(html_url)
            if raw:
                with open(html_path, "wb") as fh:
                    fh.write(raw)
                log.debug("  HTML written: %s", html_path)
                downloaded_dois.add(safe)
                downloaded += 1

        time.sleep(DOWNLOAD_DELAY_S)

    skipped_total = skipped_existing + skipped_filtered
    log.info(
        "  Query stats — total: %d | downloaded: %d | skipped: %d "
        "(already downloaded: %d, in filtered_rsc: %d)",
        total, downloaded, skipped_total, skipped_existing, skipped_filtered,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run(
    queries: list[str],
    page_start: int = DEFAULT_PAGE_START,
    page_end:   int = DEFAULT_PAGE_END,
    output_dir: str = DEFAULT_OUTPUT_DIR,
) -> None:
    """
    Main loop: for each query, search RSC, then download & scrape each article.

    :param queries:    List of search query strings.
    :param page_start: First page of search results to retrieve (1-indexed).
    :param page_end:   Last page of search results to retrieve (inclusive).
    :param output_dir: Root directory for saved HTML and metadata files.
    """
    if not queries:
        log.error("No queries provided – nothing to do.")
        return

    os.makedirs(output_dir, exist_ok=True)
    page_range = range(page_start, page_end + 1)

    # Build skip sets once before the query loop
    downloaded_dois = _build_downloaded_dois(output_dir)
    filtered_dir    = os.path.join("../data", "filtered_rsc")
    filtered_dois   = _build_filtered_dois(filtered_dir)
    log.info(
        "Pre-scan: %d DOIs already downloaded, %d in filtered_rsc — these will be skipped.",
        len(downloaded_dois), len(filtered_dois),
    )

    driver       = _build_driver()
    html_scraper = RscHtmlScraper()

    try:
        search_scraper = RscSearchScraper(driver=driver)

        for q_idx, query in enumerate(queries, start=1):
            log.info("=" * 60)
            log.info("Query %d/%d: '%s'  (pages %d–%d)",
                     q_idx, len(queries), query, page_start, page_end)
            log.info("=" * 60)

            search_results = search_query(search_scraper, query, page_range, driver)
            log.info("Found %d unique articles for '%s'.", len(search_results), query)

            if search_results:
                query_folder = _query_folder_name(query)
                process_articles(
                    search_results, html_scraper, output_dir, query_folder,
                    downloaded_dois, filtered_dois,
                )

    finally:
        driver.quit()
        log.info("Browser closed. Output directory: %s", output_dir)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RSC immersion-cooling scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "queries",
        nargs="*",
        help="Search queries. If omitted, reads from --keywords-file.",
    )
    parser.add_argument(
        "--keywords-file", "-k",
        default=DEFAULT_KEYWORDS_FILE,
        help=f"Path to keywords file (default: {DEFAULT_KEYWORDS_FILE})",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--page-start", "-s",
        type=int,
        default=DEFAULT_PAGE_START,
        help=f"First search-results page to fetch (default: {DEFAULT_PAGE_START})",
    )
    parser.add_argument(
        "--page-end", "-e",
        type=int,
        default=DEFAULT_PAGE_END,
        help=f"Last search-results page to fetch, inclusive (default: {DEFAULT_PAGE_END})",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    queries = args.queries or load_queries(args.keywords_file)
    if not queries:
        log.error(
            "No queries found. Pass them on the command line or add them to %s",
            args.keywords_file,
        )
        sys.exit(1)

    run(
        queries=queries,
        page_start=args.page_start,
        page_end=args.page_end,
        output_dir=args.output_dir,
    )
