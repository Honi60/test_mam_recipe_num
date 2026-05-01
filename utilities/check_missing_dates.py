#!/usr/bin/env python3
"""Utility to scan History folder and list JSON files with missing Date field"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR.parent))
from config import paths

HISTORY_DIR = Path(paths.DB_DIR) / "History"

def safe_print_filename(filename):
    """Safely print filename that might contain Hebrew characters"""
    try:
        # Try to print normally first
        print(filename)
    except UnicodeEncodeError:
        # If that fails, use repr to show the filename
        print(repr(filename))

def check_json_dates():
    """Scan all JSON files in History folder and check for missing Date field"""
    
    if not HISTORY_DIR.exists():
        print('History directory not found:', HISTORY_DIR)
        return
    
    print('Scanning History folder:', HISTORY_DIR)
    print('=' * 60)
    
    files_with_missing_date = []
    total_files = 0
    files_with_dates = 0
    
    # Scan all JSON files
    for json_file in sorted(HISTORY_DIR.glob('*.json')):
        total_files += 1
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check different possible JSON structures
            receipt_data = None
            
            if isinstance(data, dict):
                if 'data' in data:
                    # Structure: {"data": {"receipt_num": {...}, "info": {...}}
                    # OR Structure: {"data": {"discription": "...", "Date": "...", ...}}
                    data_section = data['data']
                    if isinstance(data_section, dict):
                        # Check if data section has receipt number keys (normal structure)
                        receipt_keys = list(data_section.keys())
                        if receipt_keys and isinstance(data_section[receipt_keys[0]], dict) and 'customer' in data_section[receipt_keys[0]]:
                            # Normal structure: receipt number keys containing receipt data
                            receipt_data = data_section[receipt_keys[0]]
                        else:
                            # Direct structure: receipt fields directly in data section
                            receipt_data = data_section
                elif len(data) == 1:
                    # Structure: {"receipt_num": {...}}
                    receipt_data = list(data.values())[0]
                else:
                    # Structure: {"customer": "...", "Date": "...", ...}
                    receipt_data = data
            
            # Check if Date field exists and is not empty
            if receipt_data:
                date_value = receipt_data.get('Date', '')
                if not date_value or date_value == '':
                    files_with_missing_date.append({
                        'filename': json_file.name,
                        'receipt_num': json_file.stem,
                        'issue': 'Missing or empty Date field',
                        'data_keys': list(receipt_data.keys()) if isinstance(receipt_data, dict) else 'Not a dict'
                    })
                else:
                    files_with_dates += 1
                    # Print success with safe filename handling
                    try:
                        print(f'OK {json_file.name}: Date = "{date_value}"')
                    except UnicodeEncodeError:
                        print(f'OK File with date: {json_file.stem}.json')
                        print(f'    Date = "{date_value}"')
            else:
                files_with_missing_date.append({
                    'filename': json_file.name,
                    'receipt_num': json_file.stem,
                    'issue': 'No receipt data found',
                    'structure': str(type(data))
                })
                
        except Exception as e:
            files_with_missing_date.append({
                'filename': json_file.name,
                'receipt_num': json_file.stem,
                'issue': f'Error reading file: {e}'
            })
    
    # Summary
    print(f'\nScan Complete: {total_files} JSON files found')
    print(f'Files with proper Date field: {files_with_dates}')
    print(f'Files with missing/empty Date field: {len(files_with_missing_date)}')
    
    if files_with_missing_date:
        print('\nFiles with missing Date field:')
        print('-' * 60)
        for i, file_info in enumerate(files_with_missing_date, 1):
            print(f'{i:2d}. ', end='')
            safe_print_filename(file_info["filename"])
            print(f'    Receipt #: {file_info["receipt_num"]}')
            print(f'    Issue: {file_info["issue"]}')
            if 'data_keys' in file_info:
                print(f'    Available keys: {file_info["data_keys"]}')
            elif 'structure' in file_info:
                print(f'    Data structure: {file_info["structure"]}')
            print()
        
        # Save report to file
        report_file = SCRIPT_DIR.parent / 'Data' / 'missing_dates_report.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('JSON files with missing Date field\n')
            f.write(f'Scan date: {json.dumps({"timestamp": str(Path().resolve())}, indent=2)}\n')
            f.write(f'Total files scanned: {total_files}\n')
            f.write(f'Files with proper dates: {files_with_dates}\n')
            f.write(f'Files with missing dates: {len(files_with_missing_date)}\n\n')
            
            for file_info in files_with_missing_date:
                f.write(f'File: {file_info["filename"]}\n')
                f.write(f'Receipt #: {file_info["receipt_num"]}\n')
                f.write(f'Issue: {file_info["issue"]}\n')
                if 'data_keys' in file_info:
                    f.write(f'Available keys: {file_info["data_keys"]}\n')
                f.write('-' * 40 + '\n')
        
        print('\nReport saved to:', report_file)
    else:
        print('\nOK All JSON files have Date field populated!')
        print(f'Successfully verified {files_with_dates} files with proper Date fields')

if __name__ == '__main__':
    check_json_dates()
