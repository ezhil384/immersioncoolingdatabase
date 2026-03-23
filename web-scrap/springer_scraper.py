import os
import time
import springer as sp  # Importing your Springer class script

def mine_springer_immersion_fluids():
    # --- Configuration ---
    QUERY = "vitrimers"
    YEARS = [2025]
    API_KEY = "ba48ba6c2c63d3c2f06bbbe8992942ec"
    DATA_TARGET = "data/springer_papers"
    MAX_PER_PAGE = 50  # Springer allows up to 100, but 50 is safer for stability

    if not os.path.exists(DATA_TARGET):
        os.makedirs(DATA_TARGET)

    print(f"Starting Springer search for '{QUERY}'...")

    for year in YEARS:
        print(f"--- Processing Year: {year} ---")
        
        # 1. Initialize the Scraper Class
        scraper = sp.SpringerScraper(
            query_text=QUERY,
            year=year,
            apikey=API_KEY,
            max_return=MAX_PER_PAGE
        )

        try:
            # 2. Find DOIs
            dois = scraper.FindDois()
            print(f"Found {len(dois)} DOIs.")

            # 3. Get the specific XML/PAM URLS for these DOIs
            xml_urls = scraper.FindingXml(dois)

            # 4. Download Phase
            for i, url in enumerate(xml_urls):
                # We use the DOI to create a unique filename
                # DOI is embedded in the record, but for naming we'll sanitize the URL index
                safe_name = dois[i].replace("/", "_").replace(":", "_")
                file_path = os.path.join(DATA_TARGET, f"springer_{safe_name}.xml")

                if os.path.exists(file_path):
                    continue

                try:
                    # Request and write the content
                    # Note: Using your download_doi logic but with a targeted path
                    import urllib.request as request
                    web_content = request.urlopen(url).read()
                    
                    with open(file_path, 'wb') as f:
                        f.write(web_content)
                    
                    if (i + 1) % 10 == 0:
                        print(f"Downloaded {i+1}/{len(xml_urls)} for {year}...")
                    
                    # Respectful crawling delay
                    time.sleep(1)

                except Exception as e:
                    print(f"Failed to download {dois[i]}: {e}")

        except Exception as e:
            print(f"Error processing year {year}: {e}")

    print(f"Mining complete. Results stored in {DATA_TARGET}")

if __name__ == "__main__":
    mine_springer_immersion_fluids()