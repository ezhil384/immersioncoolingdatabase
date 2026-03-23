#!/usr/bin/env python3
"""Merge all CSV files in a folder into one CSV and remove duplicate rows."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def collect_csv_files(input_dir: Path, recursive: bool) -> list[Path]:
    pattern = "**/*.csv" if recursive else "*.csv"
    return sorted(p for p in input_dir.glob(pattern) if p.is_file())


def merge_csvs(input_dir: Path, output_csv: Path, recursive: bool) -> None:
    csv_files = collect_csv_files(input_dir, recursive)

    # Avoid reading the output file if it is inside the same folder.
    csv_files = [p for p in csv_files if p.resolve() != output_csv.resolve()]

    if not csv_files:
        raise SystemExit(f"No CSV files found in: {input_dir}")

    frames = []
    for csv_file in csv_files:
        frames.append(pd.read_csv(csv_file))

    merged_df = pd.concat(frames, ignore_index=True)
    deduped_df = merged_df.drop_duplicates(subset=['Property', 'DOI', 'Name'], keep='last')
    print(deduped_df['Property'].value_counts())

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    deduped_df.to_csv(output_csv, index=False)

    print(f"CSV files read: {len(csv_files)}")
    print(f"Merged rows: {len(merged_df)}")
    print(f"Rows after deduplication: {len(deduped_df)}")
    print(f"Saved merged CSV to: {output_csv}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge all CSV files in a folder into one CSV and remove duplicates."
    )
    parser.add_argument(
        "input_dir",
        help="Folder that contains CSV files",
        default="outputs/immersion_rsc",
    )
    parser.add_argument(
        "output_csv",
        help="Path of the merged output CSV",
        default="outputs/immersion_rsc/merged_rsc.csv",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search subfolders recursively for CSV files",
    )
    return parser.parse_args()


def main() -> None:
    # args = parse_args()
    input_dir = Path("outputs/immersion_rsc").resolve()
    output_csv = Path("outputs/immersion_rsc/merged_rsc.csv").resolve()

    if not input_dir.is_dir():
        raise SystemExit(f"Input directory not found: {input_dir}")

    merge_csvs(input_dir, output_csv, recursive=False)


if __name__ == "__main__":
    main()
