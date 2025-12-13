import os
import sys
import json
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QComboBox, QFileDialog, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from datetime import datetime
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
        self.DB_DIR = r"E:\MyGoogleDrive\Rentals\RentalsDB"
        try:
            os.makedirs(self.DB_DIR, exist_ok=True)
        except Exception:
            pass
        
        self.data = {}
        self.entries = {}
        self.save_path = None
        self.customer_file_path = None
        self.prefs_file = os.path.join(self.DB_DIR, "prefs.json")
        self.prefs = {}
        self.last_saved_file = None
        # Load preferences (like last customer file dir) if present
        try:
            if os.path.exists(self.prefs_file):
                with open(self.prefs_file, "r", encoding="utf-8") as pf:
                    self.prefs = json.load(pf)
        except Exception:
            self.prefs = {}
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
        initial = self.prefs.get("last_customer_dir", self.DB_DIR)
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Customer Data File", initial, "JSON Files (*.json)")
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
                # Remember where the user opened the customer data file
                self.customer_file_path = file_path
                try:
                    self.prefs["last_customer_dir"] = os.path.dirname(file_path)
                    with open(self.prefs_file, "w", encoding="utf-8") as pf:
                        json.dump(self.prefs, pf, ensure_ascii=False, indent=2)
                except Exception:
                    pass
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
        recipe_num_path = os.path.join(self.DB_DIR, "receipt_number.txt")
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
                if (not cust_rn or cust_rn == '0') and next_num:
                    entry.setText(str(next_num))
                else:
                    entry.setText(cust_rn)
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
        
        # Collect data from form
        logger = logging.getLogger(__name__)
        for key, entry in self.entries.items():
            self.data[key] = entry.text()
            try:
                logger.debug("collected data recipeNum=%r", self.data.get('recipeNum'))
            except Exception:
                pass

        # The receipt number must come only from the shared `receipt_number.txt`.
        # Read it and validate it; do not accept or use any number from the
        # customer JSON or GUI fields as the authoritative number.
        recipe_num_path = os.path.join(self.DB_DIR, "receipt_number.txt")
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
            try:
                self.last_saved_file = output_path
            except Exception:
                self.last_saved_file = None
            self.open_folder_btn.setEnabled(True)
            # Show exact saved file in the path display for clarity
            try:
                self.save_path_display.setText(output_path)
            except Exception:
                pass
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
                rpath = os.path.join(self.DB_DIR, "receipt_number.txt")
                d = os.path.dirname(rpath) or '.'
                fd, tmp_r = tempfile.mkstemp(prefix='.tmp', dir=d, text=True)
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as tf:
                        tf.write(f"{new_num:05d}")
                        tf.flush()
                        try:
                            os.fsync(tf.fileno())
                        except Exception:
                            logger.debug("Could not fsync temp receipt_number file %s", tmp_r)
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
                logger = logging.getLogger(__name__)
                logger.exception("Failed to atomically update receipt_number.txt to next value")
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
                wrote = self._update_customer_file(new_num, assigned_num_str)
                if not wrote:
                    try:
                        self._notify_nonmodal("Warning", "Failed to save customer data to disk. Changes may not have been persisted.")
                    except Exception:
                        logger = logging.getLogger(__name__)
                        logger.exception("Failed to show non-modal notification after customer update failure")
            except Exception:
                logger = logging.getLogger(__name__)
                logger.exception("Unexpected error while updating customer file")
            # All updates succeeded (or were ignored); now notify the user
            try:
                QMessageBox.information(self, "Success", f"Receipt saved to:\n{output_path}")
            except Exception:
                # If message box fails (headless/testing), just print to stdout
                try:
                    logger.info("Receipt saved to: %s", output_path)
                except Exception:
                    pass
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate receipt: {e}")
    
    def open_receipt_folder(self):
        import subprocess
        # Prefer selecting the last saved file if known; otherwise open the save path
        target = None
        if getattr(self, 'last_saved_file', None) and os.path.exists(self.last_saved_file):
            target = self.last_saved_file
        elif self.save_path:
            if os.path.isfile(self.save_path):
                target = self.save_path
            else:
                target = os.path.normpath(os.path.abspath(self.save_path))

        if target:
            try:
                subprocess.Popen(f'explorer /select,"{target}"')
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open folder: {e}")
        else:
            QMessageBox.warning(self, "Warning", "No receipt file or folder to open")

    def _update_customer_file(self, new_num, recipe_num):
        """Update the original customer file with SaveFolder and recipeNum.

        Args:
            new_num: int or None -- the numeric incremented value (already incremented), or None
            recipe_num: str -- the recipe number string that was used to save the receipt
        """
        logger = logging.getLogger(__name__)
        if not self.customer_file_path or not self.selected_customer:
            logger.debug("No customer_file_path or selected_customer; skipping update")
            return False

        try:
            with open(self.customer_file_path, 'r', encoding='utf-8') as cf:
                cust_data = json.load(cf)
        except Exception:
            logger.exception("Failed to read customer file %s", self.customer_file_path)
            return False

        # Keep it simple: only update 'SaveFolder' and 'CheckNumber' from the
        # UI values (the user just set them in the form). Prefer values from
        # `self.data` (as displayed in the form) and `self.save_path`.
        try:
            # The customer record should reflect the "next" check number
            # that will be used for the following receipt (i.e. the incremented
            # value). This makes the customer's CheckNumber represent the next
            # expected number to be issued. If `new_num` is not provided, fall
            # back to the provided `recipe_num` (the assigned number) where
            # possible.
            formatted_check = None
            # Prefer the explicitly provided recipe_num (the assigned number)
            # when present since callers (like generate_receipt) pass the
            # assigned number and expect it to be recorded on the customer
            # entry. If recipe_num is not provided, fall back to new_num.
            if recipe_num is not None:
                s = str(recipe_num).strip()
                if s and s.isdigit():
                    formatted_check = f"{int(s):05d}"
                elif s:
                    formatted_check = s
            elif new_num is not None:
                try:
                    formatted_check = f"{int(new_num):05d}"
                except Exception:
                    formatted_check = str(new_num)

            updated = False
            # Helper to set values on a dict-like entry
            def _set_fields_on_entry(e):
                nonlocal updated
                if not isinstance(e, dict):
                    return
                logger.debug("_set_fields_on_entry called for customer=%r before=%r", e.get('customer'), e)
                # SaveFolder from the GUI's save_path if present
                try:
                    if self.save_path:
                        e['SaveFolder'] = os.path.normpath(self.save_path)
                except Exception:
                    pass
                # Determine assigned (the exact number used to create the
                # receipt) and the next-increment (the number that will be
                # used for subsequent receipts). Prefer recipe_num for the
                # assigned value when provided; use new_num for the next.
                assigned_str = None
                next_str = None
                if recipe_num is not None:
                    s = str(recipe_num).strip()
                    if s and s.isdigit():
                        assigned_str = f"{int(s):05d}"
                    elif s:
                        assigned_str = s
                if new_num is not None:
                    try:
                        next_str = f"{int(new_num):05d}"
                    except Exception:
                        next_str = str(new_num)

                # Persist both fields for clarity: CheckNumber records the
                # assigned value for audit, while recipeNum (legacy) tracks
                # the next expected number.
                if assigned_str is not None:
                    e['CheckNumber'] = assigned_str
                elif next_str is not None:
                    e['CheckNumber'] = next_str
                if next_str is not None:
                    e['recipeNum'] = next_str
                elif assigned_str is not None:
                    e['recipeNum'] = assigned_str
                logger.debug("_set_fields_on_entry set CheckNumber=%r recipeNum=%r", e.get('CheckNumber'), e.get('recipeNum'))
                updated = True

            if isinstance(cust_data, dict):
                # mapping or single-customer dict
                if self.selected_customer in cust_data and isinstance(cust_data[self.selected_customer], dict):
                    _set_fields_on_entry(cust_data[self.selected_customer])
                elif cust_data.get('customer') == self.selected_customer:
                    _set_fields_on_entry(cust_data)
            elif isinstance(cust_data, list):
                for item in cust_data:
                    if isinstance(item, dict) and item.get('customer') == self.selected_customer:
                        _set_fields_on_entry(item)
                        break

            if not updated:
                logger.debug("No matching customer entry found in %s to update", self.customer_file_path)
                return False

            # Persist changes to disk
            try:
                # Atomic write: write to a temp file in the same dir and rename it
                import tempfile
                d = os.path.dirname(self.customer_file_path) or '.'
                fd, tmp_path = tempfile.mkstemp(prefix='.tmp', dir=d, text=True)
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as tf:
                        json.dump(cust_data, tf, ensure_ascii=False, indent=2)
                        tf.flush()
                        try:
                            os.fsync(tf.fileno())
                        except Exception:
                            logger.debug("Could not fsync temp customer file %s", tmp_path)
                    # Move into place atomically
                    os.replace(tmp_path, self.customer_file_path)
                except Exception:
                    # Clean up temp file on failure
                    try:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    except Exception:
                        pass
                    raise
            except Exception:
                logger.exception("Failed to write updated customer file %s", self.customer_file_path)
                return False

            # Reflect the new values in-memory and refresh UI for the selected customer
            try:
                # Normalize into mapping and set self.data from the on-disk structure
                if isinstance(cust_data, dict):
                    if any(isinstance(v, dict) for v in cust_data.values()):
                        self.customers = cust_data
                    elif cust_data.get('customer'):
                        self.customers = {cust_data['customer']: cust_data}
                    else:
                        self.customers = {}
                elif isinstance(cust_data, list):
                    self.customers = {}
                    for item in cust_data:
                        if isinstance(item, dict) and 'customer' in item:
                            self.customers[item['customer']] = item

                if self.selected_customer and self.selected_customer in self.customers:
                    self.data = self.customers[self.selected_customer]
                    try:
                        self.populate_form()
                    except Exception:
                        logger.exception("Failed to refresh GUI after customer file update")
                        logger.debug("After populate_form: entries=%r; entry_texts=%r", list(self.entries.keys()), {k: v.text() for k, v in self.entries.items()})
                    # If we were told the next-increment value, prefer showing
                    # the next value (new_num) in the form so the user sees the
                    # number that will be used for the next receipt.
                    try:
                        if 'new_num' in locals() and new_num is not None:
                            logger.debug("Setting GUI next number to %r, entries=%r", new_num, list(self.entries.keys()))
                            key = 'CheckNumber' if 'CheckNumber' in self.entries else 'recipeNum'
                            try:
                                # Update the preferred entry and also keep
                                # the legacy 'recipeNum' field in sync if
                                # present so the UI consistently shows the
                                # next number regardless of which field the
                                # customer file exposes.
                                self.entries[key].setText(f"{int(new_num):05d}")
                                if 'recipeNum' in self.entries and key != 'recipeNum':
                                    try:
                                        self.entries['recipeNum'].setText(f"{int(new_num):05d}")
                                    except Exception:
                                        logger.exception("Failed to set legacy recipeNum in GUI")
                            except Exception:
                                logger.exception("Failed to set next recipeNum in GUI")
                    except Exception:
                        logger.exception("Failed to set next recipeNum in GUI after update")
                    # Update save_path display if present
                    try:
                        sp = self.data.get('SaveFolder')
                        if sp:
                            self.save_path = os.path.normpath(sp)
                            try:
                                self.save_path_display.setText(self.save_path)
                            except Exception:
                                pass
                            self.open_folder_btn.setEnabled(True)
                    except Exception:
                        logger.exception("Failed to set save_path after GUI refresh")
            except Exception:
                logger.exception("Failed to reload customer data into UI after write")

            return True
        except Exception:
            logger.exception("Unexpected error while updating customer data")
            return False

    def _notify_nonmodal(self, title: str, message: str, timeout_ms: int = 3000):
        """Show a brief non-modal notification to the user.

        The notification is a non-blocking QMessageBox that will be closed
        automatically after `timeout_ms` milliseconds. Designed to be resilient
        in headless/test environments (exceptions are caught and logged).
        """
        logger = logging.getLogger(__name__)
        try:
            # In headless/offscreen test environments creating and showing
            # actual QMessageBox widgets can crash the Qt runtime (access
            # violations). If running with the offscreen platform, avoid
            # creating GUI widgets and fall back to logging so tests and
            # headless runs are safe.
            if os.environ.get('QT_QPA_PLATFORM', '').lower() == 'offscreen':
                logger.warning("%s: %s", title, message)
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
                    # Last resort: log the message so tests can inspect logs
                    logger.warning("%s: %s", title, message)
        except Exception:
            logger.exception("Failed to show non-modal notification")


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
