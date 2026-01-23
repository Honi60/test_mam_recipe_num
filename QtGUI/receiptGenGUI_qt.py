import os
import sys
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QComboBox, QFileDialog, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from datetime import datetime
# Add parent directory to path for imports when running standalone
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.paths import DB_DIR, CUSTOMERS_FILE
# When run as a script (python QtGUI\receiptGenGUI_qt.py) the package root
# may not be on sys.path. Try importing normally and fall back to adding the
# parent directory to sys.path so sibling packages like `logic` can be found.
try:
    from logic.receiptGen import create_receipt
except ModuleNotFoundError:
    parent = os.path.dirname(os.path.dirname(__file__))
    if parent not in sys.path:
        sys.path.insert(0, parent)
    from logic.receiptGen import create_receipt
from bidi.algorithm import get_display


class ReceiptGenGUI_Qt(QWidget):
    def __init__(self):
        super().__init__()
        try:
            os.makedirs(DB_DIR, exist_ok=True)
        except Exception:
            pass
        
        self.data = {}
        self.entries = {}
        self.save_path = None
        self.customer_file_path = None
        self.last_saved_file = None
        # Load preferences (like last customer file dir) if present
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
        customer_file = os.path.join(DB_DIR, CUSTOMERS_FILE)
        if os.path.exists(customer_file):
            self.read_customers_data(customer_file, popup=False)
    
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
        # Display for currently selected save path (read-only)
        save_layout = QHBoxLayout()
        save_layout.addWidget(self.save_btn)
        self.save_path_display = QLineEdit()
        self.save_path_display.setReadOnly(True)
        self.save_path_display.setPlaceholderText("No save location selected")
        self.save_path_display.setMinimumWidth(300)
        save_layout.addWidget(self.save_path_display)
        layout.addLayout(save_layout)
        
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
        initial = DB_DIR
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Customer Data File", initial, "JSON Files (*.json)")
        if file_path:
            self.read_customers_data(file_path)

    def read_customers_data(self, file_path, popup=True):
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
            # Remember where the user opened the customer data file
            self.customer_file_path = file_path
            if popup:
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
        # Clear previous form (handle widgets and nested layouts safely)
        def clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item is None:
                    continue
                w = item.widget()
                if w is not None:
                    w.deleteLater()
                else:
                    sub_layout = item.layout()
                    if sub_layout is not None:
                        clear_layout(sub_layout)
        form_layout = self.form_frame.layout()
        if form_layout is None:
            form_layout = QVBoxLayout(self.form_frame)
        clear_layout(form_layout)

        # If customer data contains a save/path-like key, use it as the default save location
        def _extract_save_path_from_data(data):
            if not isinstance(data, dict):
                return None
            for key, val in data.items():
                try:
                    klow = str(key).lower()
                except Exception:
                    continue
                if any(tok in klow for tok in ("save", "path", "folder", "output")):
                    if isinstance(val, str) and val:
                        # If value looks like a filename, take its directory
                        p = os.path.expanduser(val)
                        if os.path.splitext(p)[1].lower() == '.pdf':
                            return os.path.normpath(os.path.dirname(p))
                        return os.path.normpath(p)
            return None

        self.entries = {}
        # Apply customer-provided save path (if present)
        cust_save = _extract_save_path_from_data(self.data)
        if cust_save:
            self.save_path = cust_save
            try:
                self.save_path_display.setText(self.save_path)
            except Exception:
                pass
            self.open_folder_btn.setEnabled(True)
        
        # Attempt to pre-fill recipeNum from the shared receipt_number.txt if available
        recipe_num_path = os.path.join(DB_DIR, "receipt_number.txt")
        try:
            with open(recipe_num_path, "r", encoding="utf-8") as f:
                next_num = f.read().strip()
        except Exception:
            next_num = None

        for key in sorted(self.data.keys()):
            # Skip internal or UI-managed fields (e.g., save folder/path) so we don't
            # display duplicate save-path inputs if the customer data contains such keys.
            klow = str(key).lower()
            if any(tok in klow for tok in ("save", "path", "folder", "output")):
                continue
            h_layout = QHBoxLayout()
            label = QLabel(f"{key}:")
            label.setMinimumWidth(120)
            entry = QLineEdit()
            # If this field is recipeNum, prefer the customer's own value unless it's empty/zero
            if key == "recipeNum":
                cust_rn = str(self.data.get("recipeNum", "")).strip()
                entry.setText(str(next_num))
            else:
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
            # Update visible path in the GUI so users see their choice immediately
            try:
                self.save_path_display.setText(self.save_path)
            except Exception:
                # If saving display update fails, still proceed but notify the user
                pass
            # Enable the "Open Receipt Folder" button so user can jump to the folder
            self.open_folder_btn.setEnabled(True)
            QMessageBox.information(self, "Save Location", f"Set to: {self.save_path}")
    
    def generate_receipt(self):
        if not self.save_path:
            QMessageBox.warning(self, "Error", "Please choose a save location first")
            return
        
        if not self.selected_customer:
            QMessageBox.warning(self, "Error", "Please select a customer")
            return
        
        # Check for "?" in form data
        fields_with_question_mark = []
        for key, entry in self.entries.items():
            if "?" in entry.text():
                fields_with_question_mark.append(key)
        
        if fields_with_question_mark:
            fields_str = ", ".join(fields_with_question_mark)
            QMessageBox.warning(self, "Invalid Data", 
                              f"The following fields contain '?':\n{fields_str}\n\nPlease fix these fields before generating the receipt.")
            return
        
        # Collect data from form
        for key, entry in self.entries.items():
            self.data[key] = entry.text()

        # The receipt number must come only from the shared `receipt_number.txt`.
        # Read it and validate it; do not accept or use any number from the
        # customer JSON or GUI fields as the authoritative number.
        recipe_num_path = os.path.join(DB_DIR, "receipt_number.txt")
        try:
            with open(recipe_num_path, "r", encoding="utf-8") as f:
                v = f.read().strip()
        except FileNotFoundError:
            QMessageBox.warning(self, "Missing Receipt Number",
                                "No receipt number found: 'receipt_number.txt' is missing. Please create or restore it with the next number to use and try again.")
            return
        except Exception:
            QMessageBox.warning(self, "Missing Receipt Number",
                                "Unable to read 'receipt_number.txt'. Please ensure it is readable and contains the next numeric receipt number, then try again.")
            return

        if not v or not str(v).strip().isdigit():
            QMessageBox.warning(self, "Missing Receipt Number",
                                "Invalid receipt number in 'receipt_number.txt'. Please ensure it contains a valid numeric next number and try again.")
            return

        # At this point `v` is the next number to assign to this receipt.
        try:
            current_num = int(str(v).strip())
        except Exception:
            QMessageBox.warning(self, "Invalid Receipt Number",
                                "Invalid numeric value in 'receipt_number.txt'. Please fix it and try again.")
            return
        # Format the number used for this receipt (zero-padded)
        assigned_num_str = f"{current_num:05d}"
        # Reflect assigned number in our working data (but do not treat this
        # as an authoritative copy for future operations — only the shared
        # file is authoritative).
        self.data["recipeNum"] = assigned_num_str

        # Helpers for filename building
        def _safe_filename_part(s: str) -> str:
            import re
            if not s:
                return ""
            s = s.strip()
            s = re.sub(r"[\\/:*?\"<>|]+", "", s)
            s = re.sub(r"\s+", "_", s)
            return s

        # Format date for filename (try dd/mm/YYYY, dd/mm/YY, ISO)
        date_str = self.data.get("Date", "")
        date_part = ""
        if date_str:
            from datetime import datetime
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%Y/%m/%d"):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    date_part = dt.strftime("%Y%m%d")
                    break
                except Exception:
                    continue
            if not date_part:
                date_part = _safe_filename_part(date_str)

        customer_part = _safe_filename_part(self.selected_customer)
        recipe_part = _safe_filename_part(str(assigned_num_str))
        parts = [p for p in (customer_part, recipe_part, date_part) if p]
        filename = "_".join(parts) + ".pdf" if parts else f"{self.selected_customer}.pdf"

        output_path = os.path.join(self.save_path, filename)
        try:
            # call create_receipt (can be monkeypatched in tests)
            create_receipt(self.data, output_path)
            
            # Record the exact saved file so we can open and select it later
            self.last_saved_file = output_path
            self.open_folder_btn.setEnabled(True)
            # Show exact saved file in the path display for clarity
            try:
                self.save_path_display.setText(output_path)
            except Exception:
                pass
            # Save history record as JSON so the Recreate tab can load it
            try:
                history_dir = os.path.join(DB_DIR, "History")
                os.makedirs(history_dir, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%dT%H%M%S")
                hist_name = f"{self.selected_customer}_{ts}.json"
                hist_path = os.path.join(history_dir, hist_name)
                with open(hist_path, "w", encoding="utf-8") as hf:
                    json.dump(self.data, hf, ensure_ascii=False, indent=2)
            except Exception:
                # Ignore history save errors but don't block the user
                pass
            # We use the number read earlier as the assigned number for the
            # receipt (assigned_num_str). After successfully creating the
            # receipt, we must update `receipt_number.txt` to the next number
            # = current_num + 1. This write must be atomic and must write
            # exactly previous+1; if it fails we abort and do not update the
            # customer file so the authoritative sequence is not left inconsistent.
            new_num = None
            try:
                # create_receipt already ran successfully at this point; compute next
                new_num = int(current_num) + 1
                # Atomic write of next number
                import tempfile
                rpath = os.path.join(DB_DIR, "receipt_number.txt")
                d = os.path.dirname(rpath) or '.'
                fd, tmp_r = tempfile.mkstemp(prefix='.tmp', dir=d, text=True)
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as tf:
                        tf.write(f"{new_num:05d}")
                        tf.flush()
                        try:
                            os.fsync(tf.fileno())
                        except Exception:
                            pass
                    os.replace(tmp_r, rpath)
                except Exception:
                    # Clean up temp file on failure
                    try:
                        if os.path.exists(tmp_r):
                            os.remove(tmp_r)
                    except Exception:
                        pass
                    raise
            except Exception:
                QMessageBox.critical(self, "Critical Error",
                                     "Failed to update 'receipt_number.txt' to the next number. Receipt generation aborted to avoid issuing untracked numbers. Please fix the file and try again.")
                # Note: We do not update customer file when the shared write fails
                # to avoid recording a number that is not safely persisted.
                return
            # Update the displayed recipeNum if present to show the next number
            if "recipeNum" in self.entries:
                try:
                    self.entries["recipeNum"].setText(f"{new_num:05d}")
                except Exception:
                    pass
            # Update the customer data file with the assigned number for this
            # receipt (assigned_num_str). Do not consult the GUI or customer
            # data for the number; it must match the authoritative value that
            # was just persisted to `receipt_number.txt` (previous+1 was written
            # and assigned was the previous value).
            try:
                update_data = {
                    'SaveFolder': os.path.normpath(self.save_path) if self.save_path else None,
                    'CheckNumber': self.entries['CheckNumber'].text()
                }
               
                update_data = {k: v for k, v in update_data.items() if v is not None}
                wrote = self._update_customer_file(self.customer_file_path, self.selected_customer, update_data)
                if not wrote:
                    try:
                        self._notify_nonmodal("Warning", "Failed to save customer data to disk. Changes may not have been persisted.")
                    except Exception:
                        pass
            except Exception:
                pass
            # All updates succeeded (or were ignored); now notify the user
            try:
                QMessageBox.information(self, "Success", f"Receipt saved to:\n{output_path}")
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate receipt: {e}")
    
    def open_receipt_folder(self):
        import subprocess
        # Prefer selecting the last saved file if known; otherwise open the save path
        if self.last_saved_file is None:
            QMessageBox.warning(self, "Warning", "No receipt file to open")
            return
        if os.path.exists(self.last_saved_file):
            try:
                subprocess.Popen(f'explorer /select,"{self.last_saved_file}"')
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open reciept: {e}")
        else:
            QMessageBox.warning(self, "Warning", "No receipt file or folder to open")  
            
    def _update_customer_file(self, file_path: str, customer_name: str, new: dict):
        """Update customer file with new fields while preserving all other fields.

        Args:
            file_path: str -- path to the customer data file
            customer_name: str -- the customer name/key to update
            new: dict -- dictionary of fields to update/add

        Returns:
            bool -- True if successful, False otherwise
        """
        try:
            # Read the customer file
            with open(file_path, 'r', encoding='utf-8') as cf:
                cust_data = json.load(cf)
        except Exception:
            return False

        try:
            # Find and update the customer record
            updated = False
            
            if isinstance(cust_data, dict):
                # Case 1: Mapping of customer_name -> customer_data
                if customer_name in cust_data and isinstance(cust_data[customer_name], dict):
                    cust_data[customer_name].update(new)
                    updated = True
                # Case 2: Single customer dict with 'customer' field
                elif cust_data.get('customer') == customer_name:
                    cust_data.update(new)
                    updated = True
            elif isinstance(cust_data, list):
                # Case 3: List of customer dicts
                for item in cust_data:
                    if isinstance(item, dict) and item.get('customer') == customer_name:
                        item.update(new)
                        updated = True
                        break

            if not updated:
                return False

            # Atomic write to disk
            try:
                import tempfile
                d = os.path.dirname(file_path) or '.'
                fd, tmp_path = tempfile.mkstemp(prefix='.tmp', dir=d, text=True)
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as tf:
                        json.dump(cust_data, tf, ensure_ascii=False, indent=2)
                        tf.flush()
                        try:
                            os.fsync(tf.fileno())
                        except Exception:
                            pass
                    os.replace(tmp_path, file_path)
                except Exception:
                    try:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    except Exception:
                        pass
                    raise
            except Exception:
                return False

            return True
        except Exception:
            return False

    def _notify_nonmodal(self, title: str, message: str, timeout_ms: int = 3000):
        """Show a brief non-modal notification to the user.

        The notification is a non-blocking QMessageBox that will be closed
        automatically after `timeout_ms` milliseconds. Designed to be resilient
        in headless/test environments (exceptions are caught and logged).
        """
        try:
            # In headless/offscreen test environments creating and showing
            # actual QMessageBox widgets can crash the Qt runtime (access
            # violations). If running with the offscreen platform, avoid
            # creating GUI widgets and fall back to logging so tests and
            # headless runs are safe.
            if os.environ.get('QT_QPA_PLATFORM', '').lower() == 'offscreen':
                return
            mbox = QMessageBox(self)
            mbox.setWindowTitle(title)
            mbox.setText(message)
            try:
                mbox.setIcon(QMessageBox.Warning)
            except Exception:
                # Some test harnesses or platforms may not support icons; ignore
                pass
            mbox.setStandardButtons(QMessageBox.Ok)
            # Make it non-modal and show it briefly
            try:
                mbox.setWindowModality(Qt.NonModal)
                mbox.show()
                QTimer.singleShot(timeout_ms, mbox.close)
            except Exception:
                # Fall back to a simple info call if direct show fails
                try:
                    QMessageBox.information(self, title, message)
                except Exception:
                    pass
        except Exception:
            pass


def main():
    """Run the Receipt UI as a standalone application."""
    # Ensure package imports work when running as a script from the QtGUI dir
    parent = os.path.dirname(os.path.dirname(__file__))
    if parent not in sys.path:
        sys.path.insert(0, parent)

    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    w = ReceiptGenGUI_Qt()
    w.setWindowTitle("Receipt Generator")
    w.show()
    app.exec_()


if __name__ == "__main__":
    main()
