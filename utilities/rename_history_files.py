#!/usr/bin/env python3
"""
Utility to rename History JSON files to consistent format.
Renames files to: receiptNum_customer_name_Date.json
"""

import json
import os
import re
from pathlib import Path
import shutil

# Import paths from config
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.paths import HISTORY_DIR, DB_DIR, RECIEPT_ROOT, get_data_mode, print_config

# Backup directory
BACKUP_DIR = Path(DB_DIR).parent / "History_backup_rename"

def sanitize_filename(name):
    """
    Sanitize a string to be safe for filenames.
    Remove or replace characters that are problematic in filenames.
    """
    if not isinstance(name, str):
        name = str(name)
    
    # Replace problematic characters
    name = name.replace('/', '_')
    name = name.replace('\\', '_')
    name = name.replace(':', '_')
    name = name.replace('*', '_')
    name = name.replace('?', '_')
    name = name.replace('"', '_')
    name = name.replace('<', '_')
    name = name.replace('>', '_')
    name = name.replace('|', '_')
    
    # Remove leading/trailing spaces and dots
    name = name.strip().strip('.')
    
    # If empty, return placeholder
    if not name:
        return 'unknown'
    
    return name

def extract_fields_from_json(file_path):
    """
    Extract receiptNum, customer_name, and Date from JSON file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        receipt_num = ''
        customer_name = ''
        date = ''
        
        # Try to get fields from data section first
        if 'data' in data and isinstance(data['data'], dict):
            data_section = data['data']
            receipt_num = data_section.get('recipeNum', '')
            customer_name = data_section.get('customer_name', '')
            date = data_section.get('Date', '')
            
            # If customer_name not in data, check info section
            if not customer_name and 'info' in data:
                info_section = data['info']
                customer_name = info_section.get('customer_name', '')
        else:
            # Try flat structure
            receipt_num = data.get('recipeNum', '')
            customer_name = data.get('customer_name', '')
            date = data.get('Date', '')
            
            # If customer_name not in flat structure, check info section
            if not customer_name and 'info' in data:
                info_section = data['info']
                customer_name = info_section.get('customer_name', '')
        
        return receipt_num, customer_name, date
        
    except Exception as e:
        print(f"  [ERROR] Error reading {file_path.name}: {e}")
        return None, None, None

def generate_new_filename(receipt_num, customer_name, date):
    """
    Generate new filename in format: receiptNum_customer_name_Date.json
    """
    # Sanitize each component
    safe_receipt_num = sanitize_filename(receipt_num)
    safe_customer_name = sanitize_filename(customer_name)
    safe_date = sanitize_filename(date)
    
    # If any field is missing, use placeholder
    if not safe_receipt_num:
        safe_receipt_num = 'unknown'
    if not safe_customer_name:
        safe_customer_name = 'unknown'
    if not safe_date:
        safe_date = 'unknown'
    
    # Generate filename
    new_filename = f"{safe_receipt_num}_{safe_customer_name}_{safe_date}.json"
    
    return new_filename

def process_file(file_path):
    """
    Process a single file to rename it.
    """
    # Extract fields
    receipt_num, customer_name, date = extract_fields_from_json(file_path)
    
    if receipt_num is None:
        return None, None
    
    # Generate new filename
    new_filename = generate_new_filename(receipt_num, customer_name, date)
    new_file_path = file_path.parent / new_filename
    
    # Check if new filename is same as old
    if file_path.name == new_filename:
        return None, None
    
    # Check if target file already exists
    if new_file_path.exists():
        print(f"  [SKIP] Target filename already exists: {new_filename}")
        return None, None
    
    return file_path, new_file_path

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
    Main function to rename all JSON files in the History folder.
    """
    print("History File Renamer")
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
    print("Target format: receiptNum_customer_name_Date.json")
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
    
    # Collect rename operations first
    rename_operations = []
    skipped_count = 0
    error_count = 0
    
    for i, file_path in enumerate(json_files, 1):
        print(f"[{i}/{total_files}] Processing {file_path.name}...")
        
        old_path, new_path = process_file(file_path)
        
        if old_path and new_path:
            rename_operations.append((old_path, new_path))
            print(f"  [OK] Will rename to: {new_path.name}")
        elif old_path is None:
            error_count += 1
        else:
            skipped_count += 1
    
    print()
    print(f"Rename operations collected: {len(rename_operations)}")
    print(f"Skipped: {skipped_count}")
    print(f"Errors: {error_count}")
    print()
    
    if rename_operations:
        print("Executing rename operations...")
        success_count = 0
        
        for old_path, new_path in rename_operations:
            try:
                old_path.rename(new_path)
                success_count += 1
                print(f"  [OK] Renamed: {old_path.name} -> {new_path.name}")
            except Exception as e:
                print(f"  [ERROR] Failed to rename {old_path.name}: {e}")
                error_count += 1
        
        print()
        print(f"Successfully renamed: {success_count}")
        print(f"Failed: {error_count}")
    else:
        print("No files to rename.")
    
    print()
    print("Processing complete!")
    print(f"Backup location: {BACKUP_DIR}")

if __name__ == "__main__":
    main()
