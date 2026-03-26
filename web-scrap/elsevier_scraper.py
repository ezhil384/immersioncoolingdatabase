import os
import re
import time
import elsevier as ev 
from urllib.parse import quote

def _build_downloaded_set(base_data_path):
    """Return a set of XML filenames already present in any subdirectory of base_data_path."""
    downloaded = set()
    if not os.path.exists(base_data_path):
        return downloaded
    for subdir in os.listdir(base_data_path):
        subdir_path = os.path.join(base_data_path, subdir)
        if not os.path.isdir(subdir_path):
            continue
        for fname in os.listdir(subdir_path):
            if fname.endswith(".xml"):
                downloaded.add(fname)
    return downloaded


def mine_immersion_fluids():
    # --- Configuration ---
    KEYWORDS_FILE = "keywords.txt"
    CHECKPOINT_FILE = "completed_queries.txt"
    YEAR_RANGE = [year for year in range(2025, 2018, -1)]
    BASE_DATA_PATH = "../data/elsevier_papers"

    if not os.path.exists(KEYWORDS_FILE):
        print(f"Error: {KEYWORDS_FILE} not found.")
        return

    with open(KEYWORDS_FILE, "r") as f:
        all_queries = [line.strip() for line in f if line.strip()]

    completed_queries = set()
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            completed_queries = {line.strip() for line in f if line.strip()}

    # Build a global set of all XML files already downloaded across all query folders
    already_downloaded = _build_downloaded_set(BASE_DATA_PATH)
    print(f"Found {len(already_downloaded)} already-downloaded XML files across all query folders.")

    for query in all_queries:
        if query in completed_queries:
            continue
        first_part = re.split(r' OR | AND ', query, flags=re.IGNORECASE)[0]
        folder_name = first_part.strip().replace(' ', '_').replace('"', '').replace('\\','').replace('(','').replace(')','')
        # folder_name = "vitrimers"
        query_folder = os.path.join(BASE_DATA_PATH, folder_name)

        if not os.path.exists(query_folder):
            os.makedirs(query_folder)

        print(f"\n--- Querying: {query} ---")
        total_dois = []

        ev.data['qs'] = query
        for year in YEAR_RANGE:
            try:
                ev.data['date'] = year
                # Use the encoded_query in your get_doi function
                dois = ev.get_doi(ev.data, 0, year)
                print(f"  Year {year}: Found {len(dois)} DOIs.")
                total_dois.extend(dois)
                time.sleep(5)
            except Exception as e:
                print(f"  Error searching {year}: {e}")

        if total_dois:
            original_dir = os.getcwd()
            os.chdir(query_folder)
            skipped=0
            try:
                for i, doi in enumerate(total_dois):
                    safe_name = doi.replace("/", "_").replace(":", "_") + ".xml"
                    if safe_name in already_downloaded:
                        skipped += 1
                        continue
                    try:
                        ev.download_doi(doi)
                        already_downloaded.add(safe_name)
                        if (i + 1) % 5 == 0:
                            print(f"    Retrieved {i + 1}/{len(total_dois)}.")
                        time.sleep(1.5)
                    except Exception as e:
                        print(f"    Error with DOI {doi}: {e}")
            finally:
                os.chdir(original_dir)
            print(f"  Completed query: {query} - Total DOIs: {len(total_dois)}, Skipped: {skipped}")
            with open(CHECKPOINT_FILE, "a") as f:
                f.write(query + "\n")

if __name__ == "__main__":
    mine_immersion_fluids()