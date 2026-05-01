#!/usr/bin/env python3
"""Qt GUI-based history file editor"""

import sys
import json
import unicodedata
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QFileDialog, QSplitter, QGroupBox, QComboBox, QLineEdit,
                             QSizePolicy)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR.parent))

from config.paths import DB_DIR, get_mode_label, USE_SIMULATION

HISTORY_DIR = Path(DB_DIR) / "History"

def _is_rtl_first_char(text: str) -> bool:
    """Return True if the first non-space char in text is strongly RTL.

    This helps align entries so Hebrew text is right-aligned and Latin is left-aligned.
    """
    if not text:
        return False
    s = text.strip()
    if not s:
        return False
    ch = s[0]
    bidi = unicodedata.bidirectional(ch)
    # 'R' = Right-to-Left, 'AL' = Arabic Letter, 'AN' = Arabic Number
    return bidi in ('R', 'AL', 'AN')

class HistoryEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.current_data = None
        self.original_data = None  # Store original data for change detection
        self.is_populating_fields = False  # Flag to prevent recursive calls
        
        # Setup Hebrew-capable font
        available_fonts = ["Alef", "Segoe UI", "Tahoma"]
        self.hebrew_font = QFont()
        for font_name in available_fonts:
            self.hebrew_font.setFamily(font_name)
            if self.hebrew_font.exactMatch():
                break
        self.hebrew_font.setPointSize(10)
        
        # Load customer data for dropdown
        self.customers = self._load_customers()
        
        self.init_ui()
        
    def _load_customers(self) -> list:
        """Load customer names from customers_data.json"""
        try:
            customers_file = Path(DB_DIR) / "customers_data.json"
            if customers_file.exists():
                with open(customers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Return sorted list of customer keys (e.g., "Gazoz", "Natan")
                return sorted(data.keys())
        except Exception as e:
            print(f"DEBUG: Error loading customers: {e}")
        return []
        
    def init_ui(self):
        self.setWindowTitle(f"History File Editor [{get_mode_label()}]")
        self.setGeometry(100, 100, 1200, 800)
        self.is_maximized = False
        self.normal_geometry = None
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # File selection section
        file_group = QGroupBox("File Selection")
        file_layout = QVBoxLayout(file_group)
        
        self.file_combo = QComboBox()
        self.file_combo.currentTextChanged.connect(self.on_file_changed)
        file_layout.addWidget(QLabel("Select File:"))
        file_layout.addWidget(self.file_combo)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        # Previous button
        self.prev_btn = QPushButton("◄ Previous")
        self.prev_btn.clicked.connect(self.go_to_previous)
        nav_layout.addWidget(self.prev_btn)
        
        # Current position display
        self.position_label = QLabel("0 / 0")
        self.position_label.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(self.position_label)
        
        # Next button
        self.next_btn = QPushButton("Next ►")
        self.next_btn.clicked.connect(self.go_to_next)
        nav_layout.addWidget(self.next_btn)
        
        file_layout.addLayout(nav_layout)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.refresh_files)
        control_layout.addWidget(refresh_btn)
        
        # Receipt number search
        control_layout.addSpacing(20)
        search_label = QLabel("Search Receipt #:")
        control_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setMaximumWidth(100)
        self.search_input.setPlaceholderText("e.g. 01730")
        self.search_input.returnPressed.connect(self.search_receipt)
        control_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.search_receipt)
        control_layout.addWidget(search_btn)
        
        file_layout.addLayout(control_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # Splitter for editor and preview
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Editor section
        editor_group = QGroupBox("JSON Editor")
        editor_group.setFont(self.hebrew_font)
        editor_layout = QVBoxLayout(editor_group)
        
        self.editor = QTextEdit()
        self.editor.setFont(self.hebrew_font)
        self.editor.setAlignment(Qt.AlignRight)
        self.editor.setAcceptRichText(True)
        

        editor_layout.addWidget(self.editor)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_file)
        button_layout.addWidget(save_btn)
        
        create_pdf_btn = QPushButton("Create PDF")
        create_pdf_btn.clicked.connect(self.create_pdf)
        button_layout.addWidget(create_pdf_btn)
        
        format_btn = QPushButton("Format JSON")
        format_btn.clicked.connect(self.format_json)
        button_layout.addWidget(format_btn)
        
        editor_layout.addLayout(button_layout)
        editor_group.setLayout(editor_layout)
        
        # Preview section
        preview_group = QGroupBox("Field Editor")
        preview_layout = QVBoxLayout(preview_group)
        
        self.field_widget = QWidget()
        self.field_layout = QVBoxLayout(self.field_widget)
        self.field_entries = {}  # Store QLineEdit widgets
        
        # Add scroll area for better handling of many fields
        from PyQt5.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.field_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview_layout.addWidget(scroll_area)
        
        # Make the preview group expand to fill available space
        preview_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        preview_group.setLayout(preview_layout)
        
        # Add to splitter with better proportions
        splitter.addWidget(editor_group)
        splitter.addWidget(preview_group)
        splitter.setSizes([400, 600])  # More space for field editor
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Add splitter to main layout with expansion
        main_layout.addWidget(splitter, 1)  # The '1' makes it expand
        
        # Status bar
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
    def refresh_files(self):
        """Refresh the file list"""
        print("DEBUG: Starting refresh_files")
        print("DEBUG: About to clear combo box")
        try:
            print("DEBUG: Clearing combo box now...")
            self.file_combo.clear()
            print("DEBUG: Combo box cleared successfully")
        except Exception as clear_error:
            print(f"DEBUG: Error clearing combo box: {clear_error}")
            print("DEBUG: Returning due to clear error")
            return
        
        try:
            print(f"DEBUG: Checking directory: {HISTORY_DIR}")
            if not HISTORY_DIR.exists():
                print(f"DEBUG: Directory does not exist")
                print("DEBUG: About to call QMessageBox.warning()")
                QMessageBox.warning(self, "Error", f"History directory not found:\n{HISTORY_DIR}")
                return
            
            print("DEBUG: Directory exists, globbing for *.json files")
            print("DEBUG: About to call HISTORY_DIR.glob()")
            files = sorted(HISTORY_DIR.glob("*.json"))
            print(f"DEBUG: Found {len(files)} files")
            
            print("DEBUG: About to start file loop")
            for i, file_path in enumerate(files):
                print(f"DEBUG: Adding file {i}: {file_path.stem}")
                try:
                    print("DEBUG: About to call self.file_combo.addItem()")
                    # Temporarily block signals to prevent popups
                    self.file_combo.blockSignals(True)
                    self.file_combo.addItem(file_path.stem)
                    self.file_combo.blockSignals(False)
                    print("DEBUG: File added successfully")
                except Exception as add_error:
                    print(f"DEBUG: Error adding file {i} to combo: {add_error}")
                    print(f"DEBUG: File path: {file_path}")
                    print(f"DEBUG: File exists: {file_path.exists()}")
                    continue
                except:
                    print(f"DEBUG: Unknown error adding file {i}")
                    continue
            
            try:
                self.status_label.setText(f"Found {len(files)} files")
                self.update_navigation_buttons()
                print("DEBUG: Refresh completed successfully")
            except Exception as status_error:
                print(f"DEBUG: Error updating status/navigation: {status_error}")
            
        except Exception as e:
            # Prevent popup by handling errors gracefully
            error_msg = f"Error refreshing files: {e}"
            self.status_label.setText(error_msg)
            print(f"DEBUG: {error_msg}")
            print(f"DEBUG: Exception type: {type(e).__name__}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            
            # Try to recover by reloading current selection if available
            try:
                if self.file_combo.count() > 0:
                    print(f"DEBUG: Recovering with {self.file_combo.count()} files in combo")
            except:
                print("DEBUG: Recovery failed")
    
    def go_to_previous(self):
        """Navigate to previous receipt"""
        print("DEBUG: go_to_previous called")
        try:
            current_index = self.file_combo.currentIndex()
            print(f"DEBUG: Current index: {current_index}")
            if current_index > 0:
                print(f"DEBUG: Setting index to {current_index - 1}")
                self.file_combo.setCurrentIndex(current_index - 1)
                print("DEBUG: Previous navigation successful")
            else:
                print("DEBUG: Already at first file, cannot go previous")
        except Exception as e:
            print(f"DEBUG: Error in go_to_previous: {e}")
    
    def go_to_next(self):
        """Navigate to next receipt"""
        print("DEBUG: go_to_next called")
        try:
            current_index = self.file_combo.currentIndex()
            print(f"DEBUG: Current index: {current_index}")
            max_index = self.file_combo.count() - 1
            print(f"DEBUG: Max index: {max_index}")
            if current_index < max_index:
                print(f"DEBUG: Setting index to {current_index + 1}")
                self.file_combo.setCurrentIndex(current_index + 1)
                print("DEBUG: Next navigation successful")
            else:
                print("DEBUG: Already at last file, cannot go next")
        except Exception as e:
            print(f"DEBUG: Error in go_to_next: {e}")
    
    def update_navigation_buttons(self):
        """Update navigation button states and position display"""
        current_index = self.file_combo.currentIndex()
        total_count = self.file_combo.count()
        
        # Update position display
        if current_index >= 0 and total_count > 0:
            self.position_label.setText(f"{current_index + 1} / {total_count}")
        else:
            self.position_label.setText("0 / 0")
        
        # Update button states
        self.prev_btn.setEnabled(current_index > 0)
        self.next_btn.setEnabled(current_index < total_count - 1)
    
    def search_receipt(self):
        """Search for a receipt by receipt number (numeric comparison to handle leading zeros)"""
        search_text = self.search_input.text().strip()
        if not search_text:
            self.status_label.setText("Please enter a receipt number to search")
            return
        
        try:
            # Convert search term to integer for numeric comparison
            search_num = int(search_text)
        except ValueError:
            self.status_label.setText(f"Invalid receipt number: {search_text}")
            return
        
        print(f"DEBUG: Searching for receipt number: {search_num}")
        
        # Search through all files in the combo box
        found_index = -1
        for i in range(self.file_combo.count()):
            filename = self.file_combo.itemText(i)
            
            # Try to extract receipt number from filename or load the file
            try:
                file_path = HISTORY_DIR / f"{filename}.json"
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Get receipt number from data section
                    if 'data' in data and isinstance(data['data'], dict):
                        recipe_num_str = data['data'].get('recipeNum', '')
                    else:
                        recipe_num_str = data.get('recipeNum', '')
                    
                    # Convert to integer for comparison (handles leading zeros)
                    if recipe_num_str:
                        try:
                            file_recipe_num = int(recipe_num_str)
                            if file_recipe_num == search_num:
                                found_index = i
                                print(f"DEBUG: Found receipt {search_num} at index {i} (filename: {filename})")
                                break
                        except ValueError:
                            # Skip files with non-numeric recipe numbers
                            continue
            except Exception as e:
                print(f"DEBUG: Error checking file {filename}: {e}")
                continue
        
        if found_index >= 0:
            # Select the found receipt
            self.file_combo.setCurrentIndex(found_index)
            self.status_label.setText(f"Found receipt #{search_num}")
            print(f"DEBUG: Navigated to receipt at index {found_index}")
        else:
            self.status_label.setText(f"Receipt #{search_num} not found")
            print(f"DEBUG: Receipt {search_num} not found in any file")
            # Show popup to user
            QMessageBox.information(self, "Receipt Not Found", 
                                    f"Receipt #{search_num} was not found in any file.")
    
    def toggle_maximize(self):
        """Toggle between normal and maximized window state"""
        if self.is_maximized:
            # Restore to normal size
            if self.normal_geometry:
                self.setGeometry(self.normal_geometry)
            else:
                self.setGeometry(100, 100, 1200, 800)
            self.maximize_btn.setText("⛶ Maximize")
            self.is_maximized = False
        else:
            # Maximize the window
            self.normal_geometry = self.geometry()
            screen = QApplication.desktop().screenGeometry()
            self.setGeometry(
                screen.x() + 10,
                screen.y() + 10,
                screen.width() - 20,
                screen.height() - 20
            )
            self.maximize_btn.setText("⛷ Restore")
            self.is_maximized = True
        
    def on_file_changed(self, filename):
        """Handle file selection change"""
        print(f"DEBUG: on_file_changed called with filename: {filename}")
        try:
            if not filename:
                print("DEBUG: No filename selected")
                self.current_file = None
                self.current_data = None
                self.editor.clear()
                # Clear field widgets instead of old table
                self.update_field_table()
                self.status_label.setText("No file selected")
                self.update_navigation_buttons()
                return
            
            print(f"DEBUG: Loading file: {filename}")
            self.current_file = filename
            self.load_file(filename)
            self.update_navigation_buttons()
            print("DEBUG: File change completed successfully")
        except Exception as e:
            print(f"DEBUG: Error in on_file_changed: {e}")
            print(f"DEBUG: Exception type: {type(e).__name__}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
        
    def load_file(self, filename):
        """Load selected JSON file"""
        file_path = HISTORY_DIR / f"{filename}.json"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Store original data for change detection
            self.original_data = json.loads(json.dumps(data))  # Deep copy
            self.current_data = data
            self.update_editor()
            
            # Add error handling for field table update
            try:
                self.update_field_table()
                self.status_label.setText(f"Loaded: {filename}")
            except Exception as field_error:
                QMessageBox.critical(self, "Field Error", f"Error updating field table:\n{field_error}")
                # Clear field widgets on error
                self.update_field_table()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load {filename}:\n{e}")
            self.current_file = None
            self.current_data = None
            self.original_data = None
            self.update_field_table()  # Clear field widgets
    
    def update_edit_timestamp(self):
        """Update the edit timestamp in the info section"""
        if not self.current_data:
            return
        
        # Ensure info section exists
        if 'info' not in self.current_data:
            self.current_data['info'] = {}
        
        # Add edit timestamp
        from datetime import datetime
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.current_data['info']['last_edit_date'] = current_time
        self.current_data['info']['last_edit_file'] = self.current_file
        self.current_data['info']['edited_by'] = 'HistoryEditor'
        
        # Debug: Print what was added
        print(f"DEBUG: Added edit tracking to info section:")
        print(f"  last_edit_date: {current_time}")
        print(f"  last_edit_file: {self.current_file}")
        print(f"  edited_by: HistoryEditor")
        print(f"  Info section now has {len(self.current_data['info'])} fields")
        
        # Update the JSON editor to show changes (but don't rebuild field table)
        self.update_editor()
        self.status_label.setText(f"Edit timestamp updated: {current_time}")
            
    def update_field_table(self):
        """Update the field editor with QLineEdit widgets"""
        try:
            print("DEBUG: Starting update_field_table")
            # Set flag to prevent recursive calls during population
            self.is_populating_fields = True
            
            # Clear existing widgets safely
            while self.field_layout.count():
                item = self.field_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    print(f"DEBUG: Removing widget: {widget}")
                    widget.setParent(None)
                    widget.deleteLater()
            self.field_entries.clear()
            
            # Also clear any remaining child widgets
            for i in reversed(range(len(self.field_widget.children()))):
                child = self.field_widget.children()[i]
                if isinstance(child, QWidget):
                    child.setParent(None)
                    child.deleteLater()
        
            if not self.current_data:
                print("DEBUG: No current_data, returning")
                return
        
            # Handle both data/info structure and flat structure
            if 'data' in self.current_data and isinstance(self.current_data['data'], dict):
                data_section = self.current_data['data']
                info_section = self.current_data.get('info', {})
                
                # Add data fields with section tracking
                for key, value in data_section.items():
                    self._create_field_widget(key, str(value), 'data')
            
                # Add info fields with section tracking
                for key, value in info_section.items():
                    self._create_field_widget(key, str(value), 'info')
                
            else:
                # Flat structure - treat all fields as data
                for key, value in self.current_data.items():
                    self._create_field_widget(key, str(value))
                
            # Reset flag after successful population
            self.is_populating_fields = False
            print("DEBUG: Field population completed, flag reset")
                
        except Exception as e:
            # Re-raise with more context
            raise Exception(f"Error in update_field_table: {e}")
    
    def _create_field_widget(self, key: str, value: str, section: str = 'data'):
        """Create a field widget with proper Hebrew support"""
        print(f"DEBUG: Creating field widget for {key} (section: {section}) with value: {value}")
        h_layout = QHBoxLayout()
        
        # Field label
        label = QLabel(f"{key}:")
        label.setMinimumWidth(120)
        label.setFont(self.hebrew_font)
        
        # Special handling for customer_name - use dropdown
        if key == 'customer_name' and self.customers:
            entry = QComboBox()
            entry.setEditable(False)  # Prevent typing - only selection allowed
            entry.addItems(self.customers)
            # Set current value if it exists in the list
            if value in self.customers:
                entry.setCurrentText(value)
            else:
                # If value not in list, add it temporarily and select it
                entry.addItem(value)
                entry.setCurrentText(value)
            entry.setFont(self.hebrew_font)
            print(f"DEBUG: Created QComboBox for customer_name with {len(self.customers)} customers")
            
            # Store section info in the widget for later use
            entry.setProperty('field_section', section)
            
            # Connect currentTextChanged signal
            entry.currentTextChanged.connect(lambda text, k=key, e=entry: self.on_field_finished(k, e))
            print(f"DEBUG: Connected currentTextChanged signal for customer_name")
        else:
            # Regular QLineEdit for other fields
            entry = QLineEdit()
            print(f"DEBUG: Created QLineEdit widget: {entry}")
            # Display value as-is (Hebrew text is now stored correctly)
            display_value = value
            entry.setText(display_value)
            entry.setFont(self.hebrew_font)
            
            # Store section info in the widget for later use
            entry.setProperty('field_section', section)
            
            # Align right only if first non-space char is RTL (Hebrew/Arabic)
            if _is_rtl_first_char(display_value):
                entry.setAlignment(Qt.AlignRight)
            else:
                entry.setAlignment(Qt.AlignLeft)
            
            print(f"DEBUG: About to connect editingFinished signal for field: {key}")
            # Connect editingFinished signal - only triggers when user finishes editing
            entry.editingFinished.connect(lambda k=key, e=entry: self.on_field_finished(k, e))
            print(f"DEBUG: Connected editingFinished signal for field: {key}")
        
        h_layout.addWidget(label)
        h_layout.addWidget(entry)
        self.field_layout.addLayout(h_layout)
        self.field_entries[key] = entry
                
    def format_json(self):
        """Format the JSON in the editor"""
        try:
            text = self.editor.toPlainText()
            data = json.loads(text)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            self.editor.setPlainText(formatted)
            self.status_label.setText("JSON formatted")
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "Format Error", f"Invalid JSON:\n{e}")

    def on_field_finished(self, field_name: str, entry_widget):
        """Handle field editing finished (user pressed Tab/Enter or clicked away)"""
        # Get the current text from the widget (handles both QLineEdit and QComboBox)
        from PyQt5.QtWidgets import QComboBox
        if isinstance(entry_widget, QComboBox):
            display_value = entry_widget.currentText()
        else:
            display_value = entry_widget.text()
        
        print(f"DEBUG: on_field_finished called for {field_name} with value: {display_value}")
        print(f"DEBUG: is_populating_fields flag: {getattr(self, 'is_populating_fields', False)}")
        
        # Skip processing if currently populating fields to prevent recursive calls
        if getattr(self, 'is_populating_fields', False):
            print("DEBUG: Skipping on_field_finished due to population flag")
            return
            
        try:
            if not self.current_data:
                return
                
            # Store value as-is (Hebrew text is now stored correctly)
            storage_value = display_value
            
            # Get section from widget property
            section = entry_widget.property('field_section') or 'data'
            print(f"DEBUG: Updating field {field_name} in section: {section}")
                
            # Update the correct section
            if section == 'info':
                if 'info' not in self.current_data:
                    self.current_data['info'] = {}
                self.current_data['info'][field_name] = storage_value
            else:
                # data section (default)
                if 'data' in self.current_data and isinstance(self.current_data['data'], dict):
                    self.current_data['data'][field_name] = storage_value
                else:
                    # Flat structure - update directly
                    self.current_data[field_name] = storage_value
            
            # Mark data as modified (for save detection)
            self.status_label.setText(f"Modified: {field_name} = {display_value} (unsaved)")
            print(f"DEBUG: Field {field_name} updated, waiting for save")
        except Exception as e:
            print(f"DEBUG: Error in on_field_finished: {e}")
            print(f"DEBUG: Exception type: {type(e).__name__}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
                
    def update_editor(self):
        """Update the JSON editor with current data"""
        if self.current_data:
            json_text = json.dumps(self.current_data, indent=2, ensure_ascii=False)
            self.editor.setPlainText(json_text)
                
    def format_json(self):
        """Format the JSON in the editor"""
        try:
            text = self.editor.toPlainText()
            data = json.loads(text)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            self.editor.setPlainText(formatted)
            self.status_label.setText("JSON formatted")
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "Format Error", f"Invalid JSON:\n{e}")

    def save_file(self):
        """Save the current file"""
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "No file selected")
            return
            
        try:
            # Add edit timestamp before saving
            self.update_edit_timestamp()
            
            # Use the current_data directly instead of parsing from editor
            data = self.current_data
            
            file_path = HISTORY_DIR / f"{self.current_file}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Update the JSON editor with saved data
            self.update_editor()
            # Refresh field table to show any new info fields (like edit timestamp)
            self.update_field_table()
            
            self.status_label.setText(f"Saved: {self.current_file}")
            QMessageBox.information(self, "Success", f"File {self.current_file} saved successfully!")
            
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Save Error", f"Invalid JSON:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save {self.current_file}:\n{e}")

    def create_pdf(self):
        """Create PDF from current receipt data without creating history entry"""
        if not self.current_data:
            QMessageBox.warning(self, "Warning", "No receipt data loaded")
            return
        
        try:
            # Import receipt generation logic
            from logic.receiptGen import create_receipt
            from config.paths import recreat_receipt_folder
            
            # Get receipt data from current_data
            if 'data' in self.current_data and isinstance(self.current_data['data'], dict):
                receipt_data = self.current_data['data']
            else:
                receipt_data = self.current_data
            
            # Generate PDF filename
            recipe_num = receipt_data.get('recipeNum', 'unknown')
            customer = receipt_data.get('customer', 'unknown')
            date = receipt_data.get('Date', '').replace('/', '-')
            pdf_filename = f"Receipt_{recipe_num}_{customer}_{date}.pdf"
            
            # Ensure output directory exists
            output_dir = Path(recreat_receipt_folder)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            pdf_path = output_dir / pdf_filename
            
            # Create the PDF
            create_receipt(receipt_data, str(pdf_path))
            
            self.status_label.setText(f"PDF created: {pdf_filename}")
            QMessageBox.information(self, "Success", 
                                    f"PDF created successfully!\n\nSaved to:\n{pdf_path}")
            print(f"DEBUG: PDF created at {pdf_path}")
            
        except ImportError as e:
            QMessageBox.critical(self, "Error", 
                                f"Failed to import PDF generation module:\n{e}\n\n"
                                f"Make sure receiptGen.py exists in the logic folder.")
        except Exception as e:
            QMessageBox.critical(self, "PDF Error", f"Failed to create PDF:\n{e}")
            print(f"DEBUG: PDF creation error: {e}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")

def main():
    app = QApplication(sys.argv)
    editor = HistoryEditor()
    editor.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
