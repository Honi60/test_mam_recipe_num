#!/usr/bin/env python3
"""
Utility to fix CheckNumber field for bank transfer receipts.
If bank_transfer_reference has a value, clear CheckNumber as bank transfers don't involve checks.
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
BACKUP_DIR = Path(DB_DIR).parent / "History_backup_fix_checknumber"

def fix_checknumber_for_bank_transfer(data):
    """
    Clear CheckNumber if bank_transfer_reference has a value.
    Returns True if changes were made, False otherwise.
    """
    if isinstance(data, dict):
        if 'data' in data and isinstance(data['data'], dict):
            data_section = data['data']
            
            # Check if bank_transfer_reference has a value
            bank_transfer_ref = data_section.get('bank_transfer_referance', '')
            
            # Only clear CheckNumber if bank_transfer_referance is not empty
            if bank_transfer_ref is not None and str(bank_transfer_ref).strip() != '':
                # Clear CheckNumber as bank transfers don't involve checks
                if 'CheckNumber' in data_section:
                    if data_section['CheckNumber'] != '':
                        data_section['CheckNumber'] = ''
                        return True
        
        return False
    return False

def process_json_file(file_path):
    """
    Process a single JSON file to fix CheckNumber for bank transfers.
    """
    try:
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Process the data
        original_data = json.dumps(data, ensure_ascii=False)
        was_changed = fix_checknumber_for_bank_transfer(data)
        fixed_json = json.dumps(data, indent=2, ensure_ascii=False)
        
        # Check if any changes were made
        if was_changed:
            print(f"  [OK] Fixed CheckNumber for bank transfer in {file_path.name}")
            return fixed_json
        else:
            print(f"  [-] No CheckNumber fix needed in {file_path.name}")
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
    print("CheckNumber Fixer for Bank Transfer Receipts")
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
    print("Logic: Clear CheckNumber when bank_transfer_referance has value")
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
    fixed_count = 0
    error_count = 0
    
    for i, file_path in enumerate(json_files, 1):
        print(f"[{i}/{total_files}] Processing {file_path.name}...")
        
        fixed_json = process_json_file(file_path)
        
        if fixed_json:
            # Write the fixed file
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_json)
                fixed_count += 1
            except Exception as e:
                print(f"  [ERROR] Error writing fixed file: {e}")
                error_count += 1
        elif fixed_json is None:
            # No changes needed (not an error)
            pass
        else:
            error_count += 1
    
    print()
    print("Processing complete!")
    print(f"Total files: {total_files}")
    print(f"Files fixed: {fixed_count}")
    print(f"Errors: {error_count}")
    print(f"Backup location: {BACKUP_DIR}")
    
    if fixed_count > 0:
        print()
        print("[OK] CheckNumber has been fixed for bank transfer receipts!")
    
    if error_count > 0:
        print()
        print("[WARNING] Some files had errors. Check the output above for details.")

if __name__ == "__main__":
    main()
