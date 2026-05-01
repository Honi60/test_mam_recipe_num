#!/usr/bin/env python3
"""Simple script to count PDFs in customer receipt folders."""

import json
import os

# Production paths (from paths.py else branch, ignoring USE_SIMULATION)
PRODUCTION_ROOT = r"E:\My Drive\Rentals"
CUSTOMER_FILE = r"E:\My Drive\Rentals\RentalsDB\customers_data.json"

def load_customers():
    """Load customers from production file."""
    if not os.path.exists(CUSTOMER_FILE):
        print(f"Customer file not found: {CUSTOMER_FILE}")
        return {}

    with open(CUSTOMER_FILE, 'r', encoding='utf-8') as f:
        text = f.read()

    try:
        return json.loads(text)
    except:
        return eval(text, {})  # fallback

def extract_save_folders(customers):
    """Extract unique save folders from customer data."""
    folders = set()
    simulation_root = r"E:\simulation_rentals"
    production_root = r"E:\My Drive\Rentals"
    
    print(f"Replacing simulation root '{simulation_root}' with production root '{production_root}'")
    
    for customer_name, data in customers.items():
        if isinstance(data, dict):
            for key, value in data.items():
                key_lower = str(key).lower()
                if any(word in key_lower for word in ['save', 'path', 'folder', 'output']):
                    if isinstance(value, str) and value.strip():
                        original_path = value
                        # Replace simulation root with production root if present
                        folder_path = value.replace(simulation_root, production_root)
                        # If it's still a relative path, prepend production root
                        if not os.path.isabs(folder_path):
                            folder_path = os.path.join(production_root, folder_path)
                        
                        if original_path != folder_path:
                            print(f"  {customer_name}: '{original_path}' -> '{folder_path}'")
                        folders.add(folder_path)
    return folders

def count_pdfs_in_folder(folder):
    """Count PDF files in a folder."""
    if not os.path.exists(folder):
        return 0
    try:
        return len([f for f in os.listdir(folder) if f.lower().endswith('.pdf')])
    except:
        return 0

def main():
    print("Loading production customer data...")
    print(f"Looking for file: {CUSTOMER_FILE}")
    customers = load_customers()
    print(f"Found {len(customers)} customers")

    if customers:
        print("\nSample customer data:")
        for i, (name, data) in enumerate(list(customers.items())[:2]):
            print(f"  {name}: {data}")

    print("\nExtracting save folders...")
    folders = extract_save_folders(customers)
    print(f"Found {len(folders)} unique folders from customer data")

    # If no folders found in customer data, try common receipt locations
    if not folders:
        print("No save folders in customer data, checking common locations...")
        common_locations = [
            r"E:\My Drive\Rentals\Receipts",
            r"E:\My Drive\Rentals\PDFs",
            r"E:\My Drive\Rentals\receipts",
            r"E:\My Drive\Rentals\pdfs"
        ]
        for location in common_locations:
            if os.path.exists(location):
                folders.add(location)
                print(f"  Found common location: {location}")

    if not folders:
        print("No folders found at all!")
        return

    print(f"\nTotal folders to check: {len(folders)}")
    print("Folders:")
    for folder in sorted(folders):
        print(f"  {folder}")

    print("\nCounting PDFs in each folder:")
    print("-" * 60)

    total_pdfs = 0
    for folder in sorted(folders):
        pdf_count = count_pdfs_in_folder(folder)
        total_pdfs += pdf_count
        print("20")

    print("-" * 60)
    print(f"Total PDFs across all folders: {total_pdfs}")

if __name__ == '__main__':
    main()