#!/usr/bin/env python3
"""
Utility to fix SaveFolder fields with mixed English/Hebrew paths.
This script specifically handles the SaveFolder field where paths contain
both English (file system paths) and Hebrew (folder names) that need to be reversed.
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

# Backup directory for SaveFolder fixes
BACKUP_DIR = Path(DB_DIR).parent / "History_backup_SaveFolder"

# Hebrew Unicode range
HEBREW_PATTERN = re.compile(r'[\u0590-\u05FF\uFB1D-\uFB4F]+')

def is_hebrew_string(text):
    """Check if a string contains Hebrew characters."""
    if not isinstance(text, str):
        return False
    return bool(HEBREW_PATTERN.search(text))

def split_path_components(path):
    """
    Split path into components, identifying which are Hebrew and which are English.
    Returns a list of tuples: (component, is_hebrew)
    """
    if not isinstance(path, str):
        return []
    
    # Split by backslashes (Windows paths)
    components = path.split('\\')
    
    result = []
    for component in components:
        is_hebrew = is_hebrew_string(component)
        result.append((component, is_hebrew))
    
    return result

def fix_savefolder_path(path):
    """
    Fix SaveFolder path by reversing only Hebrew components.
    English path components remain unchanged.
    """
    if not isinstance(path, str):
        return path
    
    # Check if path contains Hebrew
    if not is_hebrew_string(path):
        return path
    
    # The entire path is currently reversed, so we need to:
    # 1. Reverse the entire path first
    # 2. Split it into components
    # 3. Reverse Hebrew components back to correct order
    # 4. Keep English components as they are (they're now correct after step 1)
    
    # Step 1: Reverse entire path to get correct component order
    reversed_path = path[::-1]
    
    # Step 2: Split into components
    components = reversed_path.split('\\')
    
    # Step 3 & 4: Process each component
    fixed_components = []
    for component in components:
        if is_hebrew_string(component):
            # Hebrew component is now reversed, so reverse it back
            fixed_component = component[::-1]
            # Fix year patterns in Hebrew component
            year_fixes = [
                ('6202', '2026'),
                ('5202', '2025'),
                ('62', '26'),
                ('52', '25'),
            ]
            for wrong_year, correct_year in year_fixes:
                if wrong_year in fixed_component:
                    fixed_component = fixed_component.replace(wrong_year, correct_year)
            fixed_components.append(fixed_component)
        else:
            # English component is now correct after the initial reversal
            fixed_components.append(component)
    
    # Reconstruct the path
    fixed_path = '\\'.join(fixed_components)
    
    return fixed_path

def process_value(value):
    """
    Process a value recursively to fix SaveFolder paths.
    """
    if isinstance(value, str):
        # Only process SaveFolder field
        # We'll handle this at the field level
        return value
    elif isinstance(value, dict):
        return {k: process_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [process_value(item) for item in value]
    else:
        return value

def fix_savefolder_in_data(data):
    """
    Fix SaveFolder field in data structure.
    """
    if isinstance(data, dict):
        fixed_data = {}
        for key, value in data.items():
            if key == 'SaveFolder' and isinstance(value, str):
                fixed_data[key] = fix_savefolder_path(value)
            else:
                fixed_data[key] = fix_savefolder_in_data(value)
        return fixed_data
    elif isinstance(data, list):
        return [fix_savefolder_in_data(item) for item in data]
    else:
        return data

def process_json_file(file_path):
    """
    Process a single JSON file to fix SaveFolder paths.
    """
    try:
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Process the data specifically for SaveFolder
        original_data = json.dumps(data, ensure_ascii=False)
        fixed_data = fix_savefolder_in_data(data)
        fixed_json = json.dumps(fixed_data, indent=2, ensure_ascii=False)
        
        # Check if any changes were made
        if original_data != fixed_json:
            print(f"  [OK] Fixed SaveFolder path in {file_path.name}")
            return fixed_json
        else:
            print(f"  [-] No SaveFolder fixes needed in {file_path.name}")
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
    print("SaveFolder Path Fixer for History Files")
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
        print("[OK] SaveFolder paths have been fixed in the History files!")
        print("English path components preserved, Hebrew components reversed.")
    
    if error_count > 0:
        print()
        print("[WARNING] Some files had errors. Check the output above for details.")

if __name__ == "__main__":
    main()
