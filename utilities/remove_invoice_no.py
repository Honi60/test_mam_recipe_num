#!/usr/bin/env python3
"""
Utility to remove invoice_no field from data section.
This field is old and has been replaced by receipt number.
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
BACKUP_DIR = Path(DB_DIR).parent / "History_backup_remove_invoice_no"

# Field to remove
FIELD_TO_REMOVE = 'invoice_no'

def remove_invoice_no_field(data):
    """
    Remove invoice_no field from data section.
    Returns True if changes were made, False otherwise.
    """
    if isinstance(data, dict):
        if 'data' in data and isinstance(data['data'], dict):
            data_section = data['data']
            if FIELD_TO_REMOVE in data_section:
                del data_section[FIELD_TO_REMOVE]
                return True
        
        # Also check flat structure
        if FIELD_TO_REMOVE in data:
            del data[FIELD_TO_REMOVE]
            return True
        
        return False
    return False

def process_json_file(file_path):
    """
    Process a single JSON file to remove invoice_no field.
    """
    try:
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Process the data
        original_data = json.dumps(data, ensure_ascii=False)
        was_changed = remove_invoice_no_field(data)
        fixed_json = json.dumps(data, indent=2, ensure_ascii=False)
        
        # Check if any changes were made
        if was_changed:
            print(f"  [OK] Removed invoice_no from {file_path.name}")
            return fixed_json
        else:
            print(f"  [-] No invoice_no found in {file_path.name}")
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
    print("Invoice No Field Remover for History Files")
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
    print(f"Field to remove: {FIELD_TO_REMOVE}")
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
        print("[OK] invoice_no field has been removed from the History files!")
    
    if error_count > 0:
        print()
        print("[WARNING] Some files had errors. Check the output above for details.")

if __name__ == "__main__":
    main()
