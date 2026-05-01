#!/usr/bin/env python3
"""
One-time script to convert history files from old naming convention to new one.

Old format: {customer}_{YYYYMMDDTHHMMSS}.json
New format: {customer}_{YYYYMMDD}_{HHMMSS}_{receipt_num}.json
"""

import os
import json
import re
import sys
from datetime import datetime

# Ensure the parent package directory is on sys.path so `config` can be imported
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config.paths import HISTORY_DIR, USE_SIMULATION, get_mode_label

def safe_filename_part(s: str) -> str:
    """Make string safe for filenames (same as in the main app)"""
    if not s:
        return ""
    s = s.strip()
    s = re.sub(r"[\\/:*?\"<>|]+", "", s)
    s = re.sub(r"\s+", "_", s)
    return s


def parse_json_date(value: str):
    """Parse a date/time string from history JSON."""
    if not value or not isinstance(value, str):
        return None

    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y%m%dT%H%M%S",
        "%Y%m%d%H%M%S",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%d/%m/%y",
        "%Y-%m-%d",
        "%Y/%m/%d",
    ):
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            continue
    return None

def convert_history_filenames():
    """Convert all history files to new naming convention"""

    print(f"Running in {get_mode_label()} mode")
    print(f"Converting files in: {HISTORY_DIR}")
    print("=" * 50)

    if not os.path.exists(HISTORY_DIR):
        print(f"History directory not found: {HISTORY_DIR}")
        return

    converted_count = 0
    error_count = 0

    for filename in os.listdir(HISTORY_DIR):
        if not filename.endswith('.json'):
            continue

        old_path = os.path.join(HISTORY_DIR, filename)

        try:
            # Read JSON to get the name data
            with open(old_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            receipt_num = str(data.get('recipeNum') or data.get('invoice_no') or data.get('CheckNumber') or '').strip()
            if not receipt_num:
                print(f"Skipping {filename} - no receipt number found in JSON")
                error_count += 1
                continue

            customer_name = str(data.get('customer') or data.get('Customer') or data.get('customer_name') or data.get('CustomerName') or '').strip()
            if not customer_name:
                # Fallback to file name prefix if JSON lacks customer field
                name_without_ext = filename[:-5]
                customer_name = name_without_ext.split('_')[0]

            # Try to derive date/time from JSON fields first
            date_value = data.get('Date') or data.get('date') or data.get('created_at') or data.get('timestamp')
            dt = parse_json_date(date_value) if date_value else None

            # Fallback to file modification time when JSON has no usable date/time
            if not dt:
                dt = datetime.fromtimestamp(os.path.getmtime(old_path))

            date_str = dt.strftime('%Y%m%d')
            time_str = dt.strftime('%H%M%S')

            # Create new filename using JSON data
            safe_customer = safe_filename_part(customer_name)
            new_filename = f"{safe_customer}_{date_str}_{time_str}_{receipt_num}.json"
            new_path = os.path.join(HISTORY_DIR, new_filename)

            # Check if new file already exists
            if os.path.exists(new_path):
                print(f"Skipping {filename} - target file already exists: {new_filename}")
                error_count += 1
                continue

            # Rename file
            os.rename(old_path, new_path)
            print(f"✓ Converted: {filename} → {new_filename}")
            converted_count += 1

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            error_count += 1

    print("=" * 50)
    print(f"Conversion complete: {converted_count} files converted, {error_count} errors")

if __name__ == "__main__":
    convert_history_filenames()