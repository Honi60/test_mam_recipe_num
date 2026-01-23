import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QComboBox, QFileDialog, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from datetime import datetime
from receiptGen import create_receipt
from bidi.algorithm import get_display


class ReceiptGenGUI_Qt(QWidget):
    def __init__(self):
        super().__init__()
        self.DB_DIR = r"G:\My Drive\Rentals\RentalsDB"
        try:
            os.makedirs(self.DB_DIR, exist_ok=True)
        except Exception:
            pass
        
        self.data = {}
        self.entries = {}
        self.save_path = None
        self.customers = {}
        self.selected_customer = ""
        
        # Setup Hebrew-capable font
        available_fonts = ["Alef", "Segoe UI", "Arial"]
        self.hebrew_font = QFont()
        for font_name in available_fonts:
            self.hebrew_font.setFamily(font_name)
            if self.hebrew_font.exactMatch():
                break
        self.hebrew_font.setPointSize(10)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Load customer file button
        load_btn = QPushButton("Load Customer Data File")
        load_btn.clicked.connect(self.load_customer_file)
        layout.addWidget(load_btn)
        
        # Customer dropdown
        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Select Customer:"))
        self.customer_dropdown = QComboBox()
        self.customer_dropdown.currentIndexChanged.connect(self.on_customer_selected)
        dropdown_layout.addWidget(self.customer_dropdown)
        dropdown_layout.addStretch()
        layout.addLayout(dropdown_layout)
        
        # Form frame for dynamic fields
        self.form_frame = QFrame()
        form_layout = QVBoxLayout(self.form_frame)
        layout.addWidget(self.form_frame)
        
        # Save location button
        self.save_btn = QPushButton("Choose Save Location")
        self.save_btn.clicked.connect(self.choose_save_location)
        layout.addWidget(self.save_btn)
        
        # Generate receipt button
        self.gen_btn = QPushButton("Generate and Save")
        self.gen_btn.clicked.connect(self.generate_receipt)
        layout.addWidget(self.gen_btn)
        
        # Open folder button
        self.open_folder_btn = QPushButton("Open Receipt Folder")
        self.open_folder_btn.clicked.connect(self.open_receipt_folder)
        self.open_folder_btn.setEnabled(False)
        layout.addWidget(self.open_folder_btn)
        
        layout.addStretch()
    
    def load_customer_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Customer Data File", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle both dict and list structures
                if isinstance(data, dict):
                    self.customers = data
                elif isinstance(data, list):
                    # Convert list to dict with customer names as keys
                    self.customers = {}
                    for item in data:
                        if isinstance(item, dict) and 'customer' in item:
                            customer_name = item['customer']
                            self.customers[customer_name] = item
                        elif isinstance(item, str):
                            self.customers[item] = {"customer": item}
                else:
                    QMessageBox.critical(self, "Error", "Invalid customer data format")
                    return
                
                self.customer_dropdown.clear()
                self.customer_dropdown.addItems(sorted(self.customers.keys()))
                QMessageBox.information(self, "Success", f"Loaded {len(self.customers)} customers")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
    
    def on_customer_selected(self, index):
        if index >= 0 and index < self.customer_dropdown.count():
            self.selected_customer = self.customer_dropdown.currentText()
            if self.selected_customer in self.customers:
                customer_data = self.customers[self.selected_customer]
                # Ensure we have a dict, not a string
                if isinstance(customer_data, dict):
                    self.data = customer_data
                else:
                    QMessageBox.warning(self, "Error", f"Invalid data for customer {self.selected_customer}")
                    self.data = {}
                    return
                self.populate_form()
    
    def populate_form(self):
        # Clear previous form
        while self.form_frame.layout().count():
            self.form_frame.layout().takeAt(0).widget().deleteLater()
        
        form_layout = self.form_frame.layout()
        self.entries = {}
        
        for key in sorted(self.data.keys()):
            h_layout = QHBoxLayout()
            label = QLabel(f"{key}:")
            label.setMinimumWidth(120)
            entry = QLineEdit()
            entry.setText(str(self.data.get(key, "")))
            entry.setFont(self.hebrew_font)
            entry.setAlignment(Qt.AlignRight)  # RTL alignment
            h_layout.addWidget(label)
            h_layout.addWidget(entry)
            form_layout.addLayout(h_layout)
            self.entries[key] = entry
    
    def choose_save_location(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Location")
        if folder:
            self.save_path = folder
            QMessageBox.information(self, "Save Location", f"Set to: {self.save_path}")
    
    def generate_receipt(self):
        if not self.save_path:
            QMessageBox.warning(self, "Error", "Please choose a save location first")
            return
        
        if not self.selected_customer:
            QMessageBox.warning(self, "Error", "Please select a customer")
            return
        
        # Collect data from form
        for key, entry in self.entries.items():
            self.data[key] = entry.text()
        
        try:
            output_path = os.path.join(self.save_path, f"{self.selected_customer}.pdf")
            create_receipt(self.data, output_path)
            self.open_folder_btn.setEnabled(True)
            QMessageBox.information(self, "Success", f"Receipt saved to:\n{output_path}")
            # Save history record as JSON so the Recreate tab can load it
            try:
                history_dir = os.path.join(self.DB_DIR, "History")
                os.makedirs(history_dir, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%dT%H%M%S")
                hist_name = f"{self.selected_customer}_{ts}.json"
                hist_path = os.path.join(history_dir, hist_name)
                with open(hist_path, "w", encoding="utf-8") as hf:
                    json.dump(self.data, hf, ensure_ascii=False, indent=2)
            except Exception:
                # Ignore history save errors but don't block the user
                pass
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate receipt: {e}")
    
    def open_receipt_folder(self):
        import subprocess
        if self.save_path:
            win_path = os.path.normpath(os.path.abspath(self.save_path))
            try:
                subprocess.Popen(f'explorer /select,"{win_path}"')
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open folder: {e}")
