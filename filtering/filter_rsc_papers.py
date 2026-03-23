# -*- coding: utf-8 -*-
"""
filtering/filter_rsc_papers.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Filter RSC articles scraped by immersion_scraper.py.

Source structure
----------------
data/rsc_immersion/
  <query_folder>/
    <safe_doi>/
      article.html
      metadata.json

What this script does
---------------------
1. Walks every <query_folder>/<safe_doi>/ directory under BASE_SOURCE_DIR.
2. Reads article.html and checks for co-occurrence of property and
   application keywords (same logic as filter_elsevier_papers.py).
3. Copies matching article.html + metadata.json into BASE_TARGET_DIR,
   preserving the <query_folder>/<safe_doi>/ sub-structure.
4. Collects the "title" field from every metadata.json in the source tree
   (regardless of keyword match) and writes them to:
       data/rsc_titles.json   – full list as a JSON array
       data/rsc_titles.txt    – one title per line (plain text)

Usage
-----
    python filtering/filter_rsc_papers.py
"""

import json
import os
import shutil

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ROOT_DIR        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE_SOURCE_DIR = os.path.join(ROOT_DIR, "data")
BASE_TARGET_DIR = os.path.join(ROOT_DIR, "rsc_filtered")
TITLES_JSON     = os.path.join(ROOT_DIR, "rsc_filtered", "rsc_titles.json")
TITLES_TXT      = os.path.join(ROOT_DIR, "rsc_filtered", "rsc_titles.txt")

MY_KEYWORDS = [
    # Properties (first 4)
    "thermal conductivity",
    "viscosity",
    "dielectric constant",
    "dielectric strength",
    "relative permittivity"
    # Applications (remainder)
    "immersion cooling",
    "cooling performance",
    "server cooling",
    "data center",
    "esters",
    "polyurethane",
    "polymer",
    "organic fluid",
    "dielectric fluid",
    "heat transfer fluid",
    "electrical insulation",
    "dielectric breakdown",
    "dielectric dissipation factor",
    "phase cooling"
]

PROPERTY_KEYWORDS     = [k.lower() for k in MY_KEYWORDS[:4]]
APPLICATION_KEYWORDS  = [k.lower() for k in MY_KEYWORDS[4:]]


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def filter_rsc_papers(
    base_source_dir: str = BASE_SOURCE_DIR,
    base_target_dir: str = BASE_TARGET_DIR,
    titles_json:     str = TITLES_JSON,
    titles_txt:      str = TITLES_TXT,
) -> None:
    """
    Walk *base_source_dir*, filter articles by keyword co-occurrence in
    article.html, and collect titles from every metadata.json.

    :param base_source_dir: Root of the scraped RSC data tree.
    :param base_target_dir: Destination for filtered copies.
    :param titles_json:     Output path for the JSON titles list.
    :param titles_txt:      Output path for the plain-text titles list.
    """
    os.makedirs(base_target_dir, exist_ok=True)
    os.makedirs(os.path.dirname(titles_json), exist_ok=True)

    total_scanned  = 0
    total_relevant = 0
    all_titles: list[str] = []

    print(f"Source  : {base_source_dir}")
    print(f"Target  : {base_target_dir}")

    # Walk two levels deep: <query_folder>/<doi_folder>/
    for query_folder in sorted(os.listdir(base_source_dir)):
        query_path = os.path.join(base_source_dir, query_folder)
        if not os.path.isdir(query_path):
            continue

        for doi_folder in sorted(os.listdir(query_path)):
            doi_path   = os.path.join(query_path, doi_folder)
            html_path  = os.path.join(doi_path, "article.html")
            meta_path  = os.path.join(doi_path, "metadata.json")

            if not os.path.isdir(doi_path):
                continue

            # --- Collect title from metadata.json (all articles) ---
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as fh:
                        meta = json.load(fh)
                    title = meta.get("title", "").strip()
                except Exception as exc:
                    print(f"  Warning: could not read {meta_path}: {exc}")

            # --- Keyword filtering on article.html ---
            if not os.path.exists(html_path):
                continue

            total_scanned += 1
            try:
                with open(html_path, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read().lower()
            except Exception as exc:
                print(f"  Warning: could not read {html_path}: {exc}")
                continue

            has_property    = any(p in content for p in PROPERTY_KEYWORDS)
            has_application = any(a in content for a in APPLICATION_KEYWORDS)

            if not (has_property and has_application):
                continue
            if title:
                all_titles.append(title)
            # --- Copy matching article to target ---
            target_doi_dir = os.path.join(base_target_dir, query_folder, doi_folder)
            os.makedirs(target_doi_dir, exist_ok=True)

            for fname in ("article.html", "metadata.json"):
                src = os.path.join(doi_path, fname)
                dst = os.path.join(target_doi_dir, fname)
                if os.path.exists(src) and not os.path.exists(dst):
                    shutil.copy2(src, dst)

            total_relevant += 1

    # --- Write title lists ---
    with open(titles_json, "a", encoding="utf-8") as fh:
        json.dump(all_titles, fh, ensure_ascii=False, indent=2)

    with open(titles_txt, "a", encoding="utf-8") as fh:
        fh.write("\n".join(all_titles) + "\n")

    print(f"\nProcessing complete.")
    print(f"  Articles scanned  : {total_scanned}")
    print(f"  Relevant articles : {total_relevant}  →  {base_target_dir}")
    print(f"  Titles collected  : {len(all_titles)}")
    print(f"  Titles JSON       : {titles_json}")
    print(f"  Titles TXT        : {titles_txt}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    filter_rsc_papers()
