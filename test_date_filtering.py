#!/usr/bin/env python3
"""Test the date filtering functionality in to_excel_qt.py"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR.parent))

from QtGUI.to_excel_qt import load_receipts_by_month_year, _parse_dd_mm_yyyy_or_yy

def test_date_parsing():
    """Test the date parsing function"""
    print("Testing date parsing function:")
    print("=" * 50)
    
    test_dates = [
        "10/9/25",
        "2/9/25", 
        "12/9/25",
        "13/09/25",
        "30/9/25",
        "22/9/25",
        "15/10/2025",
        "13/10/25",
        "25/4/26",
        "12/1/2026",
        "9.2.2026",
        "10/11/2025",
        "31/12/25",
        "13/1/2026",
        "21/1/2026",
        "2/2/2026",
        "4/3/2026",
        "25/2/2026",
        "12/11/25",
        "12/12/25",
        "15/1/2026",
        "12/2/2026",
        "17/11/2025",
        "13/11/25",
        "13/12/25",
        "13/02/2026",
    ]
    
    for date_str in test_dates:
        parsed = _parse_dd_mm_yyyy_or_yy(date_str)
        if parsed:
            print(f"OK {date_str} -> {parsed.strftime('%Y-%m-%d')} (Month: {parsed.month}, Year: {parsed.year})")
        else:
            print(f"FAIL {date_str} -> FAILED")
    
    print()

def test_month_year_filtering():
    """Test filtering receipts by month and year"""
    print("Testing month/year filtering:")
    print("=" * 50)
    
    # Test different month/year combinations
    test_cases = [
        (9, 2025),  # September 2025
        (10, 2025), # October 2025  
        (1, 2026),  # January 2026
        (2, 2026),  # February 2026
        (3, 2026),  # March 2026
        (4, 2026),  # April 2026
    ]
    
    for month, year in test_cases:
        receipts = load_receipts_by_month_year(month, year)
        print(f"Month {month}, Year {year}: Found {len(receipts)} receipts")
        
        # Show first few receipts as examples
        for i, receipt in enumerate(receipts[:3]):
            customer = receipt.get('customer', 'Unknown')[:20]  # Limit length
            date = receipt.get('Date', 'No date')
            recipe_num = receipt.get('recipeNum', 'No num')
            print(f"  {i+1}. {recipe_num}: {customer}... - {date}")
        
        if len(receipts) > 3:
            print(f"  ... and {len(receipts) - 3} more")
        print()

def test_date_range_filtering():
    """Test finding receipts in a specific date range"""
    print("Testing date range filtering:")
    print("=" * 50)
    
    # Test specific date ranges
    date_ranges = [
        ("01/09/2025", "30/09/2025"),  # September 2025
        ("01/10/2025", "31/10/2025"),  # October 2025
        ("01/01/2026", "31/01/2026"),  # January 2026
        ("01/02/2026", "28/02/2026"),  # February 2026
    ]
    
    for start_date_str, end_date_str in date_ranges:
        start_date = _parse_dd_mm_yyyy_or_yy(start_date_str)
        end_date = _parse_dd_mm_yyyy_or_yy(end_date_str)
        
        if not start_date or not end_date:
            print(f"Invalid date range: {start_date_str} to {end_date_str}")
            continue
        
        print(f"Range {start_date_str} to {end_date_str}:")
        
        # Load all receipts and filter by date range
        from config import paths
        from QtGUI.to_excel_qt import HISTORY_DIR, _unwrap_history_payload
        import os
        import json
        
        matching_receipts = []
        
        if os.path.exists(HISTORY_DIR):
            for filename in sorted(os.listdir(HISTORY_DIR)):
                if filename.endswith('.json'):
                    try:
                        fpath = os.path.join(HISTORY_DIR, filename)
                        with open(fpath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        data = _unwrap_history_payload(data)
                        date_str = data.get('Date', '').strip()
                        
                        if date_str:
                            date_obj = _parse_dd_mm_yyyy_or_yy(date_str)
                            if date_obj and start_date <= date_obj <= end_date:
                                matching_receipts.append(data)
                    except Exception:
                        pass
        
        print(f"  Found {len(matching_receipts)} receipts")
        
        # Show examples
        for i, receipt in enumerate(matching_receipts[:3]):
            customer = receipt.get('customer', 'Unknown')[:20]
            date = receipt.get('Date', 'No date')
            recipe_num = receipt.get('recipeNum', 'No num')
            print(f"    {i+1}. {recipe_num}: {customer}... - {date}")
        
        if len(matching_receipts) > 3:
            print(f"    ... and {len(matching_receipts) - 3} more")
        print()

if __name__ == '__main__':
    test_date_parsing()
    test_month_year_filtering()
    test_date_range_filtering()
