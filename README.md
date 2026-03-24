# immersioncoolingdatabase

[![License](http://img.shields.io/:license-mit-blue.svg?style=flat-square)](https://github.com/shuhuang/batterygui/blob/master/LICENSE)

Tools for auto-generating a database of thermophysical properties of immersion cooling fluids. The pipeline scrapes scientific literature from Elsevier, RSC, and Springer, then applies a customised ChemDataExtractor (v1.5) to extract properties including **dielectric constant**, **thermal conductivity**, **dynamic viscosity**, and **flash point** for candidate coolant compounds.

---

## Installation

Install the public ChemDataExtractor base (v1.3):
```
conda install -c chemdataextractor chemdataextractor
```

Download the required data files (ML models, dictionaries, etc.):
```
cde data download
```

Install the dependency packages for the bespoke immersion-cooling version (chemdataextractor_immersion v1.5):
```
pip install -r requirements.txt
```

---

## Web Scraping

All scrapers live in `web-scrap/`. They retrieve full-text articles from each publisher and save them locally for downstream extraction. Search queries are driven by `keywords.txt` (one query per line; lines starting with `#` are ignored).

**`keywords.txt` format example:**
```
("dielectric fluid" OR "heat transfer fluid") AND ("dielectric constant" OR "dielectric strength")
("biobased hydrocarbons" OR "natural esters") AND ("thermal conductivity" OR viscosity OR "flash point")
```

### Elsevier

Uses the Elsevier ScienceDirect API. Requires an API key set in `web-scrap/elsevier.py`.

Run from inside `web-scrap/`:
```bash
python elsevier_scraper.py
```

- Reads queries from `keywords.txt` (must be present in `web-scrap/`)
- Searches years 2019–2025 for each query
- Downloads full-text XML files to `../data/elsevier_papers/<query_folder>/`
- Completed queries are checkpointed in `completed_queries.txt` so interrupted runs can resume

### RSC

Uses Selenium with a headless Chrome browser to search and download from the Royal Society of Chemistry. Requires `chromedriver` (managed automatically via `webdriver-manager`).

Run from inside `web-scrap/` or the repository root:
```bash
# Use queries from keywords.txt (default: ../keywords.txt)
python rsc_scraper.py

# Pass queries directly on the command line
python rsc_scraper.py "immersion cooling" "dielectric fluid battery"

# Set page range and output directory explicitly
python rsc_scraper.py --page-start 1 --page-end 10 --output-dir ../data/rsc_papers

# All options
python rsc_scraper.py --help
```

| Option | Short | Default | Description |
|---|---|---|---|
| `--keywords-file` | `-k` | `../keywords.txt` | Path to the keywords file |
| `--output-dir` | `-o` | `../data` | Root directory for saved HTML and metadata |
| `--page-start` | `-s` | `1` | First search-results page to fetch |
| `--page-end` | `-e` | `10` | Last search-results page to fetch (inclusive) |
| `--verbose` | `-v` | — | Enable DEBUG-level logging |

Each article is saved as `<output_dir>/<query_folder>/<safe_doi>/article.html` alongside a `metadata.json` file. Already-downloaded articles are skipped automatically.

#### Flattening RSC output with `article_doi.py`

After the RSC scrape, the articles are nested inside per-query and per-DOI subdirectories. `article_doi.py` flattens this into a single folder of DOI-named HTML files, ready for bulk extraction.

```bash
python article_doi.py --source rsc_filtered --output rsc_articles
```

| Option | Default | Description |
|---|---|---|
| `--source` | `rsc_filtered` | Root folder containing category/DOI subdirectories |
| `--output` | `rsc_articles` | Destination folder for the flat DOI HTML files |

Duplicate DOI filenames (same article found under multiple queries) are disambiguated automatically with a numeric suffix.

### Springer

Uses the Springer Nature API. Requires an API key and the target query/year configured directly in `web-scrap/springer_scraper.py`:

```python
QUERY = "immersion cooling"
YEARS = [2023, 2024, 2025]
API_KEY = "your_springer_api_key"
```

Then run from inside `web-scrap/`:
```bash
python springer_scraper.py
```

Downloads article XML files to `data/springer_papers/`.

---

## Property Extraction

Once articles have been downloaded, run `extract.py` to extract thermophysical property records using ChemDataExtractor. Provide the folder of HTML/XML files, an output directory, a slice range over the paper list, and a filename stem for the output JSON lines file.

```bash
python extract.py --input_dir <paper_folder> --output_dir <output_folder> --start 0 --end 100 --save_name raw_data
```

| Argument | Description |
|---|---|
| `--input_dir` | Folder containing `.html` or `.xml` article files (required) |
| `--output_dir` | Folder where the output JSON lines file will be saved (required) |
| `--start` | Start index into the sorted paper list (default: 0) |
| `--end` | End index into the sorted paper list (default: 1) |
| `--save_name` | Stem of the output file, saved as `<save_name>.json` (default: `raw_data`) |

For example, to process all RSC articles collected above:
```bash
python extract.py --input_dir rsc_articles/ --output_dir outputs/ --start 0 --end 500 --save_name raw_data_rsc
```

The output is a JSON lines file (one record per line) where each line contains a serialised property record with compound name, value, units, specifier, and article metadata (DOI, title, journal, date).

---

## Data Cleaning

`clean_immersion.py` reads the JSON lines output from `extract.py`, converts it to a flat CSV, removes duplicates, and filters out physically implausible values.

Edit the input and output paths at the bottom of the script, then run:
```bash
python clean_immersion.py
```

The script:
- Converts nested CDE records into a flat table with columns: `Property`, `Name`, `Specifier`, `Raw_value`, `Raw_unit`, `Value`, `Conditions`, `Unit`, `DOI`, `Title`, `Journal`, `Date`, `Warning`
- Removes duplicate rows on `(Property, DOI, Name, Value)`
- Filters `DielectricConstant` records to the physically valid range (1.0–200.0)
- Saves the result as a CSV file

---

## Acknowledgements

This project was supported by the Department of Mechanical Engineering at the University of Michigan. The author also gratefully acknowledges the technical assistance and guidance provided by the publishers throughout the development of this research. Furthermore, the use of research resources was made possible through the support of the University of Michigan's institutional facilities.

## Citation

The ChemDataExtractor framework underlying the property extraction is described in:
```
@article{huang2020database,
  title={A database of battery materials auto-generated using ChemDataExtractor},
  author={Huang, Shu and Cole, Jacqueline M},
  journal={Scientific Data},
  volume={7},
  number={1},
  pages={1--13},
  year={2020},
  publisher={Nature Publishing Group}
}
```
[![DOI](https://zenodo.org/badge/DOI/10.1038/s41597-020-00602-2.svg)](https://doi.org/10.1038/s41597-020-00602-2)
