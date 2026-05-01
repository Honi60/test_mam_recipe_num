#!/usr/bin/env python3
"""List receipt numbers and customer names from history JSON files."""

import json
import os
import sys
from pathlib import Path

# Add the parent project directory so config.paths can be imported from utilities
script_dir = Path(__file__).resolve().parent
project_dir = script_dir.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from config.paths import HISTORY_DIR


def normalize_history_entry(raw):
    if not isinstance(raw, dict):
        return {"data": {}, "info": {}}
    if "data" in raw and isinstance(raw["data"], dict):
        info = raw.get("info", {})
        return {"data": raw["data"], "info": info if isinstance(info, dict) else {}}
    if len(raw) == 1:
        inner = list(raw.values())[0]
        if isinstance(inner, dict):
            return {"data": inner, "info": {}}
    return {"data": raw, "info": {}}


def load_history_entries(history_dir):
    entries = []
    history_path = Path(history_dir)
    if not history_path.exists():
        return entries

    for filename in sorted(history_path.iterdir()):
        if filename.suffix.lower() != ".json":
            continue
        try:
            with filename.open('r', encoding='utf-8') as f:
                raw = json.load(f)
        except Exception:
            continue

        normalized = normalize_history_entry(raw)
        info = normalized.get('info', {})
        data = normalized.get('data', {})
        receipt_number = str(info.get('receipt_number') or data.get('recipeNum') or data.get('CheckNumber') or data.get('invoice_no') or data.get('receipt_number') or '').strip()
        customer_name = str(info.get('customer') or data.get('customer') or data.get('Customer') or data.get('customer_name') or data.get('CustomerName') or '').strip()
        if receipt_number or customer_name:
            entries.append((filename.name, receipt_number, customer_name))

    return entries


def print_table(rows):
    if not rows:
        print("No history entries found.")
        return

    receipt_col = "Receipt #"
    customer_col = "Customer"
    file_col = "File"

    receipt_width = max(len(receipt_col), max(len(r[1]) for r in rows))
    customer_width = max(len(customer_col), max(len(r[2]) for r in rows))
    file_width = max(len(file_col), max(len(r[0]) for r in rows))

    header = f"{receipt_col:<{receipt_width}}  {customer_col:<{customer_width}}  {file_col:<{file_width}}"
    separator = f"{'-' * receipt_width}  {'-' * customer_width}  {'-' * file_width}"

    print(header)
    print(separator)
    for filename, receipt_number, customer_name in rows:
        print(f"{receipt_number:<{receipt_width}}  {customer_name:<{customer_width}}  {filename:<{file_width}}")


def main():
    entries = load_history_entries(HISTORY_DIR)
    print_table(entries)
    print()
    print(f"History directory: {HISTORY_DIR}")
    print(f"Entries processed: {len(entries)}")


if __name__ == '__main__':
    main()