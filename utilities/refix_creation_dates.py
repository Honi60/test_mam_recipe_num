#!/usr/bin/env python3
"""Re-fix creation dates in History JSON files using actual PDF file dates"""

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

def safe_print(text):
    """Safely print text that might contain Hebrew characters"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(repr(text))

def find_pdf_for_receipt(receipt_num, customer_name):
    """Find PDF file for a receipt based on receipt number and customer name"""
    
    # Try multiple search patterns
    search_paths = [
        Path("E:/My Drive/Rentals"),
        Path("E:/simulation_rentals"),
        Path("G:/My Drive/Rentals"),
    ]
    
    customer_folders = {
        'Binyamin': ['בנימין', 'Binyamin'],
        'Dalya': ['דליה', 'Dalya'],
        'Ela': ['אלה', 'Ela'],
        'Gazoz': ['גזוז', 'Gazoz'],
        'Ilana_salon': ['אילנה', 'Ilana'],
        'Kami': ['קמי', 'Kami'],
        'Moti': ['מוטי', 'Moti'],
        'Natan': ['נתן', 'Natan'],
        'Tal': ['טל', 'Tal'],
    }
    
    # Get possible folder names for this customer
    possible_folders = customer_folders.get(customer_name, [customer_name])
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
            
        for folder_name in possible_folders:
            customer_folder = search_path / folder_name
            if not customer_folder.exists():
                continue
            
            # Search for PDF files containing receipt number
            for pdf_file in customer_folder.glob(f"*{receipt_num}*.pdf"):
                if pdf_file.exists():
                    safe_print(f"    Found PDF: {pdf_file}")
                    return pdf_file
    
    return None

def update_creation_date(json_file):
    """Update creation date for a single JSON file"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, dict) or 'data' not in data or 'info' not in data:
            safe_print(f"  Incorrect structure: {json_file.name}")
            return False
        
        receipt_data = data['data']
        info_section = data['info']
        
        receipt_num = receipt_data.get('recipeNum', '')
        customer_name = info_section.get('customer_name', '')
        
        if not receipt_num or not customer_name:
            safe_print(f"  Missing receipt_num or customer_name: {json_file.name}")
            return False
        
        # Find the PDF file
        pdf_file = find_pdf_for_receipt(receipt_num, customer_name)
        
        if pdf_file and pdf_file.exists():
            # Get PDF creation date
            creation_time = pdf_file.stat().st_mtime
            creation_date = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
            
            # Update the info section
            info_section['creation_date'] = creation_date
            print(f"  Creation date: {creation_date}")
            
            # Write back to file
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            safe_print(f"  UPDATED: {json_file.name} -> {creation_date}")
            return True
        else:
            safe_print(f"  PDF not found for receipt {receipt_num}, customer {customer_name}")
            return False
            
    except Exception as e:
        safe_print(f"  ERROR updating {json_file.name}: {e}")
        return False

def refix_all_creation_dates():
    """Re-fix creation dates for all JSON files in History folder"""
    
    if not HISTORY_DIR.exists():
        safe_print(f'History directory not found: {HISTORY_DIR}')
        return
    
    safe_print('Re-fixing creation dates in History folder...')
    safe_print('=' * 80)
    
    json_files = list(HISTORY_DIR.glob('*.json'))
    updated_count = 0
    not_found_count = 0
    error_count = 0
    
    for json_file in sorted(json_files):
        safe_print(f"Processing: {json_file.name}")
        
        if update_creation_date(json_file):
            updated_count += 1
        else:
            not_found_count += 1
    
    safe_print('=' * 80)
    safe_print('Summary:')
    safe_print(f'  Total files processed: {len(json_files)}')
    safe_print(f'  Successfully updated: {updated_count}')
    safe_print(f'  PDF not found: {not_found_count}')
    safe_print(f'  Errors: {error_count}')

if __name__ == '__main__':
    refix_all_creation_dates()
