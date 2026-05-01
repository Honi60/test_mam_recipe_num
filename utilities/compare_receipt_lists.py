#!/usr/bin/env python3
"""Compare receipt numbers between two list files and print a summary table."""

import argparse
import re
import sys
import glob
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR.parent))
from config import paths

creceipts_file = r"Data\cereipts.txt"
history = r"Data\hist_list.txt"
results_file = r"Data\compare.txt"


def parse_customers_file(text):
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('All receipt numbers:'):
            continue
        if ' - ' in line:
            num, rest = line.split(' - ', 1)
            result[num.strip()] = rest.strip()
    return result


def parse_history_file(text):
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('Receipt #') or line.startswith('---'):
            continue
        parts = re.split(r'\s{2,}', line)
        if len(parts) >= 3:
            num = parts[0].strip()
            cust = parts[1].strip()
            result[num] = cust
    return result


def load_text(path):
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding='utf-8')
    except Exception:
        return None
    return text


def find_pdf_path(receipt_num, customer_name):
    """Find the full path to the PDF file for a given receipt number and customer."""
    # Search both simulation and production directories
    search_dirs = []
    
    # Add current configured directory
    search_dirs.append(Path(paths.RECIEPT_ROOT))
    
    # Add the opposite directory (if in simulation, also search production, and vice versa)
    if paths.USE_SIMULATION:
        search_dirs.append(Path("E:\\My Drive\\Rentals"))
    else:
        search_dirs.append(Path("E:\\simulation_rentals"))
    
    # Extract customer filename from customer data if available
    customer_filename = ""
    if customer_name:
        # Check if customer_name contains a filename (like "Tal.pdf")
        if '.pdf' in customer_name.lower():
            # Extract the filename part
            parts = customer_name.split()
            for part in parts:
                if part.lower().endswith('.pdf'):
                    customer_filename = part
                    break
        
        # Extract folder name: first word before space or underscore
        clean_name = customer_name.replace('.pdf', '').split('_')[0].split()[0]
        customer_folder = clean_name
    else:
        customer_folder = ""
    
    # Try different naming patterns - prioritize broader search first
    possible_names = [
        f"*{receipt_num}*.pdf",           # Any file containing receipt number
        f"*_{receipt_num}.pdf",           # Customer_name_receipt_num.pdf
        f"*_{receipt_num}_*.pdf",         # Customer_name_receipt_num_date.pdf
        f"{receipt_num}.pdf",             # receipt_num.pdf
    ]
    
    # Search in each directory
    for production_dir in search_dirs:
        if not production_dir.exists():
            continue
        
        # First, do a broad recursive search for all patterns
        for pattern in possible_names:
            for pdf_file in production_dir.rglob(pattern):
                if pdf_file.is_file():
                    # Check if this matches our receipt number
                    filename = pdf_file.name
                    if receipt_num in filename:
                        return str(pdf_file)
        
        # If not found and we have a specific customer filename, search for it
        if customer_filename:
            for pdf_file in production_dir.rglob(customer_filename):
                if pdf_file.is_file():
                    return str(pdf_file)
        
        # If not found in broad search, try customer folder specific search
        if customer_folder:
            customer_dir = production_dir / customer_folder
            if customer_dir.exists():
                # Search for patterns in customer folder
                for pattern in possible_names:
                    if '*' in pattern:
                        # Handle wildcard patterns
                        matches = list(customer_dir.glob(pattern))
                        if matches:
                            return str(matches[0])
                    else:
                        pdf_path = customer_dir / pattern
                        if pdf_path.exists():
                            return str(pdf_path)
                
                # Also search for the specific customer filename in customer folder
                if customer_filename:
                    specific_path = customer_dir / customer_filename
                    if specific_path.exists():
                        return str(specific_path)
    
    return ""  # Return empty if not found


def format_table(rows):
    receipt_col = 'Receipt #'
    customer_col = 'Customer'
    history_col = 'In History'
    files_col = 'In Customers Folder'
    pdf_path_col = 'PDF Path'

    receipt_width = max(len(receipt_col), max(len(r[0]) for r in rows))
    customer_width = max(len(customer_col), max(len(r[1]) for r in rows))
    history_width = max(len(history_col), len('Yes'))
    files_width = max(len(files_col), len('Yes'))
    pdf_path_width = max(len(pdf_path_col), max(len(r[4]) if len(r) > 4 else 0 for r in rows))

    header = f"{receipt_col:<{receipt_width}}  {customer_col:<{customer_width}}  {history_col:<{history_width}}  {files_col:<{files_width}}  {pdf_path_col:<{pdf_path_width}}"
    separator = f"{'-' * receipt_width}  {'-' * customer_width}  {'-' * history_width}  {'-' * files_width}  {'-' * pdf_path_width}"
    lines = [header, separator]
    for row in rows:
        receipt, customer, in_history, in_folder = row[:4]
        pdf_path = row[4] if len(row) > 4 else ""
        lines.append(f"{receipt:<{receipt_width}}  {customer:<{customer_width}}  {('Yes' if in_history else 'No'):<{history_width}}  {('Yes' if in_folder else 'No'):<{files_width}}  {pdf_path:<{pdf_path_width}}")
    return '\n'.join(lines)


def print_table(rows):
    if not rows:
        print('No entries to show.')
        return
    print(format_table(rows))


def write_compare_file(rows, output_path, counts):
    lines = [
        f"Customers list entries: {counts['customers']}",
        f"History list entries: {counts['history']}",
        f"Common receipt numbers: {counts['common']}",
        f"Only in customers folder: {counts['only_customers']}",
        f"Only in history: {counts['only_history']}",
        '',
        format_table(rows),
    ]
    output_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_missing_receipts_file(missing_receipts, customers, output_path):
    production_dir = Path(paths.RECIEPT_ROOT)
    lines = [f"Receipts missing from history ({len(missing_receipts)} total):", '']
    for num in sorted(missing_receipts, key=lambda x: int(x) if x.isdigit() else x):
        customer = customers.get(num, 'Unknown')
        pdf_path = find_pdf_path(num, customer)
        lines.append(f"{num} - {customer} - {pdf_path}")
    output_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def parse_args():
    parser = argparse.ArgumentParser(description='Compare receipt lists from two files.')
    parser.add_argument('--customers-file', default=str(SCRIPT_DIR.parent / Path(creceipts_file)),
                        help='Path to the customers receipts list file (default: Data/cereipts.txt)')
    parser.add_argument('--history-file', default=str(SCRIPT_DIR.parent / Path(history)),
                        help='Path to the history receipts list file (default: Data/hist_list.txt)')
    parser.add_argument('--output-file', default=str(SCRIPT_DIR.parent / Path(results_file)),
                        help='Path to write the comparison output file (default: Data/compare.txt)')
    parser.add_argument('--missing-output-file', default=str(SCRIPT_DIR.parent / 'Data' / 'missing_from_history.txt'),
                        help='Path to write the list of missing receipt PDFs (default: Data/missing_from_history.txt)')
    return parser.parse_args()


def main():
    args = parse_args()
    customers_path = Path(args.customers_file)
    history_path = Path(args.history_file)

    print(f'Reading customers file: {customers_path.resolve()}')
    print(f'Reading history file:   {history_path.resolve()}')

    customers_text = load_text(customers_path)
    history_text = load_text(history_path)

    if customers_text is None:
        print(f'File not found or unreadable: {customers_path.resolve()}')
        return
    if history_text is None:
        print(f'File not found or unreadable: {history_path.resolve()}')
        return
    if not customers_text.strip() and not history_text.strip():
        print('Both list files are empty; nothing to compare.')
        print(f'Customers file: {customers_path.resolve()}')
        print(f'History file:   {history_path.resolve()}')
        return

    if not customers_text.strip():
        print(f'File is empty: {customers_path.resolve()}')
        return
    if not history_text.strip():
        print(f'File is empty: {history_path}')
        return

    customers = parse_customers_file(customers_text)
    history = parse_history_file(history_text)

    all_numbers = sorted(set(customers) | set(history), key=lambda x: int(x) if x.isdigit() else x)
    rows = []
    for num in all_numbers:
        customer_name = customers.get(num, history.get(num, ''))
        pdf_path = find_pdf_path(num, customer_name)
        rows.append((num, customer_name, num in history, num in customers, pdf_path))

    counts = {
        'customers': len(customers),
        'history': len(history),
        'common': len([r for r in rows if r[2] and r[3]]),
        'only_customers': len([r for r in rows if r[3] and not r[2]]),
        'only_history': len([r for r in rows if r[2] and not r[3]]),
    }
    print(f"Customers list entries: {counts['customers']}")
    print(f"History list entries: {counts['history']}")
    print(f"Common receipt numbers: {counts['common']}")
    print(f"Only in customers folder: {counts['only_customers']}")
    print(f"Only in history: {counts['only_history']}")
    print()
    print_table(rows)
    write_compare_file(rows, Path(args.output_file), counts)
    print(f'Comparison written to {args.output_file}')

    # Write missing receipts file
    missing_receipts = [num for num, _, in_history, in_customers, _ in rows if in_customers and not in_history]
    if missing_receipts:
        write_missing_receipts_file(missing_receipts, customers, Path(args.missing_output_file))
        print(f'Missing receipts list written to {args.missing_output_file}')
    else:
        print('No receipts missing from history.')


if __name__ == '__main__':
    main()
