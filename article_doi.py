#!/usr/bin/env python3
"""Collect article.html files under rsc_filtered into a single DOI-named folder."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def unique_target_path(target_dir: Path, doi: str) -> Path:
    """Return a unique output filename for a DOI if duplicates are found."""
    candidate = target_dir / f"{doi}.html"
    if not candidate.exists():
        return candidate

    index = 2
    while True:
        candidate = target_dir / f"{doi}__{index}.html"
        if not candidate.exists():
            return candidate
        index += 1


def collect_article_html(source_root: Path, output_dir: Path) -> tuple[int, int, int]:
    """Copy article files from source folder into output folder.

    Returns:
        tuple: (copied_count, missing_article_count, duplicate_doi_count)
    """
    copied_count = 0
    missing_article_count = 0
    duplicate_doi_count = 0

    output_dir.mkdir(parents=True, exist_ok=True)

    for category_dir in sorted(source_root.iterdir()):
        if not category_dir.is_dir():
            continue

        for doi_dir in sorted(category_dir.iterdir()):
            if not doi_dir.is_dir():
                continue

            article_path = doi_dir / "article.html"
            if not article_path.is_file():
                missing_article_count += 1
                continue

            doi_name = doi_dir.name
            target_path = output_dir / f"{doi_name}.html"
            if target_path.exists():
                duplicate_doi_count += 1
                target_path = unique_target_path(output_dir, doi_name)

            shutil.copy2(article_path, target_path)
            copied_count += 1

    return copied_count, missing_article_count, duplicate_doi_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read category/DOI folders under rsc_filtered and copy each article.html "
            "to a single output folder as doi.html"
        )
    )
    parser.add_argument(
        "--source",
        default="rsc_filtered",
        help="Path to the root folder that contains category folders (default: rsc_filtered)",
    )
    parser.add_argument(
        "--output",
        default="rsc_articles",
        help="Destination folder for DOI HTML files (default: rsc_articles)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    source_root = Path(args.source).resolve()
    output_dir = Path(args.output).resolve()

    if not source_root.exists() or not source_root.is_dir():
        raise SystemExit(f"Source folder not found or not a directory: {source_root}")

    copied, missing, duplicates = collect_article_html(source_root, output_dir)

    print(f"Source: {source_root}")
    print(f"Output: {output_dir}")
    print(f"Copied files: {copied}")
    print(f"DOI folders without article.html: {missing}")
    print(f"Duplicate DOI names handled: {duplicates}")


if __name__ == "__main__":
    main()
