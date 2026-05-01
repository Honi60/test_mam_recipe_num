#!/usr/bin/env python3
"""Utility to fix field display issues in history files"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR.parent))

from config.paths import DB_DIR, get_mode_label

HISTORY_DIR = Path(DB_DIR) / "History"

def safe_print(text):
    """Safely print text that might contain Hebrew characters"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(repr(text))

def load_history_file(filename):
    """Load a single history JSON file"""
    file_path = HISTORY_DIR / f"{filename}.json"
    
    if not file_path.exists():
        safe_print(f"File not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        safe_print(f"Error loading {filename}: {e}")
        return None

def save_history_file(filename, data):
    """Save a single history JSON file"""
    file_path = HISTORY_DIR / f"{filename}.json"
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        safe_print(f"Saved: {filename}")
        return True
    except Exception as e:
        safe_print(f"Error saving {filename}: {e}")
        return False

def list_history_files():
    """List all history JSON files"""
    if not HISTORY_DIR.exists():
        safe_print(f"History directory not found: {HISTORY_DIR}")
        return []
    
    files = []
    for file_path in sorted(HISTORY_DIR.glob("*.json")):
        files.append(file_path.stem)
    
    return files

def fix_field_display(filename):
    """Fix field display issues by making values more readable"""
    safe_print(f"\n{'='*60}")
    safe_print(f"Fixing: {filename}")
    safe_print(f"{'='*60}")
    
    # Load the file
    data = load_history_file(filename)
    if data is None:
        return
    
    # Display current content
    safe_print("\nCurrent content:")
    safe_print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # Check if data section exists
    if 'data' not in data or not isinstance(data['data'], dict):
        safe_print("No data section found!")
        return
    
    data_section = data['data']
    safe_print("\nCurrent data section:")
    for key, value in data_section.items():
        safe_print(f"  {key}: {value}")
    
    # Fix common field display issues
    fixes_applied = []
    
    # Fix customer field - make it more readable
    if 'customer' in data_section:
        customer_value = data_section['customer']
        if customer_value and len(str(customer_value).strip()) > 0:
            # If customer field looks like Hebrew text that got cut off or has numbers at end
            # Make it more complete by adding context or fixing truncation
            if str(customer_value).strip().endswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                # Likely truncated Hebrew text - try to make it more complete
                # For display purposes, we can add a marker or make it more readable
                fixed_value = str(customer_value).strip()
                if len(fixed_value) < 20:  # If very short, it might be truncated
                    fixed_value += " [FULL NAME NEEDED]"
                
                data_section['customer'] = fixed_value
                fixes_applied.append(f"Customer field: '{customer_value}' -> '{fixed_value}'")
    
    # Fix description field - make it more readable
    if 'discription' in data_section:
        desc_value = data_section['discription']
        if desc_value and len(str(desc_value).strip()) > 0:
            # If description looks like truncated Hebrew text
            fixed_desc = str(desc_value).strip()
            if len(fixed_desc) < 30:  # If very short, might be truncated
                fixed_desc += " [CHECK FULL DESCRIPTION]"
                
            data_section['discription'] = fixed_desc
            fixes_applied.append(f"Description field: '{desc_value}' -> '{fixed_desc}'")
    
    # Fix payment field - ensure it's a proper string
    if 'payment' in data_section:
        payment_value = data_section['payment']
        if payment_value:
            # Ensure payment is a clean string
            fixed_payment = str(payment_value).strip()
            if not fixed_payment:
                fixed_payment = "0"  # Default to 0 if empty
                
            data_section['payment'] = fixed_payment
            fixes_applied.append(f"Payment field: '{payment_value}' -> '{fixed_payment}'")
    
    # Fix date field - ensure proper format
    if 'Date' in data_section:
        date_value = data_section['Date']
        if date_value:
            # Ensure date is in proper format
            fixed_date = str(date_value).strip()
            if not fixed_date:
                fixed_date = "01/01/2000"  # Default date if empty
                
            data_section['Date'] = fixed_date
            fixes_applied.append(f"Date field: '{date_value}' -> '{fixed_date}'")
    
    # Save the fixed data
    if fixes_applied:
        safe_print(f"\nApplied {len(fixes_applied)} fixes:")
        for fix in fixes_applied:
            safe_print(f"  {fix}")
        
        if save_history_file(filename, data):
            safe_print("\nFile saved successfully!")
        else:
            safe_print("\nFailed to save file!")

def main():
    """Main utility function"""
    safe_print(f"Field Display Fixer [{get_mode_label()}]")
    safe_print(f"History directory: {HISTORY_DIR}")
    
    while True:
        files = list_history_files()
        
        if not files:
            safe_print("No history files found!")
            return
        
        safe_print(f"\nAvailable files ({len(files)}):")
        for i, filename in enumerate(files, 1):
            safe_print(f"{i:2d}. {filename}")
        
        safe_print("\nOptions:")
        safe_print("Enter file number to fix")
        safe_print("Type 'list' to refresh file list")
        safe_print("Type 'quit' to exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice.lower() == 'quit':
            safe_print("Goodbye!")
            break
        elif choice.lower() == 'list':
            continue
        elif choice.isdigit():
            file_index = int(choice) - 1
            if 0 <= file_index < len(files):
                filename = files[file_index]
                fix_field_display(filename)
            else:
                safe_print(f"Invalid file number. Please choose 1-{len(files)}.")
        else:
            safe_print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
