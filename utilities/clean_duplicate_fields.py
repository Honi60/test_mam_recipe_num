#!/usr/bin/env python3
"""
Utility to clean duplicate fields from data section.
This script removes fields that should only exist in the info section
(creation_date, customer_name) from the data section.
"""

import json
import os
from pathlib import Path
import shutil

# Import paths from config
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.paths import HISTORY_DIR, DB_DIR, RECIEPT_ROOT, get_data_mode, print_config

# Backup directory
BACKUP_DIR = Path(DB_DIR).parent / "History_backup_clean_duplicates"

# Fields to remove from data section (should only be in info section)
FIELDS_TO_REMOVE_FROM_DATA = ['creation_date', 'customer_name']

def clean_data_section(data):
    """
    Remove duplicate fields from data section that should only be in info section.
    """
    if isinstance(data, dict):
        if 'data' in data and isinstance(data['data'], dict):
            # Remove specified fields from data section
            for field in FIELDS_TO_REMOVE_FROM_DATA:
                if field in data['data']:
                    del data['data'][field]
        return data
    return data

def process_json_file(file_path):
    """
    Process a single JSON file to clean duplicate fields.
    """
    try:
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Process the data
        original_data = json.dumps(data, ensure_ascii=False)
        cleaned_data = clean_data_section(data)
        cleaned_json = json.dumps(cleaned_data, indent=2, ensure_ascii=False)
        
        # Check if any changes were made
        if original_data != cleaned_json:
            print(f"  [OK] Cleaned duplicate fields in {file_path.name}")
            return cleaned_json
        else:
            print(f"  [-] No duplicate fields found in {file_path.name}")
            return None
            
    except Exception as e:
        print(f"  [ERROR] Error processing {file_path.name}: {e}")
        return None

def create_backup():
    """
    Create a backup of the History folder.
    """
    if BACKUP_DIR.exists():
        print(f"Backup directory already exists: {BACKUP_DIR}")
        return
    
    print(f"Creating backup: {BACKUP_DIR}")
    shutil.copytree(HISTORY_DIR, BACKUP_DIR)
    print("Backup created successfully.")

def main():
    """
    Main function to process all JSON files in the History folder.
    """
    print("Duplicate Fields Cleaner for History Files")
    print("=" * 50)
    
    # Show current configuration
    try:
        print_config()
    except UnicodeEncodeError:
        print(f"Data Mode: {get_data_mode()}")
        print(f"Receipt Root: {RECIEPT_ROOT}")
        print(f"Database Dir: {DB_DIR}")
    print(f"History Directory: {HISTORY_DIR}")
    print(f"Backup Directory: {BACKUP_DIR}")
    print()
    print(f"Fields to remove from data section: {', '.join(FIELDS_TO_REMOVE_FROM_DATA)}")
    print()
    
    # Check if History directory exists
    if not Path(HISTORY_DIR).exists():
        print(f"Error: History directory not found: {HISTORY_DIR}")
        return
    
    # Create backup
    create_backup()
    
    # Get all JSON files
    json_files = list(Path(HISTORY_DIR).glob("*.json"))
    total_files = len(json_files)
    
    if total_files == 0:
        print("No JSON files found in History directory.")
        return
    
    print(f"Found {total_files} JSON files to process.")
    print()
    
    # Process each file
    cleaned_count = 0
    error_count = 0
    
    for i, file_path in enumerate(json_files, 1):
        print(f"[{i}/{total_files}] Processing {file_path.name}...")
        
        cleaned_json = process_json_file(file_path)
        
        if cleaned_json:
            # Write the cleaned file
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_json)
                cleaned_count += 1
            except Exception as e:
                print(f"  [ERROR] Error writing cleaned file: {e}")
                error_count += 1
        elif cleaned_json is None:
            # No changes needed (not an error)
            pass
        else:
            error_count += 1
    
    print()
    print("Processing complete!")
    print(f"Total files: {total_files}")
    print(f"Files cleaned: {cleaned_count}")
    print(f"Errors: {error_count}")
    print(f"Backup location: {BACKUP_DIR}")
    
    if cleaned_count > 0:
        print()
        print("[OK] Duplicate fields have been cleaned from the History files!")
        print("Removed creation_date and customer_name from data sections.")
    
    if error_count > 0:
        print()
        print("[WARNING] Some files had errors. Check the output above for details.")

if __name__ == "__main__":
    main()
