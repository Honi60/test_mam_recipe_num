#!/usr/bin/env python3
"""Create missing history JSON files from compare.txt for receipts in customers folder but not in history"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
import pdfplumber

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR.parent))
from config import paths

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / 'Data'
COMPARE_FILE = DATA_DIR / 'compare.txt'
ADDITIONS_DIR = DATA_DIR / 'additions'

# Ensure additions directory exists
ADDITIONS_DIR.mkdir(exist_ok=True)


def extract_pdf_data(pdf_path):
    """Extract receipt data from PDF based on actual PDF content structure"""
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text() + '\n'

    lines = text.split('\n')
    
    # Parse receipt number from filename first (most reliable)
    filename_match = re.search(r'(\d+)\.pdf', str(pdf_path))
    if filename_match:
        receipt_number = filename_match.group(1)
    else:
        raise ValueError(f"Could not extract receipt number from {pdf_path}")

    # Extract receipt data based on actual PDF structure
    receipt_data = {
        'receipt_number': receipt_number,
        'discription': '',
        'invoice_no': '0',
        'customer': '',
        'payment': '',
        'mamVal': '',
        'bankAccount': '',
        'BankNumber': '',
        'CheckNumber': '',
        'bank_transfer_referance': '',
        'transfer_bankAccount': '',
        'Date': '',
        'SaveFolder': str(pdf_path.parent)
    }

    # Extract data based on the actual line structure we observed
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Line 2: Receipt number (e.g., '01730')
        if i == 1 and re.match(r'^\d{4,5}$', line):
            receipt_data['receipt_number'] = line
        
        # Lines 2-3: Hebrew customer/description text
        elif i in [2, 3] and re.search(r'[\u0590-\u05FF]', line):
            if not receipt_data['customer']:
                receipt_data['customer'] = line
            elif not receipt_data['discription']:
                receipt_data['discription'] = line
        
        # Line 4: VAT percentage (e.g., '18%')
        elif i == 4 and re.match(r'^\d+%$', line):
            receipt_data['mamVal'] = line
        
        # Line 5: Payment amount (e.g., '4956')
        elif i == 5 and re.match(r'^\d{3,6}$', line):
            receipt_data['payment'] = line
        
        # Line 6: Bank details (e.g., '4956 110448 04/13700 0050734')
        elif i == 6 and re.search(r'\d{3,6}\s+\d{6,}\s+\d{2}/\d{5}\s+\d{7}', line):
            parts = line.split()
            # Extract bank details from the parts
            if len(parts) >= 4:
                if re.match(r'^\d{6,}$', parts[1]):  # bankAccount
                    receipt_data['bankAccount'] = parts[1]
                if re.match(r'^\d{2}/\d{5}$', parts[2]):  # BankNumber
                    receipt_data['BankNumber'] = parts[2]
                if re.match(r'^\d{7}$', parts[3]):  # CheckNumber
                    receipt_data['CheckNumber'] = parts[3]
        
        # Line 7: Date (e.g., '10/9/25')
        elif i == 7 and re.match(r'^\d{1,2}/\d{1,2}/\d{2}$', line):
            receipt_data['Date'] = line

    # Fallback: customer name from path if not found
    if not receipt_data['customer']:
        receipt_data['customer'] = pdf_path.parent.name

    return receipt_data


def get_customer_info_from_db(hebrew_customer_name, payment_amount='', save_folder=''):
    """Get customer info from customers_data.json using Hebrew name, payment amount, and save folder"""
    try:
        customers_file = Path(paths.CUSTOMERS_FILE)
        if not customers_file.exists():
            return hebrew_customer_name  # Fallback to Hebrew name
        
        with open(customers_file, 'r', encoding='utf-8') as f:
            customers_data = json.load(f)
        
        # First try exact Hebrew name matching
        for customer_key, customer_info in customers_data.items():
            if isinstance(customer_info, dict):
                customer_hebrew_name = customer_info.get('customer', '')
                if customer_hebrew_name == hebrew_customer_name:
                    return customer_key  # Return the English key
        
        # If not found, try payment amount matching (more reliable)
        if payment_amount:
            for customer_key, customer_info in customers_data.items():
                if isinstance(customer_info, dict):
                    customer_payment = customer_info.get('payment', '')
                    if customer_payment == payment_amount:
                        return customer_key  # Return the English key
        
        # If still not found, try partial Hebrew name matching
        for customer_key, customer_info in customers_data.items():
            if isinstance(customer_info, dict):
                customer_hebrew_name = customer_info.get('customer', '')
                # Try to match any part of the Hebrew name
                if customer_hebrew_name and hebrew_customer_name:
                    # Extract individual Hebrew words and check if any match
                    hebrew_words = hebrew_customer_name.split()
                    customer_words = customer_hebrew_name.split()
                    
                    # Check if any word from PDF matches any word from database
                    for pdf_word in hebrew_words:
                        for db_word in customer_words:
                            if pdf_word == db_word:
                                return customer_key
        
        # Try save folder matching (very reliable)
        if save_folder:
            folder_name = Path(save_folder).name
            # Map folder names to customer keys
            folder_mappings = {
                'אילנה': 'Ilana_salon',
                'טל': 'Tal',
                'דליה': 'Dalya',
                'מוטי': 'Moti',
                'קמי': 'Kami',
                'גזוז': 'Gazoz',
                'אלה': 'Ela',
                'בנימין': 'Binyamin',
                'parking': 'Tal',  # English folder name
                'פארקינג': 'Tal',  # Hebrew transliteration
            }
            
            if folder_name in folder_mappings:
                return folder_mappings[folder_name]
            
            # Try partial folder name matching
            for folder_key, customer_key in folder_mappings.items():
                if folder_key.lower() in folder_name.lower() or folder_name.lower() in folder_key.lower():
                    return customer_key
        
        # Final fallback: try to extract from folder name or Hebrew text
        hebrew_customer_name_lower = hebrew_customer_name.lower()
        
        # Check for specific Hebrew names in the customer text
        if 'אילנה' in hebrew_customer_name:
            return 'Ilana_salon'  # Default to salon for Ilana
        elif 'טל' in hebrew_customer_name:
            return 'Tal'
        elif 'דליה' in hebrew_customer_name:
            return 'Dalya'
        elif 'מוטי' in hebrew_customer_name:
            return 'Moti'
        elif 'קמי' in hebrew_customer_name:
            return 'Kami'
        elif 'גזוז' in hebrew_customer_name:
            return 'Gazoz'
        elif 'אלה' in hebrew_customer_name:
            return 'Ela'
        elif 'בנימין' in hebrew_customer_name:
            return 'Binyamin'
        
        # Try to match based on the last character (common in Hebrew names)
        if hebrew_customer_name.endswith('ל'):
            return 'Tal'
        elif hebrew_customer_name.endswith('ה'):
            return 'Dalya' or 'Ilana_salon'
        elif hebrew_customer_name.endswith('י'):
            return 'Moti'
        
        return hebrew_customer_name  # Final fallback
    except Exception as e:
        print(f"Error matching customer: {e}")
        return hebrew_customer_name  # Fallback to Hebrew name


def create_history_json(receipt_data, pdf_path):
    """Create history JSON structure with correct field names"""
    receipt_number = receipt_data['receipt_number']
    
    # Create the data structure matching your format
    data = {
        receipt_number: {
            'recipeNum': receipt_data['receipt_number'],
            'discription': receipt_data['discription'],
            'invoice_no': receipt_data['invoice_no'],
            'customer': receipt_data['customer'],
            'payment': receipt_data['payment'],
            'mamVal': receipt_data['mamVal'],
            'bankAccount': receipt_data['bankAccount'],
            'BankNumber': receipt_data['BankNumber'],
            'CheckNumber': receipt_data['CheckNumber'],
            'bank_transfer_referance': receipt_data['bank_transfer_referance'],
            'transfer_bankAccount': receipt_data['transfer_bankAccount'],
            'Date': receipt_data['Date'],
            'SaveFolder': receipt_data['SaveFolder']
        }
    }

    # Get customer name from customers_data.json (English key)
    english_customer_name = get_customer_info_from_db(receipt_data['customer'], receipt_data['payment'], receipt_data['SaveFolder'])
    
    # Get file creation date
    try:
        creation_time = pdf_path.stat().st_ctime
        creation_date = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        creation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    info = {
        'creation_date': creation_date,
        'customer_name': english_customer_name
    }

    return {
        'data': data,
        'info': info
    }


def parse_compare_file():
    """Parse compare.txt to find receipts in customers folder but not in history"""
    missing_receipts = []
    
    if not COMPARE_FILE.exists():
        print(f'Compare file not found: {COMPARE_FILE}')
        return missing_receipts

    with open(COMPARE_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find the header line to determine column positions
    header_line = None
    for i, line in enumerate(lines):
        if 'Receipt #' in line and 'In History' in line and 'In Customers Folder' in line:
            header_line = i
            break
    
    if header_line is None:
        print('Could not find header line in compare.txt')
        return missing_receipts

    # Parse data lines (skip header and separator)
    for line in lines[header_line + 2:]:
        line = line.strip()
        if not line or line.startswith('-'):
            continue

        # Split by whitespace (multiple spaces)
        parts = line.split()
        if len(parts) < 4:
            continue

        receipt_num = parts[0]
        # Customer name might have spaces, find where the Yes/No columns start
        # Look for "No" in In History column and "Yes" in In Customers Folder column
        in_history_idx = None
        in_customers_idx = None
        pdf_path_start_idx = None

        # Find the Yes/No indicators
        for i, part in enumerate(parts):
            if part in ['Yes', 'No'] and in_history_idx is None:
                in_history_idx = i
            elif part in ['Yes', 'No'] and in_history_idx is not None and in_customers_idx is None:
                in_customers_idx = i
                break

        if in_history_idx is None or in_customers_idx is None:
            continue

        # Check if this receipt is in customers folder but not in history
        if parts[in_history_idx] == 'No' and parts[in_customers_idx] == 'Yes':
            # Extract customer name (between receipt number and Yes/No columns)
            customer_parts = parts[1:in_history_idx]
            customer_name = ' '.join(customer_parts)
            
            # Extract PDF path if available (everything after the Yes/No columns)
            pdf_path = ''
            if len(parts) > in_customers_idx + 1:
                pdf_path_parts = parts[in_customers_idx + 1:]
                if pdf_path_parts and pdf_path_parts[0] not in ['Yes', 'No']:
                    pdf_path = ' '.join(pdf_path_parts)

            missing_receipts.append({
                'receipt_num': receipt_num,
                'customer': customer_name,
                'pdf_path': pdf_path
            })

    return missing_receipts


def main():
    missing_receipts = parse_compare_file()
    
    if not missing_receipts:
        print('No receipts found that are in customers folder but missing from history')
        return

    print(f'Found {len(missing_receipts)} receipts to process:')
    for receipt in missing_receipts:
        print(f"  {receipt['receipt_num']} - {receipt['customer']}")
    print()

    created_count = 0
    for receipt_info in missing_receipts:
        receipt_num = receipt_info['receipt_num']
        customer = receipt_info['customer']
        pdf_path_str = receipt_info['pdf_path']

        # Use the PDF path from compare.txt if available, otherwise construct it
        if pdf_path_str and Path(pdf_path_str).exists():
            pdf_path = Path(pdf_path_str)
        else:
            # Try to construct path from customer name
            customer_folder = customer.split()[0].split('_')[0]
            pdf_path = Path(paths.RECIEPT_ROOT) / customer_folder / f"{receipt_num}.pdf"
            # Also try other naming patterns
            if not pdf_path.exists():
                for pattern in [f"*{receipt_num}*.pdf", f"*_{receipt_num}.pdf"]:
                    matches = list(Path(paths.RECIEPT_ROOT).rglob(pattern))
                    if matches:
                        pdf_path = matches[0]
                        break

        if not pdf_path.exists():
            print(f'PDF not found for receipt {receipt_num}: {pdf_path}')
            continue

        try:
            receipt_data = extract_pdf_data(pdf_path)
            history_json = create_history_json(receipt_data, pdf_path)

            output_file = ADDITIONS_DIR / f'{receipt_num}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(history_json, f, indent=2, ensure_ascii=False)

            print(f'Created: {output_file}')
            created_count += 1

        except Exception as e:
            print(f'Error processing receipt {receipt_num}: {e}')

    print(f'\nCreated {created_count} missing history JSON files in {ADDITIONS_DIR}')


if __name__ == '__main__':
    main()