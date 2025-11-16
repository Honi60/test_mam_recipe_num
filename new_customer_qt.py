import os
import json
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
                             QPushButton, QLineEdit, QLabel, QMessageBox, QInputDialog, 
                             QFileDialog, QFrame, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from bidi.algorithm import get_display

DB_DIR = r"E:\MyGoogleDrive\Rentals\RentalsDB"
CUSTOMERS_FILE = os.path.join(DB_DIR, "customers_data.json")

SAMPLE_KEYS = [
    "recipeNum", "discription", "invoice_no", "customer", "payment", "mamVal",
    "bankAccount", "BankNumber", "CheckNumber", "Date", "SaveFolder",
    "bank_transfer_referance", "transfer_bankAccount"
]


def wrap_numbers_with_rlm(text: str) -> str:
    RLM = '\u200F'
    return re.sub(r'([0-9]+(?:[.,][0-9]+)*)', lambda m: f"{RLM}{m.group(1)}{RLM}", text)


class CustomerEditor_Qt(QWidget):
    def __init__(self):
        super().__init__()
        os.makedirs(DB_DIR, exist_ok=True)
        self.customers = {}
        self.current = None
        self.fields = {}
        
        # Setup Hebrew-capable font
        available_fonts = ["Alef", "Segoe UI", "Tahoma"]
        self.hebrew_font = QFont()
        for font_name in available_fonts:
            self.hebrew_font.setFamily(font_name)
            if self.hebrew_font.exactMatch():
                break
        self.hebrew_font.setPointSize(10)
        
        self.load_customers()
        self.init_ui()
    
    def load_customers(self):
        try:
            with open(CUSTOMERS_FILE, "r", encoding="utf-8") as f:
                self.customers = json.load(f)
        except Exception:
            self.customers = {}
    
    def backup_customers(self):
        try:
            if os.path.exists(CUSTOMERS_FILE):
                import shutil, datetime
                ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
                shutil.copy2(CUSTOMERS_FILE, f"{CUSTOMERS_FILE}.bak.{ts}")
        except Exception:
            pass
    
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Left panel: Customer list
        left_layout = QVBoxLayout()
        self.customer_list = QListWidget()
        self.customer_list.itemSelectionChanged.connect(self.on_customer_selected)
        left_layout.addWidget(QLabel("Customers:"))
        left_layout.addWidget(self.customer_list)
        
        # Buttons for list
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_customer)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_customer)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_customers)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(save_btn)
        left_layout.addLayout(btn_layout)
        
        # Right panel: Form fields
        right_layout = QVBoxLayout()
        
        # Scrollable form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QWidget()
        self.form_layout = QVBoxLayout(form_widget)
        
        for key in SAMPLE_KEYS:
            row_layout = QHBoxLayout()
            label = QLabel(f"{key}:")
            label.setMinimumWidth(150)
            entry = QLineEdit()
            entry.setFont(self.hebrew_font)
            entry.setAlignment(Qt.AlignRight)  # RTL
            entry.textChanged.connect(lambda: self.update_preview())
            
            if key == "SaveFolder":
                browse_btn = QPushButton("Browse")
                browse_btn.clicked.connect(lambda e=None, ent=entry: self.browse_folder(ent))
                row_layout.addWidget(label)
                row_layout.addWidget(entry)
                row_layout.addWidget(browse_btn)
            else:
                row_layout.addWidget(label)
                row_layout.addWidget(entry)
            
            self.form_layout.addLayout(row_layout)
            self.fields[key] = entry
        
        scroll.setWidget(form_widget)
        right_layout.addWidget(scroll)
        
        # Preview and update buttons
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(QLabel("Preview (visual order for printing):"))
        self.preview_label = QLabel("")
        self.preview_label.setAlignment(Qt.AlignRight)
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("border: 1px solid gray; padding: 5px; background-color: white;")
        self.preview_label.setMinimumHeight(60)
        preview_layout.addWidget(self.preview_label)
        
        action_layout = QHBoxLayout()
        update_btn = QPushButton("Update")
        update_btn.clicked.connect(self.update_customer)
        preview_btn = QPushButton("Update Preview")
        preview_btn.clicked.connect(self.update_preview)
        rename_btn = QPushButton("Rename Key")
        rename_btn.clicked.connect(self.rename_customer)
        action_layout.addWidget(update_btn)
        action_layout.addWidget(preview_btn)
        action_layout.addWidget(rename_btn)
        
        right_layout.addLayout(preview_layout)
        right_layout.addLayout(action_layout)
        
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)
        
        self.refresh_list()
    
    def browse_folder(self, entry):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Folder")
        if folder:
            entry.setText(folder)
    
    def refresh_list(self):
        self.customer_list.clear()
        for name in sorted(self.customers.keys()):
            self.customer_list.addItem(name)
    
    def on_customer_selected(self):
        if self.customer_list.currentItem():
            name = self.customer_list.currentItem().text()
            self.current = name
            data = self.customers.get(name, {})
            for k in SAMPLE_KEYS:
                self.fields[k].setText(data.get(k, ""))
            self.update_preview()
    
    def add_customer(self):
        name, ok = QInputDialog.getText(self, "Add Customer", "Enter customer name/key:")
        if ok and name:
            if name in self.customers:
                QMessageBox.warning(self, "Error", "Customer already exists")
                return
            self.customers[name] = {k: "" for k in SAMPLE_KEYS}
            self.customers[name]["customer"] = name
            self.refresh_list()
            idx = list(sorted(self.customers.keys())).index(name)
            self.customer_list.setCurrentRow(idx)
    
    def delete_customer(self):
        if self.customer_list.currentItem():
            name = self.customer_list.currentItem().text()
            if QMessageBox.question(self, "Delete", f"Delete customer '{name}'?") == QMessageBox.Yes:
                del self.customers[name]
                self.refresh_list()
                for entry in self.fields.values():
                    entry.setText("")
                self.current = None
    
    def update_customer(self):
        if not self.current:
            QMessageBox.warning(self, "Error", "Select a customer first")
            return
        data = {k: self.fields[k].text() for k in SAMPLE_KEYS}
        self.customers[self.current] = data
        QMessageBox.information(self, "Success", f"Customer '{self.current}' updated")
        self.refresh_list()
        idx = list(sorted(self.customers.keys())).index(self.current)
        self.customer_list.setCurrentRow(idx)
    
    def rename_customer(self):
        if not self.current:
            QMessageBox.warning(self, "Error", "Select a customer first")
            return
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=self.current)
        if ok and new_name and new_name != self.current:
            if new_name in self.customers:
                QMessageBox.warning(self, "Error", "Name already exists")
                return
            self.customers[new_name] = self.customers.pop(self.current)
            if not self.customers[new_name].get('customer'):
                self.customers[new_name]['customer'] = new_name
            self.current = new_name
            self.refresh_list()
            idx = list(sorted(self.customers.keys())).index(new_name)
            self.customer_list.setCurrentRow(idx)
    
    def save_customers(self):
        if self.current is None:
            filled = any(self.fields[k].text().strip() for k in SAMPLE_KEYS)
            if filled:
                QMessageBox.warning(self, "Error", "Select a customer before saving")
                return
        try:
            self.backup_customers()
            with open(CUSTOMERS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.customers, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Success", "Customers saved")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")
    
    def update_preview(self):
        parts = []
        cust = self.fields['customer'].text().strip()
        desc = self.fields['discription'].text().strip()
        if cust:
            parts.append(cust)
        if desc:
            parts.append(desc)
        
        bank_ref = self.fields['bank_transfer_referance'].text().strip()
        transfer_acc = self.fields['transfer_bankAccount'].text().strip()
        if bank_ref:
            bank_line = f"מחשבון: {transfer_acc}  אסמכתא העברה: {bank_ref}"
            parts.append(bank_line)
        else:
            bank_parts = []
            if self.fields['payment'].text().strip():
                bank_parts.append(f"סכום: {self.fields['payment'].text().strip()}")
            if self.fields['bankAccount'].text().strip():
                bank_parts.append(f"חשבון: {self.fields['bankAccount'].text().strip()}")
            if self.fields['BankNumber'].text().strip():
                bank_parts.append(f"בנק: {self.fields['BankNumber'].text().strip()}")
            if self.fields['CheckNumber'].text().strip():
                bank_parts.append(f"צ'ק מס: {self.fields['CheckNumber'].text().strip()}")
            if bank_parts:
                parts.append('  '.join(bank_parts))
        
        combined = '\n'.join(parts)
        combined = wrap_numbers_with_rlm(combined)
        vis = get_display(combined)
        self.preview_label.setText(vis)
