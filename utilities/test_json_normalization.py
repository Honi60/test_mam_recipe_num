#!/usr/bin/env python3
"""Test the normalize_history_entry function with different JSON structures"""

import sys
from pathlib import Path

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR.parent))

def normalize_history_entry(raw):
    if not isinstance(raw, dict):
        return {"data": {}, "info": {}}
    
    # Check for nested structure with data and info sections
    if "data" in raw and isinstance(raw["data"], dict):
        info = raw.get("info", {})
        return {"data": raw["data"], "info": info if isinstance(info, dict) else {}}
    
    # Check for flat structure (direct receipt fields)
    # If it has receipt fields like recipeNum, Date, customer, treat as flat structure
    if isinstance(raw, dict) and any(key in raw for key in ["recipeNum", "Date", "customer"]):
        return {"data": raw, "info": {}}
    
    # Fallback: if it has one nested dict, extract it
    if len(raw) == 1:
        inner = list(raw.values())[0]
        if isinstance(inner, dict):
            return {"data": inner, "info": {}}
    
    return {"data": raw, "info": {}}

def test_normalization():
    """Test normalization with different JSON structures"""
    
    print("Testing JSON normalization:")
    print("=" * 50)
    
    # Test 1: Nested structure (new format)
    nested_data = {
        "data": {
            "recipeNum": "01730",
            "customer": "Test Customer",
            "Date": "10/9/25"
        },
        "info": {
            "customer_name": "Test",
            "creation_date": "2026-01-13 22:59:21"
        }
    }
    
    result = normalize_history_entry(nested_data)
    print("Test 1 - Nested structure:")
    print(f"  Data keys: {list(result['data'].keys())}")
    print(f"  Info keys: {list(result['info'].keys())}")
    print(f"  RecipeNum: {result['data'].get('recipeNum', 'NOT FOUND')}")
    print(f"  Customer: {result['data'].get('customer', 'NOT FOUND')}")
    print(f"  Date: {result['data'].get('Date', 'NOT FOUND')}")
    print()
    
    # Test 2: Flat structure (old format)
    flat_data = {
        "recipeNum": "01759",
        "customer": "אילנה אקרונוב מכון יופי",
        "Date": "10/12/2025",
        "payment": "1029"
    }
    
    result = normalize_history_entry(flat_data)
    print("Test 2 - Flat structure:")
    print(f"  Data keys: {list(result['data'].keys())}")
    print(f"  Info keys: {list(result['info'].keys())}")
    print(f"  RecipeNum: {result['data'].get('recipeNum', 'NOT FOUND')}")
    print(f"  Customer: {result['data'].get('customer', 'NOT FOUND')}")
    print(f"  Date: {result['data'].get('Date', 'NOT FOUND')}")
    print()
    
    # Test 3: Single nested dict structure
    single_nested = {
        "01730": {
            "recipeNum": "01730",
            "customer": "Test Customer",
            "Date": "10/9/25"
        }
    }
    
    result = normalize_history_entry(single_nested)
    print("Test 3 - Single nested structure:")
    print(f"  Data keys: {list(result['data'].keys())}")
    print(f"  Info keys: {list(result['info'].keys())}")
    print(f"  RecipeNum: {result['data'].get('recipeNum', 'NOT FOUND')}")
    print(f"  Customer: {result['data'].get('customer', 'NOT FOUND')}")
    print(f"  Date: {result['data'].get('Date', 'NOT FOUND')}")

if __name__ == '__main__':
    test_normalization()
