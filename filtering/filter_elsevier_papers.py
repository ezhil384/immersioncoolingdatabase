import os
import shutil

def filter_and_flatten_xml(base_source_dir, base_target_dir, keywords):
    """
    Traverses all sub-directories, filters XMLs by keywords, 
    and moves them all into a single flat directory.
    """
    if not os.path.exists(base_target_dir):
        os.makedirs(base_target_dir)

    keywords = [k.lower() for k in keywords]
    total_scanned = 0
    total_relevant = 0

    print(f"Flattening and filtering files from: {base_source_dir}")

    for root, dirs, files in os.walk(base_source_dir):
        xml_files = [f for f in files if f.endswith('.html') or f.endswith('.xml')]
        
        for filename in xml_files:
            target_path = os.path.join(base_target_dir, filename)
            if os.path.exists(target_path):
                continue
            total_scanned += 1
            source_path = os.path.join(root, filename)
            
            try:
                with open(source_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    
                    properties = [k.lower() for k in keywords[:4]]   # First 4: thermal conductivity, viscosity, dielectric constant, dielectric strength
                    applications = [k.lower() for k in keywords[4:]] # Last 3: immersion cooling, cooling performance, fluid


                    has_property = any(p in content for p in properties)
                    has_application = any(a in content for a in applications)

                    if has_property and has_application:
                        shutil.copy(source_path, target_path)
                        total_relevant += 1
            except Exception as e:
                print(f"Error reading {source_path}: {e}")

    print(f"\nProcessing Complete.")
    print(f"Total files scanned across all subdirectories: {total_scanned}")
    print(f"Total unique relevant files moved to '{base_target_dir}': {total_relevant}")


# Usage
MY_KEYWORDS = ["thermal conductivity", "viscosity", "dielectric constant", "dielectric strength", "immersion cooling","cooling performance","server cooling","Direct Liquid Cooling", "Transformer Oils","Submerged Cooling","data center","organic fluid","dielectric fluid","coolant","heat transfer fluid","electrical insulation","dielectric breakdown","dielectric dissipation factor"]
filter_and_flatten_xml("../data/elsevier_papers", "../data/filtered_elsevier", MY_KEYWORDS)
