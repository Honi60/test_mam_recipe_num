#!/usr/bin/env python3
"""
Test version of Hebrew text fixer for History files.
This script uses test directories to verify the fixer works correctly.
"""

import json
import os
import re
from pathlib import Path
import shutil
from datetime import datetime

# Test directories
TEST_ROOT = Path(r"E:\My Drive\Rentals\reciptGen\test_hebrew_fix")
TEST_HISTORY_DIR = TEST_ROOT / "History"
TEST_BACKUP_DIR = TEST_ROOT / "History_backup"

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
    
    print(f"    Fixing Hebrew: '{text}'")
    
    # Reverse the entire string first
    fixed_text = text[::-1]
    
    # Fix year patterns that got reversed
    # 62 -> 26 (should be 2026)
    # 52 -> 25 (should be 2025)
    # 6202 -> 2026
    # 5202 -> 2025
    year_fixes = {
        '62': '26',      # 2026
        '52': '25',      # 2025
        '6202': '2026',  # 2026
        '5202': '2025',  # 2025
    }
    
    # Apply year fixes
    original_fixed = fixed_text
    for wrong_year, correct_year in year_fixes.items():
        if wrong_year in fixed_text:
            fixed_text = fixed_text.replace(wrong_year, correct_year)
            print(f"      Fixed year: {wrong_year} -> {correct_year}")
    
    if original_fixed != fixed_text:
        print(f"    Result: '{fixed_text}'")
    else:
        print(f"    Result: '{fixed_text}' (no year fix)")
    
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
        
        print(f"  Processing {file_path.name}:")
        
        # Process the data
        original_data = json.dumps(data, ensure_ascii=False)
        fixed_data = process_value(data)
        fixed_json = json.dumps(fixed_data, indent=2, ensure_ascii=False)
        
        # Check if any changes were made
        if original_data != fixed_json:
            print(f"  ✓ Fixed Hebrew text in {file_path.name}")
            return fixed_json
        else:
            print(f"  - No Hebrew text fixes needed in {file_path.name}")
            return None
            
    except Exception as e:
        print(f"  ✗ Error processing {file_path.name}: {e}")
        return None

def create_backup():
    """
    Create a backup of the test History folder.
    """
    if TEST_BACKUP_DIR.exists():
        print(f"Test backup directory already exists: {TEST_BACKUP_DIR}")
        return
    
    print(f"Creating test backup: {TEST_BACKUP_DIR}")
    shutil.copytree(TEST_HISTORY_DIR, TEST_BACKUP_DIR)
    print("Test backup created successfully.")

def show_before_after():
    """Show before and after comparison for verification."""
    print("\n" + "="*60)
    print("BEFORE AND AFTER COMPARISON")
    print("="*60)
    
    for json_file in sorted(TEST_HISTORY_DIR.glob("*.json")):
        print(f"\n{json_file.name}:")
        print("-" * 40)
        
        # Show original (from backup)
        backup_file = TEST_BACKUP_DIR / json_file.name
        if backup_file.exists():
            with open(backup_file, 'r', encoding='utf-8') as f:
                original = f.read()
            print("BEFORE:")
            print(original)
        
        # Show fixed
        with open(json_file, 'r', encoding='utf-8') as f:
            fixed = f.read()
        print("AFTER:")
        print(fixed)

def main():
    """
    Main function to process test JSON files.
    """
    print("Test Hebrew Text Fixer for History Files")
    print("=" * 50)
    
    # Check if test directories exist
    if not TEST_HISTORY_DIR.exists():
        print(f"Error: Test History directory not found: {TEST_HISTORY_DIR}")
        print("Please run test_hebrew_fixer.py first to create test environment.")
        return
    
    # Create backup
    create_backup()
    
    # Get all JSON files
    json_files = list(TEST_HISTORY_DIR.glob("*.json"))
    total_files = len(json_files)
    
    if total_files == 0:
        print("No JSON files found in test History directory.")
        return
    
    print(f"Found {total_files} test JSON files to process.")
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
                print(f"  ✗ Error writing fixed file: {e}")
                error_count += 1
        elif fixed_json is None:
            # No changes needed (not an error)
            pass
        else:
            error_count += 1
    
    print()
    print("Test processing complete!")
    print(f"Total files: {total_files}")
    print(f"Files fixed: {fixed_count}")
    print(f"Errors: {error_count}")
    print(f"Test backup location: {TEST_BACKUP_DIR}")
    
    if fixed_count > 0:
        print()
        print("✅ Hebrew text has been fixed in the test files!")
    
    if error_count > 0:
        print()
        print("⚠️  Some files had errors. Check the output above for details.")
    
    # Show before and after comparison
    show_before_after()

if __name__ == "__main__":
    main()
