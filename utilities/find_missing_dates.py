#!/usr/bin/env python3
"""Find JSON files with missing or empty Date field, handling both flat and data/info structures"""

import json
import os
import sys
from pathlib import Path

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

def extract_receipt_data(data, filename):
    """Extract receipt data from various JSON structures"""
    
    receipt_num = filename.stem
    customer_name = 'Unknown'
    date_value = 'Unknown'
    payment_value = 'Unknown'
    
    if isinstance(data, dict):
        if 'data' in data:
            # Structure: {"data": {"receipt_num": {...}, "info": {...}}
            data_section = data['data']
            if isinstance(data_section, dict):
                # Get first receipt from data section
                receipt_keys = list(data_section.keys())
                if receipt_keys:
                    receipt_data = data_section[receipt_keys[0]]
                    receipt_num = receipt_keys[0]  # Use actual key from data
                    customer_name = receipt_data.get('customer', 'Unknown')
                    date_value = receipt_data.get('Date', 'Unknown')
                    payment_value = receipt_data.get('payment', 'Unknown')
        elif len(data) == 1:
            # Structure: {"receipt_num": {...}}
            receipt_data = list(data.values())[0]
            customer_name = receipt_data.get('customer', 'Unknown')
            date_value = receipt_data.get('Date', 'Unknown')
            payment_value = receipt_data.get('payment', 'Unknown')
        else:
            # Structure: {"customer": "...", "Date": "...", ...}
            customer_name = data.get('customer', 'Unknown')
            date_value = data.get('Date', 'Unknown')
            payment_value = data.get('payment', 'Unknown')
    
    return receipt_num, customer_name, date_value, payment_value

def find_missing_dates():
    """Find JSON files with missing or empty Date field"""
    
    if not HISTORY_DIR.exists():
        safe_print('History directory not found: ' + str(HISTORY_DIR))
        return
    
    safe_print('Scanning for missing Date fields in: ' + str(HISTORY_DIR))
    safe_print('=' * 80)
    
    missing_date_files = []
    total_files = 0
    
    # Scan all JSON files
    for json_file in sorted(HISTORY_DIR.glob('*.json')):
        total_files += 1
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            receipt_num, customer_name, date_value, payment_value = extract_receipt_data(data, json_file)
            
            # Check if Date field is missing or empty
            if not date_value or date_value == '' or date_value == 'Unknown':
                missing_date_files.append({
                    'filename': json_file.name,
                    'receipt_num': receipt_num,
                    'customer': customer_name,
                    'payment': payment_value,
                    'date_status': 'Missing' if not date_value else 'Empty'
                })
                
        except Exception as e:
            # For files with errors, we'll still include them as potentially missing dates
            missing_date_files.append({
                'filename': json_file.name,
                'receipt_num': json_file.stem,
                'customer': 'ERROR',
                'payment': 'ERROR',
                'date_status': f'Error: {e}'
            })
    
    # Sort by receipt number
    missing_date_files.sort(key=lambda x: x['receipt_num'])
    
    # Print focused report
    safe_print(f'\nFiles with Missing/Empty Date Field ({len(missing_date_files)} files):')
    safe_print('=' * 80)
    safe_print(f'{"Receipt #":<15} {"Customer":<25} {"Payment":<12} {"Status":<15}')
    safe_print('-' * 80)
    
    for i, file_info in enumerate(missing_date_files, 1):
        safe_print(f'{file_info["receipt_num"]:<15} {file_info["customer"]:<25} {file_info["payment"]:<12} {file_info["date_status"]:<15}')
    
    safe_print('-' * 80)
    safe_print(f'Total files scanned: {total_files}')
    safe_print(f'Files with missing/empty dates: {len(missing_date_files)}')
    
    # Save to file
    report_file = SCRIPT_DIR.parent / 'Data' / 'missing_dates_only.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('JSON Files with Missing/Empty Date Field\n')
        f.write('=' * 80 + '\n')
        f.write(f'{"Receipt #":<15} {"Customer":<25} {"Payment":<12} {"Status":<15}\n')
        f.write('=' * 80 + '\n')
        
        for file_info in missing_date_files:
            f.write(f'{file_info["receipt_num"]:<15} {file_info["customer"]:<25} {file_info["payment"]:<12} {file_info["date_status"]:<15}\n')
        
        f.write('=' * 80 + '\n')
        f.write(f'Total files scanned: {total_files}\n')
        f.write(f'Files with missing/empty dates: {len(missing_date_files)}\n')
    
    safe_print(f'\nReport saved to: {report_file}')

if __name__ == '__main__':
    find_missing_dates()
