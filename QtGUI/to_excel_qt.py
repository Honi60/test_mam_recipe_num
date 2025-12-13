import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QMessageBox, QFileDialog, QListWidget, QLineEdit, QSpinBox, QApplication)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

DB_DIR = r"E:\MyGoogleDrive\Rentals\RentalsDB"
HISTORY_DIR = os.path.join(DB_DIR, "History")


def _parse_dd_mm_yyyy_or_yy(date_str: str):
    """Parse DD/MM/YYYY or DD/MM/YY where year may be 2 or 4 digits.

    Returns a datetime on success or None on failure. Only accepts
    day/month/year ordering (slashes or common separators).
    """
    if not date_str:
        return None
    s = date_str.strip()
    # Normalize common separators to '/'
    s = s.replace('.', '/').replace('-', '/').strip()

    # Try 4-digit year first, then 2-digit year
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def load_receipts_by_month_year(month: int, year: int):
    """Load receipts matching the specified month/year from History folder."""
    results = []
    if not os.path.exists(HISTORY_DIR):
        return results
    
    try:
        for filename in sorted(os.listdir(HISTORY_DIR)):
            if filename.endswith('.json'):
                try:
                    fpath = os.path.join(HISTORY_DIR, filename)
                    with open(fpath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # Try to match date field
                    date_str = data.get('Date', '').strip()
                    if date_str:
                        # Accept day/month/year where year can be 4 or 2 digits
                        date_obj = _parse_dd_mm_yyyy_or_yy(date_str)
                        if date_obj and date_obj.month == month and date_obj.year == year:
                            results.append(data)
                except Exception:
                    pass
    except Exception:
        pass
    
    return results


class ToExcelApp_Qt(QWidget):
    def __init__(self):
        super().__init__()
        
        # Setup Hebrew-capable font
        available_fonts = ["Alef", "Segoe UI", "Tahoma"]
        self.hebrew_font = QFont()
        for font_name in available_fonts:
            self.hebrew_font.setFamily(font_name)
            if self.hebrew_font.exactMatch():
                break
        self.hebrew_font.setPointSize(10)
        
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Month and Year selector
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Month (1-12):"))
        self.month_spinbox = QSpinBox()
        self.month_spinbox.setMinimum(1)
        self.month_spinbox.setMaximum(12)
        self.month_spinbox.setValue(datetime.now().month)
        input_layout.addWidget(self.month_spinbox)
        
        input_layout.addWidget(QLabel("Year:"))
        self.year_spinbox = QSpinBox()
        self.year_spinbox.setMinimum(2020)
        self.year_spinbox.setMaximum(2100)
        self.year_spinbox.setValue(datetime.now().year)
        input_layout.addWidget(self.year_spinbox)
        
        main_layout.addLayout(input_layout)
        
        # List of matching receipts
        main_layout.addWidget(QLabel("Receipts matching month/year:"))
        self.receipt_list = QListWidget()
        main_layout.addWidget(self.receipt_list)
        
        # Button to load receipts
        load_btn = QPushButton("Load Receipts")
        load_btn.clicked.connect(self.load_receipts)
        main_layout.addWidget(load_btn)
        
        # Export button
        export_btn = QPushButton("Export to Excel")
        export_btn.clicked.connect(self.export_to_excel)
        main_layout.addWidget(export_btn)
    
    def load_receipts(self):
        month = self.month_spinbox.value()
        year = self.year_spinbox.value()
        
        receipts = load_receipts_by_month_year(month, year)
        self.receipt_list.clear()
        self.receipts = receipts
        
        if not receipts:
            QMessageBox.information(self, "No Data", f"No receipts found for {month}/{year}")
            return
        
        for data in receipts:
            customer = data.get('customer', 'Unknown')
            date = data.get('Date', 'No date')
            self.receipt_list.addItem(f"{customer} - {date}")
        
        # Also copy the loaded receipts to the clipboard in Excel-ready TSV
        try:
            self._copy_receipts_to_clipboard(receipts)
        except Exception:
            # Non-fatal: best-effort copy
            pass

        QMessageBox.information(self, "Loaded", f"Found {len(receipts)} receipts for {month}/{year} (copied to clipboard)")

    def _parse_amount(self, raw):
        """Parse a payment value into a plain ASCII float string usable by Excel.

        Returns string like '1234.56' or empty string on failure.
        """
        if raw is None:
            return ""
        # If already numeric
        try:
            if isinstance(raw, (int, float)):
                return str(float(raw))
        except Exception:
            pass
        s = str(raw).strip()
        if not s:
            return ""
        # Remove currency symbols and spaces
        for ch in ("₪", "$", "EUR", "USD", "NIS", "ILS"):
            s = s.replace(ch, "")
        s = s.replace('\u200f', '').replace('\u200e', '')  # remove bidi marks
        s = s.replace(' ', '')

        # Normalize separators: if both '.' and ',' exist, figure which is decimal
        if '.' in s and ',' in s:
            # if last comma occurs after last dot, comma likely decimal sep
            if s.rfind(',') > s.rfind('.'):
                s = s.replace('.', '')
                s = s.replace(',', '.')
            else:
                s = s.replace(',', '')
        elif ',' in s and '.' not in s:
            # If comma present, assume it's a decimal separator if there are two digits after it
            if len(s.split(',')[-1]) in (1, 2):
                s = s.replace(',', '.')
            else:
                s = s.replace(',', '')

        # Remove any characters that are not digit, dot or minus
        cleaned = ''.join(ch for ch in s if (ch.isdigit() or ch in '.-'))
        if not cleaned or cleaned in ('.', '-', '-.'):
            return ""
        try:
            return str(float(cleaned))
        except Exception:
            return ""

    def _copy_receipts_to_clipboard(self, receipts):
        """Copy receipts to the clipboard in Excel-ready TSV format.

        Column mapping per user request:
          A: fixed string 'הכנסה'
          B: receipt Date
          C: amount as float number
          D: customer name
          E: fixed string 'המחאה'
          F: receipt number (CheckNumber or recipeNum)
          G: bank account
        """
        rows = []
        for r in receipts:
            a = 'הכנסה'
            b = r.get('Date', '')
            c = self._parse_amount(r.get('payment', ''))
            d = r.get('customer', '')
            e = 'המחאה'
            # F: receipt number (prefer recipeNum/invoice_no)
            f = r.get('recipeNum') or r.get('invoice_no') or ''
            # G: bank number (e.g., bank branch or bank identifier)
            g = r.get('BankNumber', '')
            # H: bank account number
            h = r.get('bankAccount', '')
            # I: check number (explicit CheckNumber field)
            i = r.get('CheckNumber', '')
            rows.append('\t'.join([a, b, c, d, e, f, g, h, i]))

        text = '\r\n'.join(rows)
        # Put into clipboard
        app = QApplication.instance()
        if app is None:
            # Should not happen in normal GUI usage, but guard anyway
            app = QApplication([])
        clipboard = app.clipboard()
        clipboard.setText(text)
    
    def export_to_excel(self):
        if not hasattr(self, 'receipts') or not self.receipts:
            QMessageBox.warning(self, "Error", "Load receipts first")
            return
        
        output_file = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx)")[0]
        if not output_file:
            return
        
        try:
            import openpyxl
        except ImportError:
            QMessageBox.critical(self, "Error", "openpyxl is required. Install with: pip install openpyxl")
            return
        
        try:
            # Create workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            
            # Write header
            headers = ["Customer", "Description", "Invoice No", "Payment", "MAM", "Date", "Bank Account", "Bank", "Check #"]
            for col, header in enumerate(headers, 1):
                ws.cell(row=1, column=col, value=header)
            
            # Write data
            for row_idx, receipt in enumerate(self.receipts, 2):
                ws.cell(row=row_idx, column=1, value=receipt.get('customer', ''))
                ws.cell(row=row_idx, column=2, value=receipt.get('discription', ''))
                ws.cell(row=row_idx, column=3, value=receipt.get('recipeNum', ''))
                ws.cell(row=row_idx, column=4, value=receipt.get('payment', ''))
                ws.cell(row=row_idx, column=5, value=receipt.get('mamVal', ''))
                ws.cell(row=row_idx, column=6, value=receipt.get('Date', ''))
                ws.cell(row=row_idx, column=7, value=receipt.get('bankAccount', ''))
                ws.cell(row=row_idx, column=8, value=receipt.get('BankNumber', ''))
                ws.cell(row=row_idx, column=9, value=receipt.get('CheckNumber', ''))
            
            # Adjust column widths
            for col in range(1, 10):
                ws.column_dimensions[chr(64 + col)].width = 15
            
            wb.save(output_file)
            QMessageBox.information(self, "Success", f"Exported {len(self.receipts)} receipts to {output_file}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {e}")
