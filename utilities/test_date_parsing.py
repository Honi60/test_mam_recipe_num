#!/usr/bin/env python3
"""Test the date parsing function for dd/mm/yyyy format"""

import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR.parent))

def parse_date_dd_mm_yyyy(date_str):
    """Parse date string in dd/mm/yyyy or dd/mm/yy format"""
    if not date_str:
        return None
    
    # Remove common separators and normalize
    date_str = str(date_str).strip().replace('.', '/').replace('-', '/')
    
    # Try different date formats
    formats = [
        "%d/%m/%Y",  # dd/mm/yyyy
        "%d/%m/%y",  # dd/mm/yy
        "%d/%m/%Y",  # dd/mm/yyyy (duplicate for safety)
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def test_date_parsing():
    """Test various date formats"""
    
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
    
    print("Testing date parsing:")
    print("=" * 50)
    
    parsed_dates = []
    for date_str in test_dates:
        parsed = parse_date_dd_mm_yyyy(date_str)
        if parsed:
            parsed_dates.append((date_str, parsed))
            print(f"OK {date_str} -> {parsed.strftime('%Y-%m-%d')}")
        else:
            print(f"FAIL {date_str} -> FAILED")
    
    # Sort by parsed date to verify sorting works
    print("\nSorted by date (newest first):")
    print("=" * 50)
    
    parsed_dates.sort(key=lambda x: x[1], reverse=True)
    for date_str, parsed in parsed_dates[:10]:  # Show first 10
        print(f"{date_str} -> {parsed.strftime('%Y-%m-%d')}")

if __name__ == '__main__':
    test_date_parsing()
