#!/usr/bin/env python3
"""
Utility to fix Hebrew text reversal in all JSON files in the History folder.
This script will:
1. Process all JSON files in the History folder
2. Detect Hebrew strings in all fields
3. Reverse Hebrew text to correct display order
4. Fix year patterns (62/52/6202/5202) within Hebrew strings
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
BACKUP_DIR = Path(DB_DIR).parent / "History_backup"

# Hebrew Unicode range (Basic Hebrew and Hebrew extended)
HEBREW_PATTERN = re.compile(r'[\u0590-\u05FF\uFB1D-\uFB4F]+')

# Year patterns to fix (62/52/6202/5202 for years 2026/2025)
YEAR_PATTERNS = [
    r'62',   # 2026
    r'52',   # 2025
    r'6202', # 2026
    r'5202', # 2025
]

def is_hebrew_string(text):
    """Check if a string contains Hebrew characters."""
    if not isinstance(text, str):
        return False
    return bool(HEBREW_PATTERN.search(text))

def fix_hebrew_string(text):
    """
    Fix Hebrew string by reversing it and fixing year patterns.
    """
    if not isinstance(text, str):
        return text
    
    # Check if the string contains Hebrew
    if not is_hebrew_string(text):
        return text
    
    # Reverse the entire string first
    fixed_text = text[::-1]
    
    # Fix year patterns that got reversed - only within Hebrew context
    # 62 -> 26 (should be 2026)
    # 52 -> 25 (should be 2025)
    # 6202 -> 2026
    # 5202 -> 2025
    year_fixes = [
        ('6202', '2026'),  # Fix full year first
        ('5202', '2025'),
        ('62', '26'),      # Then fix partial years
        ('52', '25'),
    ]
    
    # Apply year fixes only if the string contains Hebrew
    for wrong_year, correct_year in year_fixes:
        if wrong_year in fixed_text:
            fixed_text = fixed_text.replace(wrong_year, correct_year)
    
    return fixed_text

def process_value(value):
    """
    Process a value recursively to fix Hebrew strings.
    """
    if isinstance(value, str):
        return fix_hebrew_string(value)
    elif isinstance(value, dict):
        return {k: process_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [process_value(item) for item in value]
    else:
        return value

def process_json_file(file_path):
    """
    Process a single JSON file to fix Hebrew text.
    """
    try:
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Process the data
        original_data = json.dumps(data, ensure_ascii=False)
        fixed_data = process_value(data)
        fixed_json = json.dumps(fixed_data, indent=2, ensure_ascii=False)
        
        # Check if any changes were made
        if original_data != fixed_json:
            print(f"  [OK] Fixed Hebrew text in {file_path.name}")
            return fixed_json
        else:
            print(f"  [-] No Hebrew text fixes needed in {file_path.name}")
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
    print("Hebrew Text Fixer for History Files")
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
        print("[OK] Hebrew text has been fixed in the History files!")
        print("You can now use the history editor with properly displayed Hebrew text.")
    
    if error_count > 0:
        print()
        print("[WARNING] Some files had errors. Check the output above for details.")

if __name__ == "__main__":
    main()
