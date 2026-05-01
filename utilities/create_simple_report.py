#!/usr/bin/env python3
"""Create simplified tabular report of receipt numbers and customer names from JSON files"""

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

def create_simple_report():
    """Create simple tabular report of receipt numbers and customer names"""
    
    if not HISTORY_DIR.exists():
        safe_print('History directory not found: ' + str(HISTORY_DIR))
        return
    
    safe_print('Creating simple receipt report from: ' + str(HISTORY_DIR))
    safe_print('=' * 80)
    
    receipts_data = []
    total_files = 0
    
    # Scan all JSON files
    for json_file in sorted(HISTORY_DIR.glob('*.json')):
        total_files += 1
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract receipt number and customer name from various possible structures
            receipt_num = json_file.stem
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
            
            receipts_data.append({
                'filename': json_file.name,
                'receipt_num': receipt_num,
                'customer': customer_name,
                'date': date_value,
                'payment': payment_value
            })
                
        except Exception as e:
            receipts_data.append({
                'filename': json_file.name,
                'receipt_num': json_file.stem,
                'customer': 'ERROR',
                'date': f'Error: {e}',
                'payment': 'ERROR'
            })
    
    # Sort by receipt number
    receipts_data.sort(key=lambda x: x['receipt_num'])
    
    # Print simple tabular report
    safe_print('\nSimple Receipt Report:')
    safe_print('-' * 80)
    safe_print(f'{"Receipt #":<15} {"Customer":<25} {"Date":<12} {"Payment":<10}')
    safe_print('-' * 80)
    
    for i, receipt in enumerate(receipts_data, 1):
        safe_print(f'{receipt["receipt_num"]:<15} {receipt["customer"]:<25} {receipt["date"]:<12} {receipt["payment"]:<10}')
    
    safe_print('-' * 80)
    safe_print(f'Total: {total_files} receipts')
    
    # Save to file
    report_file = SCRIPT_DIR.parent / 'Data' / 'simple_receipt_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('Simple Receipt Report\n')
        f.write('=' * 80 + '\n')
        f.write(f'{"Receipt #":<15} {"Customer":<25} {"Date":<12} {"Payment":<10}\n')
        f.write('=' * 80 + '\n')
        
        for receipt in receipts_data:
            f.write(f'{receipt["receipt_num"]:<15} {receipt["customer"]:<25} {receipt["date"]:<12} {receipt["payment"]:<10}\n')
        
        f.write('=' * 80 + '\n')
        f.write(f'Total receipts: {total_files}\n')
    
    safe_print(f'\nReport saved to: {report_file}')

if __name__ == '__main__':
    create_simple_report()
