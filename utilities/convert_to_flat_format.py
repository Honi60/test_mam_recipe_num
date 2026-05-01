#!/usr/bin/env python3
"""Convert all JSON files in data/additions from nested receipt format to flat format"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR.parent))

ADDITIONS_DIR = SCRIPT_DIR.parent / 'Data' / 'additions'

def safe_print(text):
    """Safely print text that might contain Hebrew characters"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(repr(text))

def convert_json_to_flat_format(json_file):
    """Convert a single JSON file from nested to flat format"""
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if it's already in flat format
        if isinstance(data, dict) and 'data' in data:
            data_section = data['data']
            if isinstance(data_section, dict):
                # Check if data section has receipt number keys (nested format)
                receipt_keys = list(data_section.keys())
                if receipt_keys and isinstance(data_section[receipt_keys[0]], dict) and 'customer' in data_section[receipt_keys[0]]:
                    # This is nested format, convert to flat
                    receipt_data = data_section[receipt_keys[0]]
                    info_section = data.get('info', {})
                    
                    # Create new flat format
                    new_format = {
                        "data": receipt_data,
                        "info": info_section
                    }
                    
                    return new_format, True  # Converted
        
        # Already in flat format or different structure
        return data, False  # No conversion needed
        
    except Exception as e:
        safe_print(f'Error reading {json_file}: {e}')
        return None, False

def convert_all_files():
    """Convert all JSON files in additions directory to flat format"""
    
    if not ADDITIONS_DIR.exists():
        safe_print('Additions directory not found: ' + str(ADDITIONS_DIR))
        return
    
    safe_print('Converting JSON files to flat format in: ' + str(ADDITIONS_DIR))
    safe_print('=' * 80)
    
    json_files = list(ADDITIONS_DIR.glob('*.json'))
    converted_count = 0
    error_count = 0
    
    for json_file in sorted(json_files):
        safe_print(f'Processing: {json_file.name}')
        
        # Convert to flat format
        new_data, was_converted = convert_json_to_flat_format(json_file)
        
        if new_data is None:
            error_count += 1
            safe_print(f'  ERROR: Could not process file')
            continue
        
        if was_converted:
            # Backup original file
            backup_file = json_file.with_suffix('.json.backup')
            try:
                with open(json_file, 'r', encoding='utf-8') as original:
                    with open(backup_file, 'w', encoding='utf-8') as backup:
                        backup.write(original.read())
                
                # Write new format
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2, ensure_ascii=False)
                
                converted_count += 1
                safe_print(f'  CONVERTED (backup saved as {backup_file.name})')
                
            except Exception as e:
                error_count += 1
                safe_print(f'  ERROR saving converted file: {e}')
        else:
            safe_print(f'  Already in flat format - no conversion needed')
    
    safe_print('=' * 80)
    safe_print(f'Conversion Summary:')
    safe_print(f'  Total files processed: {len(json_files)}')
    safe_print(f'  Files converted: {converted_count}')
    safe_print(f'  Errors: {error_count}')
    safe_print(f'  Files already in correct format: {len(json_files) - converted_count - error_count}')

if __name__ == '__main__':
    convert_all_files()
