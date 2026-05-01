#!/usr/bin/env python3
"""
Test script to create simulation environment for Hebrew text fixer.
This creates test folders and sample JSON files with reversed Hebrew text.
"""

import json
import os
from pathlib import Path
import shutil

# Test directories
TEST_ROOT = Path(r"E:\My Drive\Rentals\reciptGen\test_hebrew_fix")
TEST_HISTORY_DIR = TEST_ROOT / "History"
TEST_BACKUP_DIR = TEST_ROOT / "History_backup"

# Sample data with reversed Hebrew text
TEST_FILES = {
    "01730.json": {
        "recipeNum": "01730",
        "discription": "השכרה לחודש 5202",  # "השכרה לחודש 2025" reversed
        "customer": "שם לקוח",  # "שם לקוח" reversed
        "payment": "4956",
        "mamVal": "18%",
        "Date": "10/9/2025",
        "customer_name": "אילנה_סלון",  # "אילנה_סלון" reversed
        "creation_date": "2025-10-04 22:14:57"
    },
    "01845.json": {
        "recipeNum": "01845",
        "discription": "תשלום עבור שירותים 6202",  # "תשלום עבור שירותים 2026" reversed
        "customer": "דוד כהן",  # "דוד כהן" reversed
        "payment": "1200",
        "mamVal": "18%",
        "Date": "15/11/2026",
        "customer_name": "דוד כהן",  # "דוד כהן" reversed
        "creation_date": "2026-11-15 10:30:00"
    },
    "01967.json": {
        "recipeNum": "01967",
        "discription": "החזר כספי על תקלה",  # "החזר כספי על תקלה" reversed
        "customer": "משה לוי",  # "משה לוי" reversed
        "payment": "500",
        "mamVal": "18%",
        "Date": "20/12/2025",
        "customer_name": "משה לוי",  # "משה לוי" reversed
        "creation_date": "2025-12-20 14:45:00"
    },
    "02089.json": {
        "recipeNum": "02089",
        "discription": "עבודות תחזוקה 62",  # "עבודות תחזוקה 26" reversed (should be 2026)
        "customer": "שרה אברהם",  # "שרה אברהם" reversed
        "payment": "3500",
        "mamVal": "18%",
        "Date": "5/1/2026",
        "customer_name": "שרה אברהם",  # "שרה אברהם" reversed
        "creation_date": "2026-01-05 09:15:00"
    }
}

def create_test_environment():
    """Create test environment with sample files."""
    print("Creating test environment...")
    
    # Clean up existing test directory
    if TEST_ROOT.exists():
        shutil.rmtree(TEST_ROOT)
    
    # Create test directories
    TEST_ROOT.mkdir(parents=True, exist_ok=True)
    TEST_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create test files
    for filename, data in TEST_FILES.items():
        file_path = TEST_HISTORY_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  Created: {filename}")
    
    print(f"Test environment created at: {TEST_ROOT}")
    print(f"Created {len(TEST_FILES)} test files")
    return TEST_HISTORY_DIR, TEST_BACKUP_DIR

def show_test_files():
    """Display the content of test files to verify they contain reversed Hebrew."""
    print("\nTest file contents (showing reversed Hebrew):")
    print("=" * 60)
    
    for filename in sorted(TEST_FILES.keys()):
        file_path = TEST_HISTORY_DIR / filename
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"\n{filename}:")
        print(content)
        print("-" * 40)

if __name__ == "__main__":
    test_history_dir, test_backup_dir = create_test_environment()
    show_test_files()
    
    print(f"\nTest directories:")
    print(f"  History: {test_history_dir}")
    print(f"  Backup:  {test_backup_dir}")
    print("\nYou can now test the Hebrew fixer with these directories.")
