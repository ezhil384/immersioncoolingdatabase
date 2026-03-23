import json
import pandas as pd
import re


MIN_DIELECTRIC_CONSTANT = 1.0
MAX_DIELECTRIC_CONSTANT = 200.0

def convert_immersion_data(raw_record):
    """
    Transforms CDE output where Property names are top-level keys.
    """
    # Identify the property key (e.g., 'ThermalConductivity' or 'Viscosity')
    # Skipping the 'metadata' and 'warning' keys
    property_key = [k for k in raw_record.keys() if k not in ['metadata', 'warning']][0]
    prop_data = raw_record[property_key]
    
    new_dic = {
        'Property': property_key,  # Uses the key name as the 'Property' column value
        'Name': prop_data['compound']['Compound']['names'],
        'Specifier': prop_data.get('specifier', 'None'),
        'Raw_value': prop_data.get('raw_value', 'None'),
        'Raw_unit': prop_data.get('raw_units', 'None'),
        'Value': prop_data.get('value', 'None'),
        'Conditions': prop_data.get('measurement_conditions', 'None'),
        'Unit': prop_data.get('units', 'None'),
        'DOI': raw_record['metadata'].get('doi', 'None'),
        'Title': raw_record['metadata'].get('title', 'None'),
        'Journal': raw_record['metadata'].get('journal', 'None'),
        'Date': raw_record['metadata'].get('date', 'None'),
        'Warning': 'R' if 'warning' in raw_record else 'None'
    }
    return new_dic


def extract_numeric_value(value):
    """Extract the first numeric value from mixed value formats."""
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, list):
        for item in value:
            numeric = extract_numeric_value(item)
            if numeric is not None:
                return numeric
        return None

    if isinstance(value, str):
        match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", value)
        return float(match.group(0)) if match else None

    return None

def clean_and_save(input_jsonl, output_csv):
    raw_data = []
    with open(input_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            raw_data.append(json.loads(line))

    # Convert to flat structure
    cleaned_list = [convert_immersion_data(r) for r in raw_data]
    df = pd.DataFrame(cleaned_list)

    # Flatten the 'Name' list to a single string for CSV/Table readability
    df['Name'] = df['Name'].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x)
    if df['Value'].dtype == 'O':  # If 'Value' is object type, try to convert to numeric
        df['Value'] = df['Value'].apply(extract_numeric_value)
    # Remove duplicates based on core data
    df = df.drop_duplicates(subset=['Property', 'DOI', 'Name','Value'], keep='last')

    # Remove dielectric constant values outside a physically reasonable range.
    dielectric_mask = df['Property'] == 'DielectricConstant'
    dielectric_numeric = df.loc[dielectric_mask, 'Value'].apply(extract_numeric_value)
    valid_dielectric = dielectric_numeric.notna() & dielectric_numeric.between(
        MIN_DIELECTRIC_CONSTANT,
        MAX_DIELECTRIC_CONSTANT,
    )
    valid_dielectric = valid_dielectric & (dielectric_numeric != 10.1039)
    invalid_dielectric_count = int((~valid_dielectric).sum())

    df = pd.concat([
        df.loc[~dielectric_mask],
        df.loc[dielectric_mask].loc[valid_dielectric.values],
    ], ignore_index=True)
    
    df.to_csv(output_csv, index=False)
    print(f"Cleaned data saved to {output_csv}")
    print(f"Removed invalid dielectric constant rows: {invalid_dielectric_count}")

if __name__ == "__main__":
    clean_and_save('outputs/immersion_rsc/raw_data_rsc_full_v1.json', 'outputs/immersion_rsc/immersion_rsc_full_v1.csv')