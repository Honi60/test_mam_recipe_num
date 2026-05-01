#!/usr/bin/env python3
"""Scan History folder and fix JSON files missing data/info sections"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR.parent))

from config import paths

HISTORY_DIR = Path(paths.DB_DIR) / "History"
COMPARE_FILE = SCRIPT_DIR.parent / 'Data' / 'compare.txt'
CUSTOMERS_FILE = Path(paths.CUSTOMERS_FILE)

def safe_print(text):
    """Safely print text that might contain Hebrew characters"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(repr(text))

def get_customer_info_from_db(hebrew_customer_name, payment_amount='', save_folder=''):
    """Get customer info from customers_data.json using Hebrew name, payment amount, and save folder"""
    try:
        if not CUSTOMERS_FILE.exists():
            return hebrew_customer_name  # Fallback to Hebrew name
        
        with open(CUSTOMERS_FILE, 'r', encoding='utf-8') as f:
            customers_data = json.load(f)
        
        # Try exact Hebrew name match first
        for customer_key, customer_info in customers_data.items():
            if isinstance(customer_info, dict):
                customer_hebrew_name = customer_info.get('customer', '')
                if customer_hebrew_name == hebrew_customer_name:
                    return customer_key  # Return the English key
        
        # If not found, try payment amount matching (more reliable)
        if payment_amount:
            for customer_key, customer_info in customers_data.items():
                if isinstance(customer_info, dict):
                    customer_payment = customer_info.get('payment', '')
                    if customer_payment == payment_amount:
                        return customer_key
        
        # Try folder name matching
        if save_folder:
            folder_name = Path(save_folder).name
            folder_mappings = {
                'אילנה': 'Ilana_salon',
                'טל': 'Tal',
                'דליה': 'Dalya',
                'מוטי': 'Moti',
                'קמי': 'Kami',
                'גזוז': 'Gazoz',
                'אלה': 'Ela',
                'בנימין': 'Binyamin',
                'נתן': 'Natan'
            }
            hebrew_folder = folder_mappings.get(folder_name)
            if hebrew_folder:
                return hebrew_folder
        
        # Try to match based on Hebrew text patterns
        hebrew_customer_name_lower = hebrew_customer_name.lower()
        
        # Check for specific Hebrew names in the customer text
        if 'אילנה' in hebrew_customer_name:
            return 'Ilana_salon'  # Default to salon for Ilana
        elif 'טל' in hebrew_customer_name:
            return 'Tal'
        elif 'דליה' in hebrew_customer_name:
            return 'Dalya'
        elif 'מוטי' in hebrew_customer_name:
            return 'Moti'
        elif 'קמי' in hebrew_customer_name:
            return 'Kami'
        elif 'גזוז' in hebrew_customer_name:
            return 'Gazoz'
        elif 'אלה' in hebrew_customer_name:
            return 'Ela'
        elif 'בנימין' in hebrew_customer_name:
            return 'Binyamin'
        
        return hebrew_customer_name  # Final fallback
    except Exception as e:
        safe_print(f"Error matching customer: {e}")
        return hebrew_customer_name  # Fallback to Hebrew name

def load_compare_data():
    """Load compare.txt data to locate PDF files"""
    if not COMPARE_FILE.exists():
        safe_print(f'Compare file not found: {COMPARE_FILE}')
        return {}
    
    compare_data = {}
    with open(COMPARE_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find header line to determine column positions
    header_line = None
    for line in lines:
        if line.strip() and 'No' in line and 'Yes' in line:
            header_line = line.strip()
            break
    
    if not header_line:
        safe_print("Could not find header line in compare.txt")
        return {}
    
    # Parse data lines
    for line in lines:
        line = line.strip()
        if not line or line.startswith('000'):
            continue
        
        parts = line.split()
        if len(parts) >= 4:
            receipt_num = parts[0]
            customer_name = ' '.join(parts[1:-3])  # Customer name between receipt and Yes/No
            in_history = parts[-3]  # Yes/No column
            pdf_path = parts[-1] if len(parts) > 4 else ''
            
            if in_history == 'Yes' and pdf_path:
                compare_data[receipt_num] = {
                    'customer': customer_name,
                    'pdf_path': pdf_path
                }
    
    safe_print(f"Loaded {len(compare_data)} receipts from compare.txt")
    return compare_data

def fix_json_file(json_file, receipt_info):
    """Fix a single JSON file to have proper data and info sections"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if it's already in correct format
        if isinstance(data, dict) and 'data' in data and 'info' in data:
            safe_print(f"  Already has correct structure: {json_file.name}")
            return False  # No changes needed
        
        # If it's a flat structure, convert to nested format
        if isinstance(data, dict) and any(key in data for key in ["recipeNum", "Date", "customer"]):
            # This is flat structure, convert to nested
            receipt_data = data.copy()
            
            # Get customer name from database
            english_customer_name = get_customer_info_from_db(
                receipt_data.get('customer', ''),
                receipt_data.get('payment', ''),
                receipt_data.get('SaveFolder', '')
            )
            
            # Get creation date from PDF file if available
            creation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Default fallback
            if receipt_info and 'pdf_path' in receipt_info:
                try:
                    pdf_path = Path(receipt_info['pdf_path'])
                    if pdf_path.exists():
                        creation_time = pdf_path.stat().st_ctime
                        creation_date = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
                        safe_print(f"    Using PDF creation date: {creation_date}")
                except Exception as e:
                    safe_print(f"    Could not get PDF creation date: {e}")
                    # Keep default current time if PDF date fails
            
            # Create new structure
            new_structure = {
                "data": receipt_data,
                "info": {
                    "creation_date": creation_date,
                    "customer_name": english_customer_name
                }
            }
            
            # Write back to file
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(new_structure, f, indent=2, ensure_ascii=False)
            
            safe_print(f"  FIXED: Added info section with {english_customer_name}")
            return True
        
        safe_print(f"  Unknown structure: {type(data)}")
        return False
        
    except Exception as e:
        safe_print(f"  ERROR fixing {json_file.name}: {e}")
        return False

def fix_history_json_files():
    """Scan History folder and fix JSON files missing data/info sections"""
    
    if not HISTORY_DIR.exists():
        safe_print(f'History directory not found: {HISTORY_DIR}')
        return
    
    safe_print('Scanning History folder for JSON files to fix...')
    safe_print('=' * 80)
    
    # Load compare data to locate PDF files
    compare_data = load_compare_data()
    
    json_files = list(HISTORY_DIR.glob('*.json'))
    fixed_count = 0
    error_count = 0
    already_correct_count = 0
    
    for json_file in sorted(json_files):
        safe_print(f"Processing: {json_file.name}")
        
        # Get receipt info from compare data
        receipt_num = json_file.stem
        receipt_info = compare_data.get(receipt_num, {})
        
        # Try to fix the file
        if fix_json_file(json_file, receipt_info):
            fixed_count += 1
        else:
            # Check if it was already correct
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict) and 'data' in data and 'info' in data:
                    already_correct_count += 1
                else:
                    error_count += 1
            except Exception:
                error_count += 1
    
    safe_print('=' * 80)
    safe_print('Summary:')
    safe_print(f'  Total files processed: {len(json_files)}')
    safe_print(f'  Files fixed: {fixed_count}')
    safe_print(f'  Already correct: {already_correct_count}')
    safe_print(f'  Errors: {error_count}')
    safe_print(f'  Files with proper structure: {fixed_count + already_correct_count}')

if __name__ == '__main__':
    fix_history_json_files()
