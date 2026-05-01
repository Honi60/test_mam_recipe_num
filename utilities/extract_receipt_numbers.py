#!/usr/bin/env python3
"""Extract receipt numbers from all PDF files in customer folders."""

import argparse
import json
import os
import re
import sys
import pdfplumber

# Hardcoded production paths (from paths.py else branch)
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


def extract_receipt_number_from_pdf(pdf_path):
    """Extract receipt number from PDF text. Assumes 5-digit format."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            # Find all 5-digit numbers
            matches = re.findall(r'\b\d{5}\b', text)
            if matches:
                # Assume the first 5-digit number is the receipt number
                return matches[0]
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return None


def main():
    # Always use production paths (hardcoded from paths.py else branch)
    receipt_root = PRODUCTION_ROOT
    customer_file = CUSTOMER_FILE
    mode = 'PRODUCTION (hardcoded)'

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

    folders = {}
    for name, data in customers.items():
        folder = extract_save_folder_from_customer_data(data)
        if folder:
            folders.setdefault(folder, []).append(name)

    receipt_numbers = {}  # num: list of pdf_files
    total_pdfs = 0
    no_num_count = 0

    for folder, names in sorted(folders.items()):
        if os.path.exists(folder):
            try:
                all_files = os.listdir(folder)
                pdf_files = [f for f in all_files if f.lower().endswith('.pdf')]
                total_pdfs += len(pdf_files)
                for pdf_file in pdf_files:
                    pdf_path = os.path.join(folder, pdf_file)
                    receipt_num = extract_receipt_number_from_pdf(pdf_path)
                    if receipt_num:
                        if receipt_num not in receipt_numbers:
                            receipt_numbers[receipt_num] = []
                        receipt_numbers[receipt_num].append(pdf_file)
                    else:
                        no_num_count += 1
            except Exception as e:
                print(f"Error reading folder {folder}: {e}")

    print()
    print(f"Total PDFs processed: {total_pdfs}")
    print(f"Unique receipt numbers found: {len(receipt_numbers)}")
    print(f"PDFs without receipt number: {no_num_count}")
    print()
    print("All receipt numbers:")
    for num in sorted(receipt_numbers):
        files = receipt_numbers[num]
        file_str = ", ".join(files)
        print(f"{num} - {file_str}")


if __name__ == '__main__':
    main()