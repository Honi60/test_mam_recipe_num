#!/usr/bin/env python3
"""Test parsing both JSON structures"""

import json
from pathlib import Path

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
import sys
sys.path.append(str(SCRIPT_DIR.parent))
from config import paths

HISTORY_DIR = Path(paths.DB_DIR) / "History"

def test_json_parsing():
    """Test parsing both JSON structures"""
    
    # Test normal structure
    normal_file = HISTORY_DIR / "01734.json"
    print("Testing normal structure (01734.json):")
    print("=" * 50)
    
    try:
        with open(normal_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Has 'data' key: {'data' in data}")
        if 'data' in data:
            data_section = data['data']
            receipt_keys = list(data_section.keys())
            print(f"data section keys: {receipt_keys}")
            print(f"First key type: {type(data_section[receipt_keys[0]])}")
            
            # Check if first value has customer field (receipt data)
            first_value = data_section[receipt_keys[0]]
            print(f"First value has customer field: {'customer' in first_value}")
            print(f"Date from first value: {first_value.get('Date', 'NOT FOUND')}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    # Test Binyamin structure
    binyamin_file = HISTORY_DIR / "Binyamin_20260425_152457_00002.json"
    print("Testing Binyamin structure:")
    print("=" * 50)
    
    try:
        with open(binyamin_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Has 'data' key: {'data' in data}")
        if 'data' in data:
            data_section = data['data']
            receipt_keys = list(data_section.keys())
            print(f"data section keys: {receipt_keys}")
            print(f"First key type: {type(data_section[receipt_keys[0]])}")
            
            # Check if first value has customer field
            first_value = data_section[receipt_keys[0]]
            print(f"First value has customer field: {'customer' in first_value}")
            print(f"Date from data section directly: {data_section.get('Date', 'NOT FOUND')}")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_json_parsing()
