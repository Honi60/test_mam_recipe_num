#!/usr/bin/env python3
"""List receipt save folders from customers_data.json."""

import argparse
import json
import os
import re
import sys

# Hardcoded production paths (from paths.py else branch)
# RECIEPT_ROOT = "E:\\My Drive\\Rentals"
# DB_DIR = "E:\\My Drive\\Rentals\\RentalsDB"
# CUSTOMERS_FILE = os.path.join(DB_DIR, "customers_data.json")
PRODUCTION_ROOT = r"E:\My Drive\Rentals"
CUSTOMER_FILE = r"E:\My Drive\Rentals\RentalsDB\customers_data.json"

SAVE_FOLDER_KEYS = ("save", "path", "folder", "output")


def resolve_save_folder(raw_save_folder, receipt_root):
    if not raw_save_folder:
        return None
    val = str(raw_save_folder).strip()
    if not val:
        return None
    val = os.path.expanduser(val)
    if os.path.isabs(val):
        return os.path.normpath(val)
    return os.path.normpath(os.path.join(receipt_root, val))


def extract_save_folder_from_customer_data(customer_data):
    if not isinstance(customer_data, dict):
        return None
    for key, val in customer_data.items():
        try:
            klow = str(key).lower()
        except Exception:
            continue
        if any(tok in klow for tok in SAVE_FOLDER_KEYS):
            if isinstance(val, str) and val.strip():
                # Replace simulation root with production root
                val = val.replace(r"E:\simulation_rentals", PRODUCTION_ROOT)
                if os.path.splitext(val)[1].lower() == '.pdf':
                    return resolve_save_folder(os.path.dirname(val), PRODUCTION_ROOT)
                return resolve_save_folder(val, PRODUCTION_ROOT)
    return None


def load_customers(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = eval(text, {})  # fallback for legacy Python-literal formats

    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        result = {}
        for item in data:
            if isinstance(item, dict) and 'customer' in item:
                customer_name = str(item['customer'])
                result[customer_name] = item
            elif isinstance(item, str):
                result[item] = {'customer': item}
        return result
    raise ValueError('Unsupported customer file format')


def parse_args():
    parser = argparse.ArgumentParser(description='List receipt save folders from customers_data.json')
    parser.add_argument('--mode', choices=['simulation', 'production'], default=None,
                        help='Choose SIMULATION or PRODUCTION database mode. Defaults to current config mode.')
    parser.add_argument('--customer-file', default=None,
                        help='Optional override for the customer JSON file path.')
    parser.add_argument('--receipt-root', default=None,
                        help='Optional override for the receipt root directory.')
    return parser.parse_args()


def main():
    args = parse_args()

    # Always use production paths (hardcoded from paths.py else branch)
    receipt_root = PRODUCTION_ROOT
    customer_file = CUSTOMER_FILE
    mode = 'PRODUCTION (hardcoded)'

    if args.receipt_root:
        receipt_root = os.path.normpath(os.path.expanduser(args.receipt_root))
    if args.customer_file:
        customer_file = os.path.normpath(os.path.expanduser(args.customer_file))

    print(f"Mode: {mode}")
    print(f"Receipt root: {receipt_root}")
    print(f"Using customer file: {customer_file}")
    print(f"Customer file exists: {os.path.exists(customer_file)}")
    print()

    if not os.path.exists(customer_file):
        print(f"Customer file not found: {customer_file}")
        return

    customers = load_customers(customer_file)
    print(f"Loaded {len(customers)} customers from file")
    
    # Debug: show first few customers and their data
    print("\nFirst few customers and their data:")
    for i, (name, data) in enumerate(list(customers.items())[:3]):
        print(f"  {name}: {data}")
    
    folders = {}
    missing = []

    for name, data in customers.items():
        folder = extract_save_folder_from_customer_data(data)
        if folder:
            folders.setdefault(folder, []).append(name)
        else:
            missing.append(name)

    if folders:
        rows = []
        for folder, names in sorted(folders.items()):
            pdf_count = 0
            if os.path.exists(folder):
                try:
                    all_files = os.listdir(folder)
                    pdf_files = [f for f in all_files if f.lower().endswith('.pdf')]
                    pdf_count = len(pdf_files)
                    print(f"DEBUG: Folder {folder} exists, {len(all_files)} total files, {pdf_count} PDFs")
                    if pdf_count == 0 and len(all_files) > 0:
                        print(f"DEBUG: Sample files: {all_files[:5]}")
                except Exception as e:
                    print(f"DEBUG: Error reading folder {folder}: {e}")
                    pdf_count = 0
            else:
                print(f"DEBUG: Folder {folder} does not exist")
            rows.append((folder, len(names), pdf_count))

        folder_col = "Folder"
        count_col = "Customers"
        pdf_col = "PDFs"
        col1_width = max(len(folder_col), max(len(row[0]) for row in rows))
        col2_width = max(len(count_col), max(len(str(row[1])) for row in rows))
        col3_width = max(len(pdf_col), max(len(str(row[2])) for row in rows))

        print("Found receipt save folders:")
        print(f"{folder_col:<{col1_width}}  {count_col:>{col2_width}}  {pdf_col:>{col3_width}}")
        print(f"{'-' * col1_width}  {'-' * col2_width}  {'-' * col3_width}")
        total_pdfs = 0
        for folder, count, pdfs in rows:
            print(f"{folder:<{col1_width}}  {count:>{col2_width}}  {pdfs:>{col3_width}}")
            total_pdfs += pdfs
        print()
        print(f"Total folders: {len(rows)}")
        print(f"Total PDFs: {total_pdfs}")
    else:
        print("No save folders were found in customer data.")

    if missing:
        print()
        print(f"Customers without a save folder: {len(missing)}")
        print(", ".join(sorted(missing)))


if __name__ == '__main__':
    main()
