import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMessageBox, QFileDialog, QApplication,
                             QTableWidget, QTableWidgetItem)
import sys
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from receiptGen import create_receipt

DB_DIR = r"G:\My Drive\Rentals\RentalsDB"
HISTORY_DIR = r"G:\My Drive\Rentals\RentalsDB\History"
HISTORY_FILE = os.path.join(DB_DIR, "history.json")
CUSTOMERS_FILE = os.path.join(DB_DIR, "customers_data.json")


def load_history():
    """Load history entries from either a single history.json (legacy TK format)
    or per-file JSONs in the History folder. Returns a list of (key, data_dict).
    The returned data_dict is the actual receipt data (has fields like 'customer','Date').
    """
    entries = []
    # 1) Try legacy single history file (history.json)
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                h = json.load(f)
            if isinstance(h, dict):
                for key in sorted(h.keys(), reverse=True):
                    entry = h.get(key)
                    # entry may be {customer: data} or directly data
                    if isinstance(entry, dict) and len(entry) == 1:
                        # {customer: data}
                        inner = list(entry.values())[0]
                        if isinstance(inner, dict):
                            entries.append((key, inner))
                        else:
                            entries.append((key, {}))
                    elif isinstance(entry, dict):
                        # assume entry is data dict
                        entries.append((key, entry))
    except Exception:
        pass

    # 2) Load per-file JSONs from History directory
    if os.path.exists(HISTORY_DIR):
        for filename in sorted(os.listdir(HISTORY_DIR), reverse=True):
            if not filename.endswith('.json'):
                continue
            fpath = os.path.join(HISTORY_DIR, filename)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # If file contains a mapping like {customer: data}, extract inner data
                if isinstance(data, dict) and len(data) == 1:
                    inner = list(data.values())[0]
                    if isinstance(inner, dict):
                        entries.append((filename[:-5], inner))
                        continue
                # If file is a plain data dict (we save that from generate), use it
                if isinstance(data, dict):
                    entries.append((filename[:-5], data))
            except Exception:
                pass

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
        self.history_table.setHorizontalHeaderLabels(["Key", "Customer", "Date"])
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setSelectionBehavior(self.history_table.SelectRows)
        self.history_table.setEditTriggers(self.history_table.NoEditTriggers)
        self.history_table.setColumnWidth(0, 220)
        self.history_table.setColumnWidth(1, 260)
        self.history_table.setColumnWidth(2, 140)
        self.history_table.itemSelectionChanged.connect(self.on_receipt_selected)
        main_layout.addWidget(self.history_table)
        # enable clickable header sorting and default to newest (Key desc)
        self.history_table.setSortingEnabled(True)
        
        # Details table (Field | Value)
        main_layout.addWidget(QLabel("Receipt Details:"))
        self.detail_keys = ["customer", "discription", "invoice_no", "payment", "mamVal", "Date"]
        self.details_table = QTableWidget(len(self.detail_keys), 2)
        self.details_table.setHorizontalHeaderLabels(["Field", "Value"])
        self.details_table.verticalHeader().setVisible(False)
        self.details_table.setEditTriggers(self.details_table.NoEditTriggers)
        self.details_table.setSelectionBehavior(self.details_table.SelectRows)
        self.details_table.setColumnWidth(0, 160)
        self.details_table.setColumnWidth(1, 520)
        # populate field names and set value alignment
        for r, key in enumerate(self.detail_keys):
            key_item = QTableWidgetItem(key)
            key_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            # value cell placeholder
            val_item = QTableWidgetItem("")
            val_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            # align value to right for RTL clarity
            val_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.details_table.setItem(r, 0, key_item)
            self.details_table.setItem(r, 1, val_item)
        main_layout.addWidget(self.details_table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        save_btn = QPushButton("Save PDF")
        save_btn.clicked.connect(self.save_pdf)
        action_layout.addWidget(save_btn)
        
        main_layout.addLayout(action_layout)
    
    def reload_history(self):
        self.history = {}
        # clear table
        self.history_table.setRowCount(0)
        history = load_history()
        for name, data in history:
            # store normalized data under the key
            self.history[name] = data
            cust = data.get('customer', '') if isinstance(data, dict) else ''
            date = data.get('Date', '') if isinstance(data, dict) else ''
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            key_item = QTableWidgetItem(name)
            key_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            key_item.setData(Qt.UserRole, name)
            cust_item = QTableWidgetItem(str(cust))
            cust_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            cust_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            date_item = QTableWidgetItem(str(date))
            date_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            date_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.history_table.setItem(row, 0, key_item)
            self.history_table.setItem(row, 1, cust_item)
            self.history_table.setItem(row, 2, date_item)
        # default sort by Key (column 0) descending so newest receipts appear on top
        self.history_table.sortItems(0, Qt.DescendingOrder)
    
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
            data = self.history.get(key, {})
            # populate the details table values
            for r, k in enumerate(self.detail_keys):
                val = data.get(k, "") if isinstance(data, dict) else ""
                val_item = QTableWidgetItem(str(val))
                val_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                val_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.details_table.setItem(r, 1, val_item)

    
    
    def save_pdf(self):
        if not self.current_receipt:
            QMessageBox.warning(self, "Error", "Select a receipt first")
            return
        
        data = self.history.get(self.current_receipt, {})
        output_file = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")[0]
        
        if output_file:
            try:
                create_receipt(data, output_file)
                QMessageBox.information(self, "Success", f"PDF saved to {output_file}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create PDF: {e}")


if __name__ == '__main__':
    # Allow this module to run standalone for testing the Recreate UI
    app = QApplication(sys.argv)
    w = RecreateReceiptApp_Qt()
    w.setWindowTitle('Recreate Receipt - Standalone Test')
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec_())
