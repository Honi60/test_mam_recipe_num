#!/usr/bin/env python3
"""GUI to list PDF files with receipt numbers and open them on click."""

import sys
import os
import json
import re
import pdfplumber
from PyQt5.QtWidgets import QApplication, QListWidget, QListWidgetItem, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt

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
    except Exception:
        return None
    return None


def load_pdf_data():
    """Load all PDFs with their receipt numbers and paths."""
    receipt_pdfs = {}  # num: list of (filename, full_path)

    if not os.path.exists(CUSTOMER_FILE):
        return receipt_pdfs

    customers = load_customers(CUSTOMER_FILE)

    folders = {}
    for name, data in customers.items():
        folder = extract_save_folder_from_customer_data(data)
        if folder:
            folders.setdefault(folder, []).append(name)

    for folder, names in sorted(folders.items()):
        if os.path.exists(folder):
            try:
                all_files = os.listdir(folder)
                pdf_files = [f for f in all_files if f.lower().endswith('.pdf')]
                for pdf_file in pdf_files:
                    pdf_path = os.path.join(folder, pdf_file)
                    receipt_num = extract_receipt_number_from_pdf(pdf_path)
                    if receipt_num:
                        if receipt_num not in receipt_pdfs:
                            receipt_pdfs[receipt_num] = []
                        receipt_pdfs[receipt_num].append((pdf_file, pdf_path))
            except Exception:
                pass

    return receipt_pdfs


class PDFViewerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Receipt Viewer")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.label = QLabel("Double-click a PDF to open it:")
        layout.addWidget(self.label)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.open_pdf)
        layout.addWidget(self.list_widget)

        self.setLayout(layout)

        self.load_data()

    def load_data(self):
        receipt_pdfs = load_pdf_data()
        for num in sorted(receipt_pdfs):
            for filename, path in receipt_pdfs[num]:
                item_text = f"{num} - {filename}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, path)  # Store full path
                self.list_widget.addItem(item)

    def open_pdf(self, item):
        path = item.data(Qt.UserRole)
        if path and os.path.exists(path):
            os.startfile(path)  # Opens with default PDF viewer on Windows


def main():
    app = QApplication(sys.argv)
    window = PDFViewerGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()