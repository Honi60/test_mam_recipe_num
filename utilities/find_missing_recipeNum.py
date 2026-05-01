#!/usr/bin/env python3
"""
Utility to find all receipts missing recipeNum field in data section.
"""

import json
import os
from pathlib import Path

# Import paths from config
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.paths import HISTORY_DIR, DB_DIR, RECIEPT_ROOT, get_data_mode, print_config

def check_recipeNum(file_path):
    """
    Check if recipeNum exists in data section.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check data section
        if 'data' in data and isinstance(data['data'], dict):
            data_section = data['data']
            if 'recipeNum' in data_section:
                return True, data_section['recipeNum']
            else:
                return False, None
        else:
            # Check flat structure
            if 'recipeNum' in data:
                return True, data['recipeNum']
            else:
                return False, None
                
    except Exception as e:
        print(f"  [ERROR] Error reading {file_path.name}: {e}")
        return False, None

def main():
    """
    Main function to find all files missing recipeNum.
    """
    print("Finding Receipts Missing recipeNum Field")
    print("=" * 50)
    
    # Show current configuration
    try:
        print_config()
    except UnicodeEncodeError:
        print(f"Data Mode: {get_data_mode()}")
        print(f"Receipt Root: {RECIEPT_ROOT}")
        print(f"Database Dir: {DB_DIR}")
    print(f"History Directory: {HISTORY_DIR}")
    print()
    
    # Check if History directory exists
    if not Path(HISTORY_DIR).exists():
        print(f"Error: History directory not found: {HISTORY_DIR}")
        return
    
    # Get all JSON files
    json_files = list(Path(HISTORY_DIR).glob("*.json"))
    total_files = len(json_files)
    
    if total_files == 0:
        print("No JSON files found in History directory.")
        return
    
    print(f"Scanning {total_files} JSON files...")
    print()
    
    # Check each file
    missing_count = 0
    missing_files = []
    
    for file_path in json_files:
        has_recipeNum, recipeNum_value = check_recipeNum(file_path)
        
        if not has_recipeNum:
            missing_count += 1
            missing_files.append(file_path.name)
            print(f"[MISSING] {file_path.name}")
        else:
            print(f"[OK] {file_path.name} - recipeNum: {recipeNum_value}")
    
    print()
    print("=" * 50)
    print(f"Total files: {total_files}")
    print(f"Missing recipeNum: {missing_count}")
    print(f"Have recipeNum: {total_files - missing_count}")
    
    if missing_files:
        print()
        print("Files missing recipeNum:")
        for filename in missing_files:
            print(f"  - {filename}")
    else:
        print()
        print("All files have recipeNum field.")

if __name__ == "__main__":
    main()
