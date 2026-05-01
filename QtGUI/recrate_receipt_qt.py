import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMessageBox, QFileDialog, QApplication,
                             QTableWidget, QTableWidgetItem)
import sys
from datetime import datetime
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class DateTableWidgetItem(QTableWidgetItem):
    """Custom QTableWidgetItem that sorts by date value"""
    def __init__(self, text, date_value):
        super().__init__(text)
        self.date_value = date_value
    
    def __lt__(self, other):
        if hasattr(other, 'date_value'):
            if self.date_value and other.date_value:
                return self.date_value < other.date_value
            elif self.date_value:
                return False  # Valid dates come before invalid ones
            elif other.date_value:
                return True   # Invalid dates come after valid ones
        return super().__lt__(other)

# Add parent directory to path for imports when running standalone
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.receiptGen import create_receipt
from config.paths import DB_DIR, get_mode_label, USE_SIMULATION

HISTORY_DIR = os.path.join(DB_DIR, "History")
CUSTOMERS_FILE = os.path.join(DB_DIR, "customers_data.json")


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


def normalize_history_entry(raw):
    if not isinstance(raw, dict):
        return None  # Invalid structure
    
    # Expect only proper data and info sections
    if "data" in raw and isinstance(raw["data"], dict) and "info" in raw:
        info = raw.get("info", {})
        return {"data": raw["data"], "info": info if isinstance(info, dict) else {}}
    
    return None  # Invalid structure


def load_history():
    entries = []
    if os.path.exists(HISTORY_DIR):
        for filename in sorted(os.listdir(HISTORY_DIR), reverse=True):
            if not filename.endswith('.json'):
                continue
            fpath = os.path.join(HISTORY_DIR, filename)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                normalized = normalize_history_entry(raw)
                if normalized is None:
                    print(f"CORRUPTED FILE: {filename} - Invalid JSON structure")
                    continue  # Skip corrupted files
                entries.append((filename[:-5], normalized))
            except Exception as e:
                print(f"CORRUPTED FILE: {filename} - {e}")
                continue  # Skip corrupted files

    return entries


class RecreateReceiptApp_Qt(QWidget):
    def __init__(self):
        super().__init__()
        self.history = {}
        self.current_receipt = None
        
        # Setup Hebrew-capable font
        available_fonts = ["Alef", "Segoe UI", "Tahoma"]
        self.hebrew_font = QFont()
        for font_name in available_fonts:
            self.hebrew_font.setFamily(font_name)
            if self.hebrew_font.exactMatch():
                break
        self.hebrew_font.setPointSize(10)
        
        self.init_ui()
        self.reload_history()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Reload button
        reload_btn = QPushButton("Reload History")
        reload_btn.clicked.connect(self.reload_history)
        main_layout.addWidget(reload_btn)

        # (Table header supports sorting by clicking column headers)

        # History table (Key | Customer | Date)
        main_layout.addWidget(QLabel("History:"))
        self.history_table = QTableWidget(0, 3)
        self.history_table.setHorizontalHeaderLabels(["Receipt number", "Customer", "Date"])
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setSelectionBehavior(self.history_table.SelectRows)
        self.history_table.setEditTriggers(self.history_table.NoEditTriggers)
        self.history_table.setColumnWidth(0, 220)
        self.history_table.setColumnWidth(1, 350)  # Increased customer column width
        self.history_table.setColumnWidth(2, 140)
        self.history_table.itemSelectionChanged.connect(self.on_receipt_selected)
        main_layout.addWidget(self.history_table)
        # enable clickable header sorting and default to newest (Key desc)
        self.history_table.setSortingEnabled(True)
        
        # Details table (Field | Value)
        main_layout.addWidget(QLabel("Receipt Details:"))
        self.detail_keys = []  # Will be populated dynamically when data is loaded
        self.details_table = QTableWidget(0, 2)  # Start with 0 rows, will be resized
        self.details_table.setHorizontalHeaderLabels(["Field", "Value"])
        self.details_table.verticalHeader().setVisible(False)
        self.details_table.setEditTriggers(self.details_table.NoEditTriggers)
        self.details_table.setSelectionBehavior(self.details_table.SelectRows)
        self.details_table.setColumnWidth(0, 200)  # Increased field name width
        self.details_table.setColumnWidth(1, 480)  # Adjusted value width
        # Field population will be done dynamically when receipt is selected
        main_layout.addWidget(self.details_table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        save_btn = QPushButton("Save PDF")
        save_btn.clicked.connect(self.save_pdf)
        action_layout.addWidget(save_btn)
        
        main_layout.addLayout(action_layout)
    
    def reload_history(self):
        self.history = {}
        # clear table completely
        self.history_table.setRowCount(0)
        self.history_table.clearContents()
        
        history = load_history()
        print(f"Loading {len(history)} history entries")
        
        for name, entry in history:
            # store normalized history entry under the key
            self.history[name] = entry
            data = entry['data']  # All files have proper structure
            
            # Extract receipt data
            receipt_num = data.get('recipeNum', name)
            customer_name = data.get('customer', '')
            receipt_date = data.get('Date', '')
            
            # Only add row if we have at least a receipt number
            if receipt_num:
                # Parse date for proper sorting
                parsed_date = parse_date_dd_mm_yyyy(receipt_date)
                
                # Get current row count and insert new row
                row = self.history_table.rowCount()
                self.history_table.insertRow(row)
                
                # Create table items
                receipt_item = QTableWidgetItem(str(receipt_num))
                receipt_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                receipt_item.setData(Qt.UserRole, name)  # Store filename for retrieval
                
                customer_item = QTableWidgetItem(str(customer_name))
                customer_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                customer_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                
                date_item = DateTableWidgetItem(str(receipt_date), parsed_date)
                date_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                date_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                
                # Set items in table
                self.history_table.setItem(row, 0, receipt_item)   # Receipt number
                self.history_table.setItem(row, 1, customer_item)  # Customer name
                self.history_table.setItem(row, 2, date_item)       # Receipt date
                
                print(f"  Row {row} set: {receipt_item.text()} | {customer_item.text()} | {date_item.text()}")
        
        print(f"Table now has {self.history_table.rowCount()} rows")
        
        # Enable sorting by date column descending
        #self.history_table.sortItems(2, Qt.DescendingOrder)
    
    def on_receipt_selected(self):
        # determine selected row in table
        selected = self.history_table.selectedItems()
        if selected:
            row = selected[0].row()
            key_item = self.history_table.item(row, 0)
            key = key_item.data(Qt.UserRole) if key_item is not None else None
            if not key and key_item is not None:
                key = key_item.text()
            self.current_receipt = key
            entry = self.history.get(key, {})
            data = entry['data']  # All files have proper structure
            
            # Dynamically get all fields from data section, but only include non-empty fields
            self.detail_keys = [k for k in data.keys() if data.get(k) and str(data.get(k)).strip()]
            # Resize table to match number of non-empty fields
            self.details_table.setRowCount(len(self.detail_keys))
            
            # Populate only non-empty fields dynamically
            for r, k in enumerate(self.detail_keys):
                # Field name
                key_item = QTableWidgetItem(k)
                key_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                key_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                
                # Field value
                val = data.get(k, "")
                val_item = QTableWidgetItem(str(val))
                val_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                val_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                
                self.details_table.setItem(r, 0, key_item)
                self.details_table.setItem(r, 1, val_item)

    
    
    def save_pdf(self):
        if not self.current_receipt:
            QMessageBox.warning(self, "Error", "Select a receipt first")
            return
        
        data = self.history.get(self.current_receipt, {})
        output_file = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")[0]
        
        if output_file:
            try:
                create_receipt(data.get('data', data), output_file)
                QMessageBox.information(self, "Success", f"PDF saved to {output_file}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create PDF: {e}")


if __name__ == '__main__':
    # Allow this module to run standalone for testing the Recreate UI
    app = QApplication(sys.argv)
    w = RecreateReceiptApp_Qt()
    mode_text = f"[{get_mode_label()}]" if USE_SIMULATION else f"[{get_mode_label()}]"
    w.setWindowTitle(f'Recreate Receipt {mode_text}')
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec_())
